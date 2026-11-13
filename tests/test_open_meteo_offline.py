"""Pruebas unitarias OFFLINE de la captura de Open-Meteo.

No tocan internet: usan una respuesta REAL de Open-Meteo guardada como fixture
(tests/fixtures/open_meteo_colima_7dias.json, recortada a 7 días) y una sesión falsa que
simula éxitos, saturación (429/500), timeouts y respuestas dañadas.
"""
import copy
import csv
import json
from datetime import date
from pathlib import Path

import pytest
import requests

from extractors import captura_diaria as cap
from extractors.clima_extractor import USER_AGENT
from pipeline import integracion as integ

FIXTURE = Path(__file__).parent / "fixtures" / "open_meteo_colima_7dias.json"
COORDS = {"lat": 19.2433, "lon": -103.7250}
INICIO, FIN = date(2026, 11, 1), date(2026, 11, 7)


def respuesta_real():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class RespuestaFalsa:
    def __init__(self, status=200, cuerpo=None, json_valido=True):
        self.status_code, self._cuerpo, self._valido = status, cuerpo, json_valido

    def json(self):
        if not self._valido:
            raise ValueError("no es JSON")
        return self._cuerpo


class SesionFalsa:
    """Responde en orden con lo que se le programe; registra cada petición."""

    def __init__(self, *respuestas):
        self.respuestas, self.peticiones = list(respuestas), []

    def get(self, url, params=None, timeout=None):
        self.peticiones.append({"url": url, "params": params, "timeout": timeout})
        r = self.respuestas.pop(0) if len(self.respuestas) > 1 else self.respuestas[0]
        if isinstance(r, Exception):
            raise r
        return r


def sin_espera(segundos):
    sin_espera.llamadas.append(segundos)


sin_espera.llamadas = []


# ------------------------------------------------------------- petición
def test_parametros_de_la_peticion():
    p = cap.construir_parametros(COORDS, INICIO, FIN)
    assert p["latitude"] == 19.2433 and p["longitude"] == -103.7250
    assert p["start_date"] == "2026-11-01" and p["end_date"] == "2026-11-07"
    assert p["timezone"] == "auto"
    assert p["daily"].split(",") == cap.VARIABLES_DIARIAS


def test_la_sesion_se_identifica_con_user_agent_honesto():
    s = cap.crear_sesion()
    assert s.headers["User-Agent"] == USER_AGENT
    assert "TDL" in USER_AGENT


# ----------------------------------------------------------- validación
def test_respuesta_real_de_open_meteo_es_valida():
    assert cap.validar_respuesta(respuesta_real()) == []


def test_validacion_detecta_respuestas_danadas():
    r = respuesta_real()
    assert "falta el bloque 'daily'" in cap.validar_respuesta({"latitude": 1})
    assert cap.validar_respuesta([1, 2]) == ["la respuesta no es un objeto JSON"]

    sin_var = copy.deepcopy(r)
    del sin_var["daily"]["precipitation_sum"]
    assert any("precipitation_sum" in p for p in cap.validar_respuesta(sin_var))

    desigual = copy.deepcopy(r)
    desigual["daily"]["temperature_2m_max"].pop()
    assert any("temperature_2m_max" in p and "valores" in p for p in cap.validar_respuesta(desigual))

    fahrenheit = copy.deepcopy(r)
    fahrenheit["daily_units"]["temperature_2m_max"] = "°F"
    assert any("unidad inesperada" in p for p in cap.validar_respuesta(fahrenheit))

    vacia = copy.deepcopy(r)
    vacia["daily"]["time"] = []
    assert any("vacío" in p for p in cap.validar_respuesta(vacia))


# ---------------------------------------------- descarga y reintentos
def test_descarga_exitosa():
    s = SesionFalsa(RespuestaFalsa(200, respuesta_real()))
    r = cap.descargar_municipio("colima", COORDS, INICIO, FIN, s, dormir=sin_espera)
    assert r["ok"] and r["filas"] == 7 and r["intentos"] == 1 and r["http_status"] == 200
    assert s.peticiones[0]["url"] == cap.URL_ARCHIVO
    assert s.peticiones[0]["timeout"] == cap.TIMEOUT_S


def test_reintenta_ante_429_y_luego_funciona():
    sin_espera.llamadas.clear()
    s = SesionFalsa(RespuestaFalsa(429), RespuestaFalsa(200, respuesta_real()))
    r = cap.descargar_municipio("colima", COORDS, INICIO, FIN, s, pausa_reintento=2.0, dormir=sin_espera)
    assert r["ok"] and r["intentos"] == 2
    assert sin_espera.llamadas == [2.0]            # espera antes de reintentar


def test_espera_exponencial_y_falla_tras_agotar_intentos():
    sin_espera.llamadas.clear()
    s = SesionFalsa(RespuestaFalsa(500))
    r = cap.descargar_municipio("colima", COORDS, INICIO, FIN, s, intentos=3,
                                pausa_reintento=2.0, dormir=sin_espera)
    assert not r["ok"] and r["intentos"] == 3 and "500" in r["error"]
    assert sin_espera.llamadas == [2.0, 4.0]       # 2 s, 4 s (no espera tras el último)


