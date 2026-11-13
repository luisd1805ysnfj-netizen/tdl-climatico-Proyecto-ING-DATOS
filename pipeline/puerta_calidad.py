"""Puerta de calidad 1 (bronce -> plata): validación con pandera + cuarentena.

Regla de oro del proyecto: un registro que no cumple NO se borra en silencio.
Va a `data/cuarentena/` con la(s) regla(s) violada(s) y el valor que la rompió.
Los errores de ESQUEMA (falta una columna completa) detienen el pipeline, porque
no hay registro al cual culpar.
"""
from datetime import datetime

import pandas as pd

try:  # pandera >= 0.24
    import pandera.pandas as pa
except ImportError:  # versiones anteriores
    import pandera as pa

from . import config as cfg


class PuertaCalidadError(RuntimeError):
    """Falla de esquema: el lote completo no se puede validar."""


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def _check_numerico(nombre):
    # pandera usa `error` (si existe) como texto del rechazo, así que lleva el detalle de la regla.
    regla = f"{nombre}: tipo numerico"
    return pa.Check(lambda s: _num(s).notna(), name=regla, error=regla)


def _check_rango(nombre, lo, hi):
    regla = f"{nombre}: rango [{lo}, {hi}]"
    return pa.Check(lambda s: _num(s).between(lo, hi), name=regla, error=regla)

def construir_esquema(hoy=None):
    hoy = pd.Timestamp(hoy) if hoy is not None else pd.Timestamp.today().normalize()
    fmin = pd.Timestamp(cfg.FECHA_MINIMA)
    columnas = {
        "municipio": pa.Column(nullable=False, checks=pa.Check(
            lambda s: s.isin(list(cfg.MUNICIPIOS)), name="municipio: en catalogo")),
        "fuente": pa.Column(nullable=False, checks=pa.Check(
            lambda s: s.isin(cfg.FUENTES_VALIDAS), name="fuente: en catalogo")),
        "fecha": pa.Column(nullable=False, checks=[
            pa.Check(lambda s: pd.to_datetime(s, errors="coerce").notna(),
                     name="fecha: formato valido"),
            pa.Check(lambda s: pd.to_datetime(s, errors="coerce").between(fmin, hoy),
                     name=f"fecha: entre {cfg.FECHA_MINIMA} y hoy (sin fechas futuras)"),
        ]),
        "lat_grid": pa.Column(nullable=True, checks=_check_rango("lat_grid", *cfg.LIMITES_COORD["lat"])),
        "lon_grid": pa.Column(nullable=True, checks=_check_rango("lon_grid", *cfg.LIMITES_COORD["lon"])),
        # Regla de negocio: la máxima nunca puede ser menor que la mínima.
        "amplitud_termica_c": pa.Column(nullable=True, checks=_check_rango(
            "tmax-tmin (regla de negocio tmax>=tmin)", 0.0, cfg.AMPLITUD_MAX_C)),
        # Unicidad: se acepta la primera aparición; las repetidas se rechazan.
        "clave": pa.Column(nullable=False, checks=pa.Check(
            lambda s: ~s.duplicated(keep="first"), name="unicidad: fuente+municipio+fecha")),
    }
    for var, (lo, hi) in cfg.RANGOS_FISICOS.items():
        # Un faltante (NaN) pasa la puerta: es tema de limpieza, no de invalidez.
        columnas[var] = pa.Column(nullable=True, checks=[_check_numerico(var), _check_rango(var, lo, hi)])
    return pa.DataFrameSchema(columnas, strict=False)


def _preparar(df):
    e = df.copy()
    e["amplitud_termica_c"] = _num(e["tmax_c"]) - _num(e["tmin_c"])
    fechas = pd.to_datetime(e["fecha"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("NaT")
    e["clave"] = e["fuente"].astype(str) + "|" + e["municipio"].astype(str) + "|" + fechas
    return e


def aplicar_puerta(df, hoy=None):
    """Valida `df` y separa aprobados de cuarentena.

    Devuelve (aprobados, cuarentena, reporte).
    """
    df = df.reset_index(drop=True)
    entrada = _preparar(df)
    try:
        construir_esquema(hoy).validate(entrada, lazy=True)
        fallos = pd.DataFrame(columns=["column", "check", "failure_case", "index"])
    except pa.errors.SchemaErrors as exc:
        fallos = exc.failure_cases.copy()
    except pa.errors.SchemaError as exc:  # pragma: no cover
        raise PuertaCalidadError(str(exc)) from exc

    if len(fallos) and fallos["index"].isna().any():
        malos = fallos[fallos["index"].isna()][["column", "check"]].drop_duplicates()
        raise PuertaCalidadError(f"Falla de esquema (no atribuible a un registro):\n{malos}")

    if len(fallos):
        fallos["index"] = fallos["index"].astype(int)
        fallos["regla"] = fallos["column"].astype(str) + " :: " + fallos["check"].astype(str)
        fallos["detalle"] = fallos["regla"] + " (valor=" + fallos["failure_case"].astype(str) + ")"
        por_fila = fallos.groupby("index").agg(
            reglas_violadas=("regla", lambda s: " | ".join(sorted(set(s)))),
            motivo_rechazo=("detalle", lambda s: " | ".join(sorted(set(s)))),
        )
    else:
        por_fila = pd.DataFrame(columns=["reglas_violadas", "motivo_rechazo"])

    rechazado = df.index.isin(por_fila.index)
    aprobados = df[~rechazado].reset_index(drop=True)
    cuarentena = df[rechazado].join(por_fila).assign(
        regla=lambda d: d["reglas_violadas"],
        fecha_rechazo=datetime.now().isoformat(timespec="seconds"),
    ).reset_index(drop=True)

    reporte = {
        "registros_recibidos": len(df),
        "registros_aprobados": len(aprobados),
        "registros_en_cuarentena": len(cuarentena),
        "pct_rechazo": round(100 * len(cuarentena) / max(len(df), 1), 3),
        "rechazos_por_regla": (fallos["regla"].value_counts().to_dict() if len(fallos) else {}),
    }
    return aprobados, cuarentena, reporte


def guardar_cuarentena(cuarentena, directorio=None):
    """Escribe el CSV de cuarentena (si hay algo) y devuelve su ruta."""
    directorio = directorio or cfg.DIR_CUARENTENA
    directorio.mkdir(parents=True, exist_ok=True)
    if cuarentena.empty:
        return None
    ruta = directorio / f"cuarentena_{datetime.now():%Y%m%d_%H%M%S}.csv"
    cuarentena.to_csv(ruta, index=False, encoding="utf-8")
    return ruta
