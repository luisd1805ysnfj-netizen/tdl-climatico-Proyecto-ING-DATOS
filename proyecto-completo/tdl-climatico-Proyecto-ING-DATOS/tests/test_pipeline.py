"""Pruebas del pipeline de E1. Corren en cada push (CI) con datos sintéticos."""
import json

import numpy as np
import pandas as pd
import pytest

from pipeline import config as cfg
from pipeline import integracion as integ
from pipeline import limpieza as lim
from pipeline import oro
from pipeline import puerta_calidad as puerta
from pipeline.run_pipeline import ejecutar


def _json_open_meteo(ruta, dias=120, lat=19.2, lon=-103.7, unidad_viento="km/h", semilla=1):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2025-01-01", periods=dias, freq="D").strftime("%Y-%m-%d").tolist()
    contenido = {
        "latitude": lat, "longitude": lon, "elevation": 100.0, "timezone": "America/Mexico_City",
        "daily_units": {"time": "iso8601", "temperature_2m_max": "°C", "temperature_2m_min": "°C",
                        "precipitation_sum": "mm", "wind_speed_10m_max": unidad_viento},
        "daily": {
            "time": fechas,
            "temperature_2m_max": (31 + rng.normal(0, 1.5, dias)).round(1).tolist(),
            "temperature_2m_min": (21 + rng.normal(0, 1.5, dias)).round(1).tolist(),
            "precipitation_sum": np.where(rng.random(dias) < 0.4, rng.gamma(1.2, 6, dias), 0).round(1).tolist(),
            "wind_speed_10m_max": (14 + rng.normal(0, 3, dias)).round(1).tolist(),
        },
    }
    ruta.write_text(json.dumps(contenido), encoding="utf-8")


@pytest.fixture()
def bronce(tmp_path):
    d = tmp_path / "bronce"
    d.mkdir()
    for i, mun in enumerate(["tecoman", "colima", "manzanillo"]):
        _json_open_meteo(d / f"clima_historico_{mun}_20261109.json", semilla=i)
    return d


@pytest.fixture()
def df_valido(bronce):
    crudo = integ.cargar_bronce(bronce)
    return integ.integrar(crudo)[0]


# ----------------------------------------------------------- integración
def test_normalizar_municipio():
    assert integ.normalizar_municipio(" TECOMÁN ") == "tecoman"
    assert integ.normalizar_municipio("Manzanillo_Colima") == "manzanillo"
    assert integ.normalizar_municipio(None) is None


def test_carga_bronce_modelo_comun(bronce):
    df = integ.cargar_bronce(bronce)
    assert list(df.columns) == integ.COLUMNAS_MODELO
    assert set(df["municipio"]) == {"tecoman", "colima", "manzanillo"}
    assert (df["fuente"] == "open-meteo-archive").all()


def test_conversion_de_unidades_viento(tmp_path):
    _json_open_meteo(tmp_path / "clima_historico_colima_20261109.json", unidad_viento="m/s")
    df = integ.cargar_open_meteo_archive(tmp_path / "clima_historico_colima_20261109.json")
    assert df["viento_max_kmh"].mean() == pytest.approx(14 * 3.6, abs=3.0)  # 14 m/s -> ~50 km/h


def test_unidad_desconocida_falla(tmp_path):
    _json_open_meteo(tmp_path / "clima_historico_colima_20261109.json", unidad_viento="furlongs")
    with pytest.raises(ValueError):
        integ.cargar_open_meteo_archive(tmp_path / "clima_historico_colima_20261109.json")


def test_duplicados_de_captura_se_registran_no_se_pierden(tmp_path):
    for fecha in ("20261108", "20261109"):
        _json_open_meteo(tmp_path / f"clima_historico_colima_{fecha}.json", dias=10)
    df = integ.cargar_bronce(tmp_path)
    limpio, descartados = integ.integrar(df)
    assert len(df) == 20 and len(limpio) == 10 and len(descartados) == 10
    assert (descartados["fecha_captura"] == pd.Timestamp("2026-11-08")).all()
    assert descartados["motivo_rechazo"].str.contains("duplicado").all()


def test_adaptar_segunda_fuente_resuelve_conflictos():
    crudo = pd.DataFrame({
        "FECHA": ["01/03/2025", "02/03/2025"], "MUNICIPIO": ["Tecomán", "TECOMAN"],
        "TMAX": ["95.0", "Nulo"], "TMIN": ["68.0", "70.0"], "PRECIP": ["0", "1.0"],
    })
    perfil = {**cfg.PERFIL_SMN, "conversiones": {"tmax_c": "f_a_c", "tmin_c": "f_a_c"}}
    df = integ.adaptar_tabla(crudo, perfil, archivo="smn_prueba.csv")
    assert (df["municipio"] == "tecoman").all()
    assert df.loc[0, "tmax_c"] == pytest.approx(35.0)
    assert np.isnan(df.loc[1, "tmax_c"])            # 'Nulo' -> NaN
    assert df["viento_max_kmh"].isna().all()        # la fuente no mide viento
    assert df["fecha"].iloc[0] == pd.Timestamp("2025-03-01")


