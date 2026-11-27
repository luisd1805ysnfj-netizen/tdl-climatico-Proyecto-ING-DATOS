"""Integración de fuentes heterogéneas (bronce -> modelo común).

Resuelve conflictos de esquema (nombres de columnas), de tipos (fechas y
números), de unidades (°F, m/s, pulgadas), de zona horaria, de nombres de
municipio (entity resolution) y de duplicados entre capturas y entre fuentes.
"""
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as cfg

PATRON_ARCHIVO = re.compile(r"clima_historico_(?P<mun>[a-z_]+)_(?P<fecha>\d{8})\.json$")

COLUMNAS_MODELO = [
    "fecha", "municipio", "fuente", *cfg.VARIABLES,
    "lat_grid", "lon_grid", "elevacion_m", "zona_horaria",
    "fecha_original", "archivo_origen", "fecha_captura",
]

# Conversión de unidades hacia las canónicas (°C, mm, km/h).
CONVERSIONES = {
    "f_a_c": lambda s: (s - 32.0) * 5.0 / 9.0,
    "k_a_c": lambda s: s - 273.15,
    "ms_a_kmh": lambda s: s * 3.6,
    "mph_a_kmh": lambda s: s * 1.609344,
    "kn_a_kmh": lambda s: s * 1.852,
    "pulg_a_mm": lambda s: s * 25.4,
}
UNIDADES_OPEN_METEO = {
    "temperature_2m_max": {"°C": None, "°F": "f_a_c"},
    "temperature_2m_min": {"°C": None, "°F": "f_a_c"},
    "precipitation_sum": {"mm": None, "inch": "pulg_a_mm"},
    "wind_speed_10m_max": {"km/h": None, "m/s": "ms_a_kmh", "mph": "mph_a_kmh",
                           "kn": "kn_a_kmh"},
}
RENOMBRE_OPEN_METEO = {
    "temperature_2m_max": "tmax_c", "temperature_2m_min": "tmin_c",
    "precipitation_sum": "precip_mm", "wind_speed_10m_max": "viento_max_kmh",
}


