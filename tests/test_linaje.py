"""Linaje: cada valor de la capa oro se rastrea hasta su archivo de bronce y su fecha de ingesta."""
import json

import pandas as pd

from pipeline import config as cfg
from pipeline import integracion as integ
from pipeline import oro
from pipeline.run_pipeline import ejecutar


def correr(bronce, tmp_path):
    return ejecutar(bronce, tmp_path / "plata", tmp_path / "oro", tmp_path / "cuarentena",
                    verbose=False)


def test_la_huella_no_depende_del_sistema_operativo():
    assert integ.huella_archivo(b"a\r\nb\r\n") == integ.huella_archivo(b"a\nb\n")
    assert integ.huella_archivo(b"a") != integ.huella_archivo(b"b")


def test_bronce_trae_archivo_huella_y_posicion(bronce_linaje):
    df = integ.cargar_bronce(bronce_linaje)
    fila = df[(df["municipio"] == "colima")].iloc[3]
    archivo, sha12, pos = fila["bronce_ref"].split("|")
    assert archivo == "clima_historico_colima_20261109.json" and pos == "3"
    assert fila["bronce_sha256"].startswith(sha12) and len(fila["bronce_sha256"]) == 64
    assert fila["fecha_captura"] == pd.Timestamp("2026-11-09")


def test_todo_el_oro_es_rastreable(bronce_linaje, tmp_path):
    r = correr(bronce_linaje, tmp_path)
    rep = oro.verificar_linaje(r["oro_diario"], bronce_linaje)
    assert rep["fallos"] == 0
    assert rep["trazables"] == len(r["oro_diario"]) * len(cfg.VARIABLES)
    assert (tmp_path / "oro" / "reporte_linaje.json").exists()


def test_id_registro_es_unico_y_estable(bronce_linaje, tmp_path):
    d = correr(bronce_linaje, tmp_path)["oro_diario"]
    assert d["id_registro"].is_unique
    assert d["id_registro"].iloc[0] == f"{d['municipio'].iloc[0]}|{d['fecha'].iloc[0]:%Y-%m-%d}"


def test_si_alguien_edita_el_bronce_la_huella_lo_delata(bronce_linaje, tmp_path):
    d = correr(bronce_linaje, tmp_path)["oro_diario"]
    ruta = bronce_linaje / "clima_historico_colima_20261109.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos["daily"]["temperature_2m_max"][0] += 5
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    rep = oro.verificar_linaje(d, bronce_linaje)
    assert rep["fallos"] > 0 and "huella" in rep["detalle_fallos"][0][2]


def test_si_oro_no_coincide_con_bronce_se_detecta(bronce_linaje, tmp_path):
    d = correr(bronce_linaje, tmp_path)["oro_diario"].copy()
    d.loc[0, "tmax_c"] += 1.0
    rep = oro.verificar_linaje(d, bronce_linaje)
    assert rep["fallos"] == 1 and "distinto" in rep["detalle_fallos"][0][2]


def test_si_falta_el_archivo_de_bronce_se_detecta(bronce_linaje, tmp_path):
    d = correr(bronce_linaje, tmp_path)["oro_diario"]
    (bronce_linaje / "clima_historico_tecoman_20261109.json").unlink()
    rep = oro.verificar_linaje(d, bronce_linaje)
    assert rep["fallos"] > 0 and "no existe" in rep["detalle_fallos"][0][2]


def test_los_valores_imputados_se_declaran_no_se_esconden(bronce_linaje, tmp_path):
    ruta = bronce_linaje / "clima_historico_manzanillo_20261109.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos["daily"]["temperature_2m_max"][5] = None   # el día 6 llegó sin temperatura máxima
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    d = correr(bronce_linaje, tmp_path)["oro_diario"]
    fila = d[(d["municipio"] == "manzanillo")].iloc[5]
    assert fila["origen_tmax_c"].startswith("IMPUTADO:")
    assert fila["origen_tmin_c"].count("|") == 2       # los demás valores sí vienen de bronce
    rep = oro.verificar_linaje(d, bronce_linaje)
    assert rep["fallos"] == 0 and rep["imputados"] == 1


def test_el_oro_mensual_declara_de_que_dias_sale(bronce_linaje, tmp_path):
    r = correr(bronce_linaje, tmp_path)
    m = r["oro_mensual"]
    assert m["n_dias"].sum() == len(r["oro_diario"])
    assert (m["primer_dia"] <= m["ultimo_dia"]).all()
    assert (m["ultima_ingesta"] == pd.Timestamp("2026-11-09")).all()
    assert (m["n_dias_imputados"] == 0).all()


def test_el_diccionario_documenta_el_linaje():
    d = oro.diccionario_df()["columna"].tolist()
    assert "id_registro" in d and "origen_<variable>" in d and "primer_dia / ultimo_dia" in d
