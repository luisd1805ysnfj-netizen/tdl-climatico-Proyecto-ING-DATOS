"""Pruebas OFFLINE de la fuente geoespacial (OpenStreetMap / Overpass).

La respuesta de Overpass de estas pruebas es SINTÉTICA (misma estructura que la real, valores
inventados, con etiquetas personales a propósito para probar que se eliminan). Cuando capturen la
primera respuesta real, pueden guardar una versión recortada en tests/fixtures/ y usarla aquí.
"""
import json

import pandas as pd
import pytest
import requests

from extractors import osm_overpass as osm
from pipeline import config as cfg
from pipeline import geoespacial as geo
from tests.conftest import escribir_json_open_meteo

LAT, LON = 18.95, -103.88   # cerca de Tecomán


def rectangulo(lat0, lon0, dlat=0.009, dlon=0.0095):
    """Anillo cerrado de ~1 km x 1 km (≈ 100 ha) con la forma que devuelve `out geom`."""
    pts = [(lat0, lon0), (lat0, lon0 + dlon), (lat0 + dlat, lon0 + dlon), (lat0 + dlat, lon0), (lat0, lon0)]
    return [{"lat": la, "lon": lo} for la, lo in pts]


def respuesta_overpass(n=3, con_datos_personales=True):
    elementos = []
    for i in range(n):
        etiquetas = {"landuse": "orchard" if i % 2 == 0 else "farmland", "crop": "lime"}
        if con_datos_personales:
            etiquetas |= {"name": "Rancho de Juan Pérez", "operator": "Familia Pérez",
                          "phone": "+52 313 000 0000", "addr:street": "Calle Secreta 1"}
        elementos.append({"type": "way", "id": 1000 + i, "tags": etiquetas,
                          "geometry": rectangulo(LAT + i * 0.02, LON)})
    return {"version": 0.6, "generator": "Overpass API (sintético)",
            "osm3s": {"timestamp_osm_base": "2026-11-16T10:00:00Z",
                      "copyright": "The data included in this document is from www.openstreetmap.org (ODbL)."},
            "elements": elementos}


class Resp:
    def __init__(self, status=200, cuerpo=None, json_valido=True):
        self.status_code, self._c, self._v = status, cuerpo, json_valido

    def json(self):
        if not self._v:
            raise ValueError("no es JSON")
        return self._c


class SesionPost:
    def __init__(self, *respuestas):
        self.respuestas, self.llamadas = list(respuestas), []

    def post(self, url, data=None, timeout=None):
        self.llamadas.append({"url": url, "data": data, "timeout": timeout})
        r = self.respuestas.pop(0) if len(self.respuestas) > 1 else self.respuestas[0]
        if isinstance(r, Exception):
            raise r
        return r


def sin_espera(_segundos):
    return None


# -------------------------------------------------------------- consulta
def test_la_consulta_pide_uso_agricola_alrededor_del_punto():
    q = osm.construir_consulta(LAT, LON, 10_000)
    assert "around:10000,18.95,-103.88" in q and "out geom" in q
    assert all(u in q for u in cfg.OSM_USOS_AGRICOLAS)


def test_el_centro_sale_de_la_malla_real_de_open_meteo(tmp_path):
    escribir_json_open_meteo(tmp_path / "clima_historico_colima_20261109.json", lat=19.2267, lon=-103.7092)
    assert osm.centro_desde_bronce("colima", tmp_path) == (19.2267, -103.7092, "clima_historico_colima_20261109.json")
    assert osm.centro_desde_bronce("tecoman", tmp_path)[2] == "coordenadas_solicitadas"   # sin archivo: respaldo