def normalizar_municipio(valor):
    """'Tecomán', ' TECOMAN ', 'tecoman_colima' -> 'tecoman'."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return None
    s = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z]+", "_", s.strip().lower()).strip("_")
    return cfg.ALIAS_MUNICIPIOS.get(s, s)


def cargar_open_meteo_archive(ruta):
    """Lee un JSON de la API de archivo de Open-Meteo y lo lleva al modelo común."""
    ruta = Path(ruta)
    m = PATRON_ARCHIVO.search(ruta.name)
    if not m:
        raise ValueError(f"Nombre de archivo no reconocido: {ruta.name}")
    with open(ruta, encoding="utf-8") as f:
        crudo = json.load(f)

    diario = crudo["daily"]
    unidades = crudo.get("daily_units", {})
    df = pd.DataFrame({"fecha_original": diario["time"]})
    for origen, destino in RENOMBRE_OPEN_METEO.items():
        serie = pd.to_numeric(pd.Series(diario.get(origen, [np.nan] * len(df))),
                              errors="coerce")
        conv = UNIDADES_OPEN_METEO[origen].get(unidades.get(origen), None)
        if unidades.get(origen) not in UNIDADES_OPEN_METEO[origen]:
            raise ValueError(f"Unidad desconocida para {origen}: {unidades.get(origen)}")
        df[destino] = CONVERSIONES[conv](serie) if conv else serie

    df["fecha"] = pd.to_datetime(df["fecha_original"], format="%Y-%m-%d", errors="coerce")
    df["municipio"] = normalizar_municipio(m["mun"])
    df["fuente"] = "open-meteo-archive"
    # Open-Meteo "ajusta" las coordenadas pedidas a su celda de malla:
    # se guardan las reales, no las solicitadas.
    df["lat_grid"] = crudo.get("latitude")
    df["lon_grid"] = crudo.get("longitude")
    df["elevacion_m"] = crudo.get("elevation")
    df["zona_horaria"] = crudo.get("timezone")
    df["archivo_origen"] = ruta.name
    df["fecha_captura"] = pd.to_datetime(m["fecha"], format="%Y%m%d")
    return df[COLUMNAS_MODELO]


def adaptar_tabla(crudo, perfil, archivo="(memoria)", fecha_captura=None):
    """Lleva una tabla de otra fuente (p. ej. CSV del SMN) al modelo común.

    `perfil` describe cómo traducir esa fuente (ver config.PERFIL_SMN).
    """
    df = crudo.rename(columns=perfil["columnas"]).copy()
    out = pd.DataFrame(index=df.index)
    out["fecha_original"] = df["fecha"].astype(str)
    fechas = pd.to_datetime(df["fecha"], format=perfil.get("formato_fecha"), errors="coerce")
    tz = perfil.get("tz_origen")
    if tz:  # fecha-hora en otra zona -> fecha calendario local
        fechas = (pd.to_datetime(df["fecha"], errors="coerce", utc=True)
                  .dt.tz_convert("America/Mexico_City").dt.tz_localize(None).dt.normalize())
    out["fecha"] = fechas
    out["municipio"] = df["municipio"].map(normalizar_municipio)
    out["fuente"] = perfil["fuente"]
    for v in cfg.VARIABLES:
        if v in df.columns:
            s = pd.to_numeric(df[v].replace(perfil.get("valores_nulos", []), np.nan),
                              errors="coerce")
            if v in perfil.get("conversiones", {}):
                s = CONVERSIONES[perfil["conversiones"][v]](s)
            out[v] = s
        else:
            out[v] = np.nan  # la fuente no mide esta variable
    out["lat_grid"] = np.nan
    out["lon_grid"] = np.nan
    out["elevacion_m"] = np.nan
    out["zona_horaria"] = "America/Mexico_City"
    out["archivo_origen"] = archivo
    out["fecha_captura"] = pd.to_datetime(fecha_captura) if fecha_captura else pd.Timestamp.today().normalize()
    return out[COLUMNAS_MODELO]


def cargar_csv_smn(ruta, perfil=None):
    perfil = perfil or cfg.PERFIL_SMN
    crudo = pd.read_csv(ruta, encoding=perfil.get("encoding", "utf-8"), dtype=str)
    return adaptar_tabla(crudo, perfil, archivo=Path(ruta).name)


def cargar_bronce(directorio=None):
    """Carga todo lo que haya en bronce: JSON de Open-Meteo y CSV del SMN."""
    directorio = Path(directorio or cfg.DIR_BRONCE)
    partes = [cargar_open_meteo_archive(p) for p in sorted(directorio.glob("clima_historico_*.json"))]
    partes += [cargar_csv_smn(p) for p in sorted(directorio.glob("smn_*.csv"))]
    if not partes:
        raise FileNotFoundError(f"No hay archivos de bronce en {directorio}")
    return pd.concat(partes, ignore_index=True)


def integrar(df):
    """Elimina duplicados entre capturas de la MISMA fuente (queda la más reciente).

    Devuelve (df_integrado, descartados). Los descartados NO se pierden:
    el pipeline los registra en cuarentena con su motivo.
    """
    df = df.sort_values(["fuente", "municipio", "fecha", "fecha_captura"], kind="stable")
    dup = df.duplicated(["fuente", "municipio", "fecha"], keep="last")
    descartados = df[dup].assign(
        regla="unicidad_captura",
        motivo_rechazo="duplicado: reemplazado por una captura más reciente de la misma fuente",
    )
    return df[~dup].reset_index(drop=True), descartados.reset_index(drop=True)


def consolidar_fuentes(df, prioridad=None):
    """Un registro por (municipio, fecha), combinando fuentes variable por variable.

    - Cada variable toma el primer valor no nulo según `prioridad`.
    - `n_fuentes` y `fuentes_usadas` documentan el linaje.
    - `dif_<var>` guarda la discrepancia absoluta entre fuentes cuando hay 2+.
    """
    prioridad = prioridad or cfg.PRIORIDAD_FUENTES
    rango = {f: i for i, f in enumerate(prioridad)}
    d = df.assign(_rk=df["fuente"].map(rango).fillna(len(rango))) \
          .sort_values(["municipio", "fecha", "_rk"], kind="stable")
    llave = ["municipio", "fecha"]
    g = d.groupby(llave, sort=True)

    base = d.drop_duplicates(llave, keep="first").set_index(llave)  # metadatos de la fuente principal
    base[cfg.VARIABLES] = g[cfg.VARIABLES].first()                  # primer no nulo por variable
    base["n_fuentes"] = g.size()
    base["fuentes_usadas"] = g["fuente"].agg("+".join)
    for v in cfg.VARIABLES:
        rng = g[v].agg(lambda s: s.max() - s.min() if s.notna().sum() > 1 else np.nan)
        base[f"dif_{v}"] = rng
    base = base.drop(columns=["_rk"]).reset_index()
    return base