def test_error_4xx_no_se_reintenta():
    s = SesionFalsa(RespuestaFalsa(400))
    r = cap.descargar_municipio("colima", COORDS, INICIO, FIN, s, dormir=sin_espera)
    assert not r["ok"] and r["intentos"] == 1 and len(s.peticiones) == 1


def test_timeout_se_reintenta():
    s = SesionFalsa(requests.exceptions.Timeout("lento"), RespuestaFalsa(200, respuesta_real()))
    r = cap.descargar_municipio("colima", COORDS, INICIO, FIN, s, dormir=sin_espera)
    assert r["ok"] and r["intentos"] == 2


def test_json_roto_no_pasa():
    s = SesionFalsa(RespuestaFalsa(200, json_valido=False))
    r = cap.descargar_municipio("colima", COORDS, INICIO, FIN, s, dormir=sin_espera)
    assert not r["ok"] and "JSON" in r["error"]


def test_respuesta_200_con_forma_invalida_no_pasa():
    mala = respuesta_real()
    del mala["daily"]["wind_speed_10m_max"]
    r = cap.descargar_municipio("colima", COORDS, INICIO, FIN,
                                SesionFalsa(RespuestaFalsa(200, mala)), dormir=sin_espera)
    assert not r["ok"] and "respuesta inválida" in r["error"]


# ------------------------------------------------- captura completa
def test_captura_completa_guarda_archivos_y_bitacora(tmp_path):
    s = SesionFalsa(RespuestaFalsa(200, respuesta_real()))
    res = cap.capturar_todo(hoy=date(2026, 11, 9), dir_bronce=tmp_path / "bronce",
                            ruta_bitacora=tmp_path / "bitacora.csv", sesion=s,
                            pausa=1.0, dormir=sin_espera)
    assert all(r["ok"] for r in res)
    nombres = sorted(p.name for p in (tmp_path / "bronce").glob("*.json"))
    assert nombres == ["clima_historico_colima_20261109.json",
                       "clima_historico_manzanillo_20261109.json",
                       "clima_historico_tecoman_20261109.json"]
    filas = list(csv.DictReader(open(tmp_path / "bitacora.csv", encoding="utf-8")))
    assert len(filas) == 3 and all(f["exito"] == "True" for f in filas)
    # ventana: termina 2 días antes de hoy y cubre 7 días
    assert s.peticiones[0]["params"]["end_date"] == "2026-11-07"
    assert s.peticiones[0]["params"]["start_date"] == "2026-11-01"


def test_pausa_entre_municipios_cumple_la_regla_de_1_segundo(tmp_path):
    sin_espera.llamadas.clear()
    cap.capturar_todo(hoy=date(2026, 11, 9), dir_bronce=tmp_path / "b",
                      ruta_bitacora=tmp_path / "bit.csv",
                      sesion=SesionFalsa(RespuestaFalsa(200, respuesta_real())), dormir=sin_espera)
    assert sin_espera.llamadas == [1.0, 1.0] and min(sin_espera.llamadas) >= 1.0


def test_si_un_municipio_falla_se_registra_y_no_se_guarda_basura(tmp_path):
    ok, caido = RespuestaFalsa(200, respuesta_real()), RespuestaFalsa(500)
    s = SesionFalsa(ok, caido, caido, caido, ok)   # orden: tecoman ok, colima falla 3 veces, manzanillo ok
    res = cap.capturar_todo(hoy=date(2026, 11, 9), dir_bronce=tmp_path / "b",
                            ruta_bitacora=tmp_path / "bit.csv", sesion=s, dormir=sin_espera)
    fallidos = [r for r in res if not r["ok"]]
    assert [r["municipio"] for r in fallidos] == ["colima"]
    guardados = list((tmp_path / "b").glob("*.json"))
    assert len(guardados) == len(res) - len(fallidos)
    filas = list(csv.DictReader(open(tmp_path / "bit.csv", encoding="utf-8")))
    assert len(filas) == 3 and any(f["exito"] == "False" and f["error"] for f in filas)
    assert not list((tmp_path / "b").glob("*.tmp"))


def test_bitacora_acumula_corridas(tmp_path):
    ruta = tmp_path / "bit.csv"
    for _ in range(2):
        cap.capturar_todo(hoy=date(2026, 11, 9), dir_bronce=tmp_path / "b", ruta_bitacora=ruta,
                          sesion=SesionFalsa(RespuestaFalsa(200, respuesta_real())), dormir=sin_espera)
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    assert lineas[0].split(",") == cap.CAMPOS_BITACORA and len(lineas) == 1 + 6


# -------------------------------- compatibilidad con el pipeline
def test_lo_que_captura_el_extractor_lo_lee_el_pipeline(tmp_path):
    cap.capturar_todo(hoy=date(2026, 11, 9), dir_bronce=tmp_path / "b", ruta_bitacora=tmp_path / "bit.csv",
                      sesion=SesionFalsa(RespuestaFalsa(200, respuesta_real())), dormir=sin_espera)
    df = integ.cargar_bronce(tmp_path / "b")
    assert len(df) == 3 * 7 and set(df["municipio"]) == {"colima", "manzanillo", "tecoman"}
    assert df["tmax_c"].notna().all()


def test_la_prueba_realmente_esta_offline():
    with pytest.raises((RuntimeError, requests.exceptions.RequestException)):
        requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=1)
