"""Captura de uso de suelo agrícola de OpenStreetMap (Overpass API) para los 3 municipios.

Fuente ESPECIALIZADA GEOESPACIAL de E2. Se consulta alrededor de las coordenadas REALES de la
malla de clima (lat_grid/lon_grid que guardó Open-Meteo en bronce), así ambas fuentes hablan
del mismo punto.

Ética de la captura (ver docs/etica-datos.md):
- Servicio público y gratuito: pocas consultas (3), identificadas con User-Agent propio,
  pausa entre ellas y reintentos con espera. Captura manual o mensual, nunca por hora.
- Cero datos personales: solo se guardan etiquetas de una LISTA BLANCA; se descartan nombres,
  dueños, teléfonos, correos y direcciones ANTES de escribir nada en bronce.
- Datos © OpenStreetMap contributors, licencia ODbL: se conserva la atribución en el archivo.

Uso:  python -m extractors.osm_overpass
"""
import json
import re
import time
from datetime import UTC, date, datetime
from pathlib import Path

import requests

from extractors.captura_diaria import crear_sesion, registrar_bitacora
from extractors.clima_extractor import MUNICIPIOS
from pipeline import config as cfg

PAUSA_ENTRE_CONSULTAS_S = 5.0
TIMEOUT_S = 120
TIPOS_REINTENTABLES = {429, 502, 503, 504}
PATRON_CLIMA = re.compile(r"clima_historico_(?P<mun>[a-z_]+)_(?P<fecha>\d{8})\.json$")


class ErrorOverpass(RuntimeError):
    """La respuesta de Overpass no se pudo obtener o no tiene la forma esperada."""


def construir_consulta(lat, lon, radio_m=cfg.OSM_RADIO_M, usos=None):
    usos = usos or cfg.OSM_USOS_AGRICOLAS
    patron = "|".join(usos)
    return (f'[out:json][timeout:90];\n'
            f'(way["landuse"~"^({patron})$"](around:{radio_m},{lat},{lon}););\n'
            f'out geom;')


def _fecha_archivo(ruta):
    m = PATRON_CLIMA.search(ruta.name)
    return m.group("fecha") if m else ""


def centro_desde_bronce(nombre, dir_bronce="data/bronce"):
    """Coordenadas reales de la malla de Open-Meteo (la captura de clima más reciente)."""
    archivos = sorted(Path(dir_bronce).glob(f"clima_historico_{nombre}_*.json"), key=_fecha_archivo)
    if archivos:
        datos = json.loads(archivos[-1].read_text(encoding="utf-8"))
        if "latitude" in datos and "longitude" in datos:
            return float(datos["latitude"]), float(datos["longitude"]), archivos[-1].name
    c = MUNICIPIOS[nombre]  # respaldo: las coordenadas pedidas
    return c["lat"], c["lon"], "coordenadas_solicitadas"


def sanear_elementos(elementos):
    """Lista blanca de etiquetas. Devuelve (elementos_limpios, resumen_de_saneamiento).

    El resumen cuenta cuántas etiquetas y de qué CLAVE se descartaron (nunca sus valores,
    porque un valor puede ser el nombre de una persona).
    """
    permitidas = set(cfg.OSM_ETIQUETAS_PERMITIDAS)
    limpios, descartadas = [], {}
    for el in elementos:
        etiquetas = el.get("tags", {})
        for clave in etiquetas:
            if clave not in permitidas:
                descartadas[clave] = descartadas.get(clave, 0) + 1
        limpios.append({"type": el.get("type"), "id": el.get("id"),
                        "tags": {k: v for k, v in etiquetas.items() if k in permitidas},
                        "geometry": el.get("geometry", [])})
    return limpios, {"etiquetas_descartadas_por_clave": dict(sorted(descartadas.items())),
                     "total_etiquetas_descartadas": sum(descartadas.values())}


def validar_respuesta(datos):
    """Problemas de FORMA de la respuesta de Overpass (lista vacía = válida)."""
    if not isinstance(datos, dict):
        return ["la respuesta no es un objeto JSON"]
    if "elements" not in datos or not isinstance(datos["elements"], list):
        return ["falta la lista 'elements'"]
    problemas = []
    for el in datos["elements"]:
        if el.get("type") != "way" or "id" not in el:
            problemas.append(f"elemento inesperado: {str(el)[:60]}")
            break
    return problemas