def test_consolidar_fuentes_prioridad_y_diferencia(df_valido):
    base = df_valido[df_valido["municipio"] == "colima"].head(3).copy()
    smn = base.assign(fuente="smn-conagua", tmax_c=base["tmax_c"] + 1.0, viento_max_kmh=np.nan)
    smn.loc[smn.index[0], "tmax_c"] = np.nan  # el día 1 el SMN no reportó
    c = integ.consolidar_fuentes(pd.concat([base, smn], ignore_index=True))
    assert len(c) == 3 and (c["n_fuentes"] == 2).all()
    assert c.loc[0, "tmax_c"] == pytest.approx(base["tmax_c"].iloc[0])        # cae a open-meteo
    assert c.loc[1, "tmax_c"] == pytest.approx(base["tmax_c"].iloc[1] + 1.0)  # gana smn
    assert c.loc[1, "dif_tmax_c"] == pytest.approx(1.0)
    assert c["viento_max_kmh"].notna().all()                                  # viento solo existe en open-meteo


# ------------------------------------------------------- puerta de calidad
def test_puerta_aprueba_datos_validos(df_valido):
    ok, cuarentena, rep = puerta.aplicar_puerta(df_valido)
    assert len(ok) == len(df_valido) and cuarentena.empty
    assert rep["registros_en_cuarentena"] == 0


def test_puerta_manda_invalidos_a_cuarentena_con_motivo(df_valido):
    malo = df_valido.copy()
    malo.loc[0, "precip_mm"] = -5.0          # imposible
    malo.loc[1, "tmax_c"] = 20.0
    malo.loc[1, "tmin_c"] = 25.0             # tmax < tmin (regla de negocio)
    malo.loc[2, "municipio"] = "mazatlan"    # fuera de catálogo
    malo.loc[3, "viento_max_kmh"] = 900.0    # fuera de rango físico
    malo.loc[4, "fecha"] = pd.Timestamp("2099-01-01")  # fecha futura
    ok, cuarentena, rep = puerta.aplicar_puerta(malo)
    assert len(cuarentena) == 5
    assert len(ok) == len(malo) - 5          # nada se perdió: ok + cuarentena = entrada
    assert cuarentena["motivo_rechazo"].str.len().gt(0).all()
    assert cuarentena["motivo_rechazo"].str.contains("precip_mm").any()
    assert cuarentena["motivo_rechazo"].str.contains("tmax-tmin").any()
    assert rep["registros_en_cuarentena"] == 5 and rep["pct_rechazo"] > 0


def test_puerta_rechaza_duplicado_pero_deja_el_primero(df_valido):
    con_dup = pd.concat([df_valido, df_valido.head(2)], ignore_index=True)
    ok, cuarentena, _ = puerta.aplicar_puerta(con_dup)
    assert len(cuarentena) == 2 and len(ok) == len(df_valido)
    assert cuarentena["motivo_rechazo"].str.contains("unicidad").all()


def test_puerta_faltante_pasa_a_limpieza(df_valido):
    con_nan = df_valido.copy()
    con_nan.loc[0, "tmax_c"] = np.nan
    ok, cuarentena, _ = puerta.aplicar_puerta(con_nan)
    assert cuarentena.empty and len(ok) == len(con_nan)


def test_puerta_falla_si_falta_una_columna(df_valido):
    with pytest.raises(puerta.PuertaCalidadError):
        puerta.aplicar_puerta(df_valido.drop(columns=["precip_mm"]))


# ----------------------------------------------------------------- limpieza
def _plata(df_valido):
    c = integ.consolidar_fuentes(df_valido)
    return lim.completar_calendario(c)


def test_diagnostico_sin_faltantes(df_valido):
    d = lim.diagnosticar_faltantes(_plata(df_valido))
    assert (d["faltantes"] == 0).all()


def test_diagnostico_detecta_mar():
    rng = np.random.default_rng(0)
    n = 600
    df = pd.DataFrame({"tmax_c": rng.normal(30, 2, n), "tmin_c": rng.normal(20, 2, n),
                       "viento_max_kmh": rng.normal(14, 3, n), "precip_mm": rng.gamma(1, 3, n),
                       "municipio": "colima", "mes": rng.integers(1, 13, n)})
    df.loc[df["tmin_c"] > 21.5, "tmax_c"] = np.nan   # ausencia depende de otra variable = MAR
    d = lim.diagnosticar_faltantes(df).set_index("variable")
    assert d.loc["tmax_c", "mecanismo_probable"] == "MAR"


def test_dias_ausentes_se_vuelven_visibles_y_se_imputan(df_valido):
    recortado = df_valido.drop(index=[10, 11, 12]).reset_index(drop=True)
    plata = lim.completar_calendario(integ.consolidar_fuentes(recortado))
    assert plata["fila_agregada"].sum() == 3
    imp = lim.imputar(plata)
    assert imp[cfg.VARIABLES].notna().all().all()
    assert imp["tmax_c_imputado"].sum() == 3