# ------------------------------------------------------------ privacidad
def test_se_eliminan_los_datos_personales_antes_de_guardar():
    limpios, resumen = osm.sanear_elementos(respuesta_overpass()["elements"])
    for el in limpios:
        assert set(el["tags"]) <= set(cfg.OSM_ETIQUETAS_PERMITIDAS)
    assert resumen["total_etiquetas_descartadas"] == 3 * 4
    assert set(resumen["etiquetas_descartadas_por_clave"]) == {"name", "operator", "phone", "addr:street"}
    texto = json.dumps([limpios, resumen], ensure_ascii=False)
    assert "Juan" not in texto and "Pérez" not in texto and "000 0000" not in texto and "Secreta" not in texto


def test_el_documento_de_bronce_no_contiene_datos_personales():
    r = osm.descargar_municipio("tecoman", LAT, LON, SesionPost(Resp(200, respuesta_overpass())), dormir=sin_espera)
    texto = json.dumps(r["documento"], ensure_ascii=False)
    assert r["ok"] and "Juan" not in texto and "Pérez" not in texto and "+52" not in texto
    assert r["documento"]["osm3s"]["timestamp_osm_base"] == "2026-11-16T10:00:00Z"
    assert "openstreetmap" in r["documento"]["osm3s"]["copyright"].lower()   # atribución conservada


# ------------------------------------------------------------ validación
def test_validar_respuesta_de_overpass():
    assert osm.validar_respuesta(respuesta_overpass()) == []
    assert osm.validar_respuesta([]) == ["la respuesta no es un objeto JSON"]
    assert osm.validar_respuesta({"remark": "runtime error"}) == ["falta la lista 'elements'"]
    assert osm.validar_respuesta({"elements": [{"type": "node", "id": 1}]})


# ------------------------------------------------------ red: reintentos
def test_reintenta_ante_429_y_luego_funciona():
    s = SesionPost(Resp(429), Resp(200, respuesta_overpass()))
    datos, endpoint, intentos = osm.consultar("q", s, intentos=3, dormir=sin_espera)
    assert intentos == 2 and endpoint == cfg.OSM_ENDPOINTS[0] and len(datos["elements"]) == 3


def test_usa_el_espejo_si_el_principal_esta_saturado():
    s = SesionPost(Resp(503), Resp(503), Resp(503), Resp(200, respuesta_overpass()))
    _, endpoint, intentos = osm.consultar("q", s, intentos=3, dormir=sin_espera)
    assert endpoint == cfg.OSM_ENDPOINTS[1] and intentos == 4


def test_errores_4xx_no_se_reintentan():
    s = SesionPost(Resp(400))
    with pytest.raises(osm.ErrorOverpass):
        osm.consultar("q", s, dormir=sin_espera)
    assert len(s.llamadas) == 1


def test_timeout_y_json_roto_se_manejan():
    ok = osm.consultar("q", SesionPost(requests.exceptions.Timeout("lento"), Resp(200, respuesta_overpass())),
                       dormir=sin_espera)
    assert ok[2] == 2
    r = osm.descargar_municipio("tecoman", LAT, LON, SesionPost(Resp(200, json_valido=False)), dormir=sin_espera)
    assert not r["ok"] and "JSON" in r["error"]


def test_si_todo_falla_se_registra_sin_lanzar():
    r = osm.descargar_municipio("tecoman", LAT, LON, SesionPost(Resp(504)), intentos=2, dormir=sin_espera)
    assert not r["ok"] and r["documento"] is None and "sin respuesta" in r["error"]