def consultar(consulta, sesion, endpoints=None, intentos=3, pausa_reintento=5.0, dormir=time.sleep):
    """POST a Overpass con reintentos y espejo de respaldo. Devuelve (json, endpoint, intentos)."""
    endpoints = endpoints or cfg.OSM_ENDPOINTS
    total, ultimo_error = 0, ""
    for endpoint in endpoints:
        for i in range(intentos):
            total += 1
            try:
                r = sesion.post(endpoint, data={"data": consulta}, timeout=TIMEOUT_S)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                ultimo_error = f"{type(exc).__name__}: {exc}"
                if i < intentos - 1:
                    dormir(pausa_reintento * 2 ** i)
                continue
            if r.status_code in TIPOS_REINTENTABLES:
                ultimo_error = f"HTTP {r.status_code}"
                if i < intentos - 1:
                    dormir(pausa_reintento * 2 ** i)
                continue
            if r.status_code != 200:
                raise ErrorOverpass(f"HTTP {r.status_code} en {endpoint}")
            try:
                datos = r.json()
            except ValueError as exc:
                raise ErrorOverpass("la respuesta no es JSON válido") from exc
            return datos, endpoint, total
    raise ErrorOverpass(f"sin respuesta tras {total} intentos: {ultimo_error}")


def descargar_municipio(nombre, lat, lon, sesion, radio_m=cfg.OSM_RADIO_M, **kw):
    """Una consulta; nunca lanza por fallas esperadas. Devuelve el resultado y el documento de bronce."""
    inicio = time.monotonic()
    res = {"municipio": f"osm-{nombre}", "ok": False, "http_status": None, "filas": 0,
           "intentos": 0, "error": "", "documento": None}
    try:
        datos, endpoint, intentos = consultar(construir_consulta(lat, lon, radio_m), sesion, **kw)
    except ErrorOverpass as exc:
        res["error"] = str(exc)
        res["duracion_s"] = round(time.monotonic() - inicio, 2)
        return res
    res.update(http_status=200, intentos=intentos)
    problemas = validar_respuesta(datos)
    if problemas:
        res["error"] = "respuesta inválida: " + "; ".join(problemas)
    else:
        elementos, saneamiento = sanear_elementos(datos["elements"])
        osm3s = datos.get("osm3s", {})
        res.update(ok=True, filas=len(elementos), documento={
            "fuente": "openstreetmap-overpass", "municipio": nombre,
            "centro": {"lat": lat, "lon": lon}, "radio_m": radio_m, "endpoint": endpoint,
            "consulta": construir_consulta(lat, lon, radio_m),
            "capturado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "osm3s": {"timestamp_osm_base": osm3s.get("timestamp_osm_base"),
                      "copyright": osm3s.get("copyright",
                                             "© OpenStreetMap contributors. Open Database License (ODbL).")},
            "saneamiento": saneamiento, "elements": elementos})
    res["duracion_s"] = round(time.monotonic() - inicio, 2)
    return res


def _guardar_json(datos, destino):
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    tmp.replace(destino)


def capturar_todo(hoy=None, dir_bronce="data/bronce", ruta_bitacora="calidad/bitacora_osm.csv",
                  sesion=None, pausa=PAUSA_ENTRE_CONSULTAS_S, dormir=time.sleep, **kw):
    hoy = hoy or date.today()
    dir_bronce = Path(dir_bronce)
    dir_bronce.mkdir(parents=True, exist_ok=True)
    sesion = sesion or crear_sesion()
    resultados = []
    for k, nombre in enumerate(MUNICIPIOS):
        if k:
            dormir(pausa)
        lat, lon, origen_centro = centro_desde_bronce(nombre, dir_bronce)
        r = descargar_municipio(nombre, lat, lon, sesion, dormir=dormir, **kw)
        if r["ok"]:
            r["documento"]["centro"]["origen"] = origen_centro
            _guardar_json(r["documento"], dir_bronce / f"osm_agricola_{nombre}_{hoy:%Y%m%d}.json")
        resultados.append(r)
        print(f"[{'OK' if r['ok'] else 'ERROR'}] {nombre}: parcelas={r['filas']} "
              f"intentos={r['intentos']} {r['error']}")
    registrar_bitacora(ruta_bitacora, resultados)
    return resultados


def main():
    resultados = capturar_todo()
    return 0 if all(r["ok"] for r in resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