def test_imputacion_no_inventa_variables_que_la_fuente_no_mide(df_valido):
    d = _plata(df_valido).assign(viento_max_kmh=np.nan)
    imp = lim.imputar(d)
    assert imp["viento_max_kmh"].isna().all() and not imp["viento_max_kmh_imputado"].any()


def test_evaluar_imputacion_devuelve_todos_los_metodos(df_valido):
    r = lim.evaluar_imputacion(_plata(df_valido), "tmax_c")
    assert set(r["metodo"]) == {"media", "mediana", "interpolacion_temporal", "climatologia_mensual", "knn"}
    assert (r["rmse"] > 0).all()


def test_atipico_inyectado_se_marca_y_no_se_elimina(df_valido):
    plata = lim.imputar(_plata(df_valido))
    n = len(plata)
    plata.loc[5, "viento_max_kmh"] = 120.0
    marcado = lim.marcar_atipicos(plata)
    assert len(marcado) == n                       # no se borra nada
    assert bool(marcado.loc[5, "atipico_viento_max_kmh"])
    assert bool(marcado.loc[5, "atipico_cualquiera"])


def test_z_robusto_e_iqr():
    s = pd.Series([10, 11, 12, 10, 11, 12, 11, 100.0])
    assert lim.z_robusto(s).iloc[-1] > 3.5
    assert lim.atipicos_iqr(s).iloc[-1]


def test_escalado_minmax_y_z(df_valido):
    plata = lim.imputar(_plata(df_valido))
    params = lim.ajustar_escalado(plata)
    e = lim.aplicar_escalado(plata, params)
    assert e["tmax_c_minmax"].min() == pytest.approx(0.0) and e["tmax_c_minmax"].max() == pytest.approx(1.0)
    assert e["tmax_c_z"].mean() == pytest.approx(0.0, abs=1e-9)
    assert e["tmax_c_z"].std() == pytest.approx(1.0, abs=1e-9)


def test_discretizacion_y_jerarquias(df_valido):
    plata = lim.imputar(_plata(df_valido))
    d = lim.agregar_jerarquias(lim.discretizar(plata))
    assert d["tmax_categoria"].notna().all() and d["precip_categoria"].notna().all()
    assert set(d["temporada"]) <= {"lluvias", "secas"}
    assert d.loc[d["municipio"] == "manzanillo", "zona"].eq("Costa").all()
    assert (d["estado"] == "Colima").all()
    assert (d.loc[d["precip_mm"] == 0, "precip_categoria"] == "sin_lluvia").all()


def test_reduccion_mensual_y_seleccion(df_valido):
    plata = lim.marcar_atipicos(lim.imputar(_plata(df_valido)))
    oro_d = lim.agregar_jerarquias(lim.discretizar(plata))
    m = lim.reducir_mensual(oro_d)
    assert len(m) < len(oro_d) and m["n_dias"].sum() == len(oro_d)
    sel = lim.seleccion_variables(plata, umbral=0.9)
    assert set(sel["conservadas"]) | set(sel["descartadas"]) == set(cfg.VARIABLES)


def test_diccionario_cubre_tablas():
    d = oro.diccionario_df()
    assert {"diaria", "mensual", "ambas"} >= set(d["tabla"])
    assert d["descripcion"].str.len().gt(5).all()


# --------------------------------------------------------- flujo completo
def test_pipeline_completo_bronce_a_oro(bronce, tmp_path):
    r = ejecutar(bronce, tmp_path / "plata", tmp_path / "oro", tmp_path / "cuarentena", verbose=False)
    assert (tmp_path / "plata" / "clima_plata.csv").exists()
    assert (tmp_path / "oro" / "clima_oro_diario.csv").exists()
    assert (tmp_path / "oro" / "clima_oro_mensual.csv").exists()
    assert (tmp_path / "oro" / "diccionario_datos.csv").exists()
    assert (tmp_path / "oro" / "params_escalado.json").exists()
    rep = json.loads((tmp_path / "plata" / "reporte_puerta_calidad.json").read_text(encoding="utf-8"))
    assert rep["puerta"]["registros_recibidos"] == 360 and rep["cuarentena_total"] == 0
    assert len(r["oro_diario"]) == 360 and len(r["oro_mensual"]) < 360


def test_pipeline_con_registro_malo_lo_manda_a_cuarentena(bronce, tmp_path):
    ruta = bronce / "clima_historico_colima_20261109.json"
    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    contenido["daily"]["precipitation_sum"][3] = -9.0
    ruta.write_text(json.dumps(contenido), encoding="utf-8")
    r = ejecutar(bronce, tmp_path / "plata", tmp_path / "oro", tmp_path / "cuarentena", verbose=False)
    assert len(r["cuarentena"]) == 1
    archivos = list((tmp_path / "cuarentena").glob("cuarentena_*.csv"))
    assert len(archivos) == 1
    assert "precip_mm" in pd.read_csv(archivos[0])["motivo_rechazo"].iloc[0]
    # el día rechazado aparece como faltante imputado, no desaparece en silencio
    assert r["reporte"]["imputados"]["precip_mm"] == 1