# ----------------------------------------------------- captura completa
def test_captura_completa_guarda_bronce_y_bitacora(tmp_path):
    for mun in cfg.MUNICIPIOS:
        escribir_json_open_meteo(tmp_path / f"clima_historico_{mun}_20261109.json")
    s = SesionPost(Resp(200, respuesta_overpass()))
    res = osm.capturar_todo(hoy=pd.Timestamp("2026-11-17").date(), dir_bronce=tmp_path,
                            ruta_bitacora=tmp_path / "bitacora_osm.csv", sesion=s, dormir=sin_espera)
    assert all(r["ok"] for r in res)
    assert sorted(p.name for p in tmp_path.glob("osm_agricola_*.json")) == [
        "osm_agricola_colima_20261117.json", "osm_agricola_manzanillo_20261117.json",
        "osm_agricola_tecoman_20261117.json"]
    assert "around:10000,19.2267,-103.7092" in s.llamadas[0]["data"]["data"] or \
           "around:10000,19.2267,-103.7092" in s.llamadas[1]["data"]["data"]
    assert len((tmp_path / "bitacora_osm.csv").read_text(encoding="utf-8").splitlines()) == 4


# ------------------------------------------ bronce -> parcelas -> puerta
@pytest.fixture()
def bronce_osm(tmp_path):
    for mun in ("tecoman", "colima"):
        osm_doc = respuesta_overpass(con_datos_personales=False)
        elementos, _ = osm.sanear_elementos(osm_doc["elements"])
        doc = {"fuente": "openstreetmap-overpass", "municipio": mun, "centro": {"lat": LAT, "lon": LON},
               "radio_m": 10_000, "osm3s": osm_doc["osm3s"], "elements": elementos}
        (tmp_path / f"osm_agricola_{mun}_20261116.json").write_text(json.dumps(doc), encoding="utf-8")
    (tmp_path / "osm_agricola_tecoman_20261117.json").write_text(json.dumps({
        "centro": {"lat": LAT, "lon": LON}, "radio_m": 10_000,
        "osm3s": {}, "elements": osm.sanear_elementos(respuesta_overpass(n=5)["elements"])[0]}), encoding="utf-8")
    return tmp_path


def test_se_lee_la_captura_mas_reciente_de_cada_municipio(bronce_osm):
    parcelas, centros = geo.cargar_osm_bronce(bronce_osm)
    assert set(centros) == {"tecoman", "colima"}
    assert (parcelas["municipio"] == "tecoman").sum() == 5     # la del 17 gana a la del 16
    assert (parcelas["municipio"] == "colima").sum() == 3
    archivo, sha12, pos = parcelas.iloc[0]["bronce_ref"].split("|")
    assert archivo.startswith("osm_agricola_") and len(sha12) == 12 and pos == "0"
    assert parcelas["fecha_ingesta"].notna().all()


def test_puerta_geoespacial_manda_lo_invalido_a_cuarentena_con_motivo(bronce_osm):
    parcelas, _ = geo.cargar_osm_bronce(bronce_osm)
    malas = parcelas.head(5).copy().reset_index(drop=True)
    malas.at[0, "uso"] = "industrial"                                    # fuera de catálogo
    malas.at[1, "coords"] = malas.at[1, "coords"][:-1]                  # polígono sin cerrar
    malas.at[2, "coords"] = malas.at[2, "coords"][:3]                   # menos de 4 vértices
    malas.at[3, "coords"] = [(-100.0, 25.0)] * 4                        # fuera de Colima
    todo = pd.concat([malas.iloc[:4], parcelas.iloc[4:]], ignore_index=True)
    validas, cuarentena = geo.validar_parcelas(todo)
    assert len(validas) + len(cuarentena) == len(todo)                 # nada se pierde en silencio
    assert len(cuarentena) == 4
    motivos = " ".join(cuarentena["motivo_rechazo"])
    for texto in ("fuera de catálogo", "no cerrado", "menos de 4 vértices", "fuera del estado"):
        assert texto in motivos


def test_osm_id_repetido_se_rechaza(bronce_osm):
    parcelas, _ = geo.cargar_osm_bronce(bronce_osm)
    repetido = pd.concat([parcelas, parcelas.head(1)], ignore_index=True)
    validas, cuarentena = geo.validar_parcelas(repetido)
    assert len(cuarentena) == 1 and "unicidad" in cuarentena["motivo_rechazo"].iloc[0]


