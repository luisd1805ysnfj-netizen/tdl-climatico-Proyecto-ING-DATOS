"""Captura diaria programada de Open-Meteo (la corre GitHub Actions: captura.yml).

Descarga los últimos días de los 3 municipios, valida la FORMA de la respuesta antes
de guardarla en bronce y deja una bitácora de cada intento (insumo de fiabilidad:
MTBF, MTTR y disponibilidad). Una respuesta inválida NO se guarda.

Uso:  python -m extractors.captura_diaria
Código de salida: 0 si los 3 municipios se capturaron, 1 si alguno falló.
"""
import csv
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from extractors.clima_extractor import MUNICIPIOS, USER_AGENT

URL_ARCHIVO = "https://archive-api.open-meteo.com/v1/archive"
VARIABLES_DIARIAS = ["temperature_2m_max", "temperature_2m_min",
                     "precipitation_sum", "wind_speed_10m_max"]
UNIDADES_ESPERADAS = {"temperature_2m_max": "°C", "temperature_2m_min": "°C",
                      "precipitation_sum": "mm", "wind_speed_10m_max": "km/h"}
DIAS_POR_CAPTURA = 7          # se traslapan a propósito: si un día falla, el siguiente lo cubre
REZAGO_ARCHIVO_DIAS = 2       # el archivo de Open-Meteo se publica con ~2 días de retraso
TIMEOUT_S = 20
PAUSA_ENTRE_PETICIONES_S = 1.0   # regla del proyecto: mínimo 1 s entre peticiones
CAMPOS_BITACORA = ["timestamp_utc", "municipio", "exito", "http_status", "filas",
                   "intentos", "duracion_s", "error"]


def crear_sesion():
    sesion = requests.Session()
    sesion.headers["User-Agent"] = USER_AGENT   # extractor identificado honestamente
    return sesion


def construir_parametros(coords, inicio, fin):
    return {
        "latitude": coords["lat"], "longitude": coords["lon"],
        "start_date": inicio.isoformat(), "end_date": fin.isoformat(),
        "daily": ",".join(VARIABLES_DIARIAS), "timezone": "auto",
    }


def validar_respuesta(datos):
    """Devuelve la lista de problemas de FORMA de la respuesta (vacía = válida)."""
    if not isinstance(datos, dict):
        return ["la respuesta no es un objeto JSON"]
    problemas = []
    diario = datos.get("daily")
    if not isinstance(diario, dict):
        return ["falta el bloque 'daily'"]
    tiempos = diario.get("time")
    if not tiempos:
        problemas.append("'daily.time' vacío o ausente")
    unidades = datos.get("daily_units", {})
    for var in VARIABLES_DIARIAS:
        if var not in diario:
            problemas.append(f"falta la variable '{var}'")
            continue
        if tiempos and len(diario[var]) != len(tiempos):
            problemas.append(f"'{var}' tiene {len(diario[var])} valores y 'time' {len(tiempos)}")
        if unidades.get(var) != UNIDADES_ESPERADAS[var]:
            problemas.append(f"unidad inesperada en '{var}': {unidades.get(var)!r}")
    return problemas


def descargar_municipio(nombre, coords, inicio, fin, sesion, intentos=3,
                        pausa_reintento=2.0, dormir=time.sleep):
    """Una petición con reintentos (429, 5xx, timeouts). Nunca lanza por fallas esperadas."""
    inicio_t = time.monotonic()
    res = {"municipio": nombre, "ok": False, "http_status": None, "filas": 0,
           "intentos": 0, "error": "", "datos": None}
    for i in range(intentos):
        res["intentos"] = i + 1
        try:
            r = sesion.get(URL_ARCHIVO, params=construir_parametros(coords, inicio, fin),
                           timeout=TIMEOUT_S)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            res["error"] = f"{type(exc).__name__}: {exc}"
            if i < intentos - 1:
                dormir(pausa_reintento * 2 ** i)
            continue
        res["http_status"] = r.status_code
        if r.status_code == 429 or r.status_code >= 500:   # saturación: esperar y reintentar
            res["error"] = f"HTTP {r.status_code}"
            if i < intentos - 1:
                dormir(pausa_reintento * 2 ** i)
            continue
        if r.status_code != 200:                            # 4xx: reintentar no sirve
            res["error"] = f"HTTP {r.status_code}"
            break
        try:
            datos = r.json()
        except ValueError:
            res["error"] = "la respuesta no es JSON válido"
            break
        problemas = validar_respuesta(datos)
        if problemas:
            res["error"] = "respuesta inválida: " + "; ".join(problemas)
            break
        res.update(ok=True, error="", datos=datos, filas=len(datos["daily"]["time"]))
        break
    res["duracion_s"] = round(time.monotonic() - inicio_t, 2)
    return res


def registrar_bitacora(ruta, resultados, ahora=None):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ahora = ahora or datetime.now(timezone.utc)
    nuevo = not ruta.exists()
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_BITACORA)
        if nuevo:
            w.writeheader()
        for r in resultados:
            w.writerow({"timestamp_utc": ahora.isoformat(timespec="seconds"),
                        "municipio": r["municipio"], "exito": r["ok"],
                        "http_status": r["http_status"] or "", "filas": r["filas"],
                        "intentos": r["intentos"], "duracion_s": r.get("duracion_s", ""),
                        "error": r["error"]})


def _guardar_json(datos, destino):
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(destino)   # escritura atómica: nunca queda un JSON a medias


def capturar_todo(hoy=None, dir_bronce="data/bronce", ruta_bitacora="calidad/bitacora_captura.csv",
                  sesion=None, pausa=PAUSA_ENTRE_PETICIONES_S, dormir=time.sleep,
                  dias=DIAS_POR_CAPTURA):
    hoy = hoy or date.today()
    fin = hoy - timedelta(days=REZAGO_ARCHIVO_DIAS)
    inicio = fin - timedelta(days=dias - 1)
    dir_bronce = Path(dir_bronce)
    dir_bronce.mkdir(parents=True, exist_ok=True)
    sesion = sesion or crear_sesion()
    resultados = []
    for k, (nombre, coords) in enumerate(MUNICIPIOS.items()):
        if k:
            dormir(pausa)
        r = descargar_municipio(nombre, coords, inicio, fin, sesion, dormir=dormir)
        if r["ok"]:
            _guardar_json(r["datos"], dir_bronce / f"clima_historico_{nombre}_{hoy:%Y%m%d}.json")
        resultados.append(r)
        print(f"[{'OK' if r['ok'] else 'ERROR'}] {nombre}: filas={r['filas']} "
              f"intentos={r['intentos']} {r['error']}")
    registrar_bitacora(ruta_bitacora, resultados)
    return resultados


def main():
    resultados = capturar_todo()
    return 0 if all(r["ok"] for r in resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