# --------------------------------------------- GeoPandas (en CI y local)
def test_area_agricola_en_hectareas_y_sin_doble_conteo(bronce_osm):
    pytest.importorskip("geopandas")
    parcelas, centros = geo.cargar_osm_bronce(bronce_osm)
    uno = parcelas[(parcelas["municipio"] == "colima")].head(1)
    gdf = geo.a_geodataframe(pd.concat([uno, uno.assign(osm_id=99999)], ignore_index=True))  # mismo polígono dos veces
    r = geo.resumen_agricola(gdf, {"colima": centros["colima"]})
    assert r["area_agricola_ha"].iloc[0] == pytest.approx(100, rel=0.06)   # ≈ 1 km²; no 200
    assert r["pct_area_agricola"].iloc[0] <= 100
    assert r["area_orchard_ha"].iloc[0] > 0 and r["area_vineyard_ha"].iloc[0] == 0


def test_parcelas_lejanas_no_entran_al_circulo(bronce_osm):
    pytest.importorskip("geopandas")
    parcelas, centros = geo.cargar_osm_bronce(bronce_osm)
    lejana = parcelas.head(1).copy()
    lejana["coords"] = [[(lo, la) for lo, la in [(-104.4, 19.4), (-104.39, 19.4), (-104.39, 19.41), (-104.4, 19.41), (-104.4, 19.4)]]]
    gdf = geo.a_geodataframe(lejana)
    r = geo.resumen_agricola(gdf, {"colima": centros["colima"]})
    assert r["n_parcelas"].iloc[0] == 0 and r["area_agricola_ha"].iloc[0] == 0


def test_el_mapa_lleva_la_atribucion_de_osm(bronce_osm, tmp_path):
    pytest.importorskip("geopandas")
    pytest.importorskip("folium")
    from pipeline import mapa
    parcelas, centros = geo.cargar_osm_bronce(bronce_osm)
    gdf = geo.a_geodataframe(parcelas)
    contexto = geo.resumen_agricola(gdf, centros)
    ruta = mapa.construir_mapa(gdf, contexto, centros, tmp_path / "m.html")
    html = ruta.read_text(encoding="utf-8")
    assert "OpenStreetMap" in html and "ODbL" in html and "tecoman" in html.lower()


def test_pipeline_integra_la_capa_agricola_al_oro(bronce_linaje_osm, tmp_path):
    pytest.importorskip("geopandas")
    pytest.importorskip("folium")
    from pipeline.run_pipeline import ejecutar
    r = ejecutar(bronce_linaje_osm, tmp_path / "plata", tmp_path / "oro", tmp_path / "cuarentena",
                 verbose=False, dir_tablero=tmp_path / "tablero")
    assert {"area_agricola_ha", "pct_area_agricola", "radio_agricola_km"} <= set(r["oro_diario"].columns)
    assert (tmp_path / "oro" / "oro_contexto_agricola.csv").exists()
    assert (tmp_path / "plata" / "osm_parcelas.geojson").exists()
    assert (tmp_path / "tablero" / "mapa_agricola.html").exists()
    assert r["reporte"]["osm"]["cuarentena"] == 0


@pytest.fixture()
def bronce_linaje_osm(bronce_linaje):
    for mun in cfg.MUNICIPIOS:
        lat, lon, _ = osm.centro_desde_bronce(mun, bronce_linaje)
        doc = respuesta_overpass(con_datos_personales=False)
        for i, el in enumerate(doc["elements"]):
            el["geometry"] = rectangulo(lat + i * 0.01, lon)
        doc = {"centro": {"lat": lat, "lon": lon}, "radio_m": 10_000, "osm3s": doc["osm3s"],
               "elements": osm.sanear_elementos(doc["elements"])[0]}
        (bronce_linaje / f"osm_agricola_{mun}_20261117.json").write_text(json.dumps(doc), encoding="utf-8")
    return bronce_linaje
