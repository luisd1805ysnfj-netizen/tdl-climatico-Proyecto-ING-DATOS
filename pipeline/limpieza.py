"""Limpieza y preprocesamiento (capa plata y features de la capa oro).

Cada función corresponde a un punto de la rúbrica de E1 de Ingeniería de Datos:
faltantes, atípicos y ruido, normalización, discretización/jerarquías, reducción.
Ninguna borra datos: todo lo que se corrige o sospecha queda marcado con banderas.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.impute import KNNImputer

from . import config as cfg

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


# ----------------------------------------------------------------- calendario
def agregar_calendario(df):
    df = df.copy()
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    return df


def completar_calendario(df):
    """Hace visibles los días AUSENTES (filas que nunca llegaron) como NaN."""
    partes = []
    for mun, g in df.groupby("municipio", sort=True):
        rango = pd.date_range(g["fecha"].min(), g["fecha"].max(), freq="D")
        g = g.set_index("fecha").reindex(rango)
        g["fila_agregada"] = g["municipio"].isna()
        g["municipio"] = mun
        g.index.name = "fecha"
        partes.append(g.reset_index())
    out = pd.concat(partes, ignore_index=True)
    out["fila_agregada"] = out["fila_agregada"].astype(bool)
    return agregar_calendario(out)


# ------------------------------------------------------------------ faltantes
def diagnosticar_faltantes(df, variables=None, alfa=0.01):
    """Cuenta faltantes y orienta el diagnóstico del mecanismo (MCAR/MAR/MNAR).

    - MAR: la ausencia de la variable se asocia con OTRAS variables observadas,
      con el municipio o con el mes (Mann-Whitney / chi-cuadrada, Bonferroni).
    - MCAR plausible: no hay asociación detectable.
    - MNAR no se puede probar solo con los datos: se argumenta por dominio.
    """
    variables = variables or cfg.VARIABLES
    filas = []
    for v in variables:
        falta = df[v].isna()
        n = int(falta.sum())
        fila = {"variable": v, "faltantes": n, "pct": round(100 * n / len(df), 3),
                "mecanismo_probable": "sin faltantes", "evidencia": ""}
        if n > 0:
            pruebas = []
            for otra in [x for x in variables if x != v]:
                a, b = df.loc[falta, otra].dropna(), df.loc[~falta, otra].dropna()
                if len(a) > 5 and len(b) > 5:
                    pruebas.append((otra, stats.mannwhitneyu(a, b).pvalue))
            for cat in ["municipio", "mes"]:
                tabla = pd.crosstab(df[cat], falta)
                if tabla.shape[1] == 2:
                    pruebas.append((cat, stats.chi2_contingency(tabla)[1]))
            umbral = alfa / max(len(pruebas), 1)
            asociadas = [f"{k} (p={p:.3g})" for k, p in pruebas if p < umbral]
            if asociadas:
                fila["mecanismo_probable"] = "MAR"
                fila["evidencia"] = "asociado con: " + ", ".join(asociadas)
            else:
                fila["mecanismo_probable"] = "MCAR plausible (MNAR no descartable por dominio)"
                fila["evidencia"] = "sin asociación detectable con otras variables, municipio o mes"
        filas.append(fila)
    return pd.DataFrame(filas)


def _knn_columna(g, var, k=5):
    """Imputa `var` con KNN usando las demás variables + estacionalidad (sen/cos del día)."""
    X = g[cfg.VARIABLES].copy().dropna(axis=1, how="all")  # no usar variables que la fuente no mide
    doy = g["fecha"].dt.dayofyear.to_numpy()
    X["sen"], X["cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    mu, sd = X.mean(), X.std().replace(0, 1)
    Xi = KNNImputer(n_neighbors=k).fit_transform((X - mu) / sd)
    return Xi[:, list(X.columns).index(var)] * sd[var] + mu[var]


def evaluar_imputacion(df, var, frac=0.10, escenario="aleatorio", largo_bloque=5,
                       semilla=cfg.SEMILLA):
    """Enmascara valores REALES y mide qué método los recupera mejor (RMSE/MAE).

    escenario="aleatorio": huecos de un día. "bloques": huecos de `largo_bloque` días.
    Sirve para JUSTIFICAR el método de imputación con evidencia, no por gusto.
    """
    rng = np.random.default_rng(semilla)
    acumulado = {}
    for _, g in df.sort_values("fecha").groupby("municipio"):
        g = g.reset_index(drop=True)
        n = len(g)
        mascara = np.zeros(n, dtype=bool)
        if escenario == "aleatorio":
            mascara[rng.choice(n, int(frac * n), replace=False)] = True
        else:
            for s in rng.choice(n - largo_bloque, max(int(frac * n / largo_bloque), 1), replace=False):
                mascara[s:s + largo_bloque] = True
        real = g[var].to_numpy(float)
        s = g[var].where(~mascara)
        s.index = g["fecha"]
        pred = {
            "media": np.full(n, s.mean()),
            "mediana": np.full(n, s.median()),
            "interpolacion_temporal": s.interpolate(method="time", limit_direction="both").to_numpy(),
            "climatologia_mensual": s.groupby(g["fecha"].dt.month.to_numpy()).transform("mean").to_numpy(),
        }
        pred["knn"] = _knn_columna(g.assign(**{var: g[var].where(~mascara).to_numpy()}), var)
        for nombre, p in pred.items():
            err = np.asarray(p)[mascara] - real[mascara]
            acumulado.setdefault(nombre, []).append((np.sqrt(np.mean(err ** 2)), np.mean(np.abs(err))))
    filas = [{"metodo": m, "rmse": float(np.mean([x[0] for x in v])),
              "mae": float(np.mean([x[1] for x in v]))} for m, v in acumulado.items()]
    return pd.DataFrame(filas).sort_values("rmse").reset_index(drop=True)


def imputar(df):
    """Imputa según la evidencia de `evaluar_imputacion`. Toda imputación se marca.

    - tmax, tmin, viento: interpolación temporal (máx. LIMITE_INTERPOLACION_DIAS
      seguidos); lo que quede se completa con la mediana climatológica mes/municipio.
    - precipitación: KNN con las demás variables y la estacionalidad (fue el método
      de menor RMSE en el experimento de enmascarado; la interpolación no sirve
      porque la lluvia es intermitente).
    - Si una fuente nunca midió una variable (columna 100% vacía en el municipio)
      no se inventa: se deja NaN.
    """
    df = df.sort_values(["municipio", "fecha"]).reset_index(drop=True).copy()
    for v in cfg.VARIABLES:
        df[f"{v}_imputado"] = False
    for _, idx in df.groupby("municipio").groups.items():
        for v in ["tmax_c", "tmin_c", "viento_max_kmh", "precip_mm"]:  # lluvia al final
            g = df.loc[idx]
            if g[v].isna().all() or not g[v].isna().any():
                continue
            falta = g[v].isna()
            if v == "precip_mm":
                valores = pd.Series(_knn_columna(g, v), index=g.index).clip(lower=0).round(1)
            else:
                s = g.set_index("fecha")[v].interpolate(
                    method="time", limit=cfg.LIMITE_INTERPOLACION_DIAS, limit_area="inside")
                clim = g.groupby(g["fecha"].dt.month)[v].transform("median")
                valores = pd.Series(s.fillna(pd.Series(clim.to_numpy(), index=s.index)).to_numpy(),
                                    index=g.index)
            df.loc[idx, v] = np.where(falta, valores, g[v])
            df.loc[idx, f"{v}_imputado"] = falta.to_numpy()
    return df


# -------------------------------------------------------------------- atípicos
def z_robusto(serie):
    """Puntaje z modificado (Iglewicz-Hoaglin): 0.6745 * (x - mediana) / MAD."""
    med = np.nanmedian(serie)
    mad = np.nanmedian(np.abs(serie - med))
    if mad == 0 or np.isnan(mad):
        return pd.Series(0.0, index=serie.index)
    return 0.6745 * (serie - med) / mad


def atipicos_iqr(serie, k=1.5):
    q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
    iqr = q3 - q1
    return (serie < q1 - k * iqr) | (serie > q3 + k * iqr)


def marcar_atipicos(df):
    """Marca (NO elimina) valores sospechosos con tres métodos complementarios.

    1) z robusto sobre la ANOMALÍA (valor - mediana del mes/municipio) para tmax,
       tmin y viento: así la estacionalidad normal no se confunde con un atípico.
    2) IQR (k=3) sobre los DÍAS CON LLUVIA (precip > 0): con ~60% de días en cero un
       IQR sobre todos los días no sirve. Se probó sobre log1p y no marcaba casi nada
       (el log comprime justo la cola que interesa), así que se usa la escala lineal.
    3) Isolation Forest multivariado (1%) para combinaciones raras de variables.

    Decisión: se marcan y se conservan. Un valor imposible físicamente ya fue
    rechazado por la puerta de calidad; lo que llega aquí es clima extremo que
    puede ser real (y el hallazgo más interesante del observatorio).
    """
    df = df.copy()
    anom = pd.DataFrame(index=df.index)
    for v in ["tmax_c", "tmin_c", "viento_max_kmh"]:
        clim = df.groupby(["municipio", "mes"])[v].transform("median")
        anom[v] = df[v] - clim
        z = anom[v].groupby(df["municipio"]).transform(z_robusto)
        df[f"z_robusto_{v}"] = z
        df[f"atipico_{v}"] = z.abs() > cfg.UMBRAL_Z_ROBUSTO
    lluvia = df["precip_mm"].where(df["precip_mm"] > 0)
    q1 = lluvia.groupby(df["municipio"]).transform(lambda s: s.quantile(0.25))
    q3 = lluvia.groupby(df["municipio"]).transform(lambda s: s.quantile(0.75))
    df["atipico_precip_mm"] = (lluvia > q3 + cfg.K_IQR_LLUVIA * (q3 - q1)).fillna(False)
    anom["precip_log"] = np.log1p(df["precip_mm"])

    X = anom.fillna(0.0)
    X = (X - X.mean()) / X.std().replace(0, 1)
    bosque = IsolationForest(contamination=cfg.CONTAMINACION_IFOREST, random_state=cfg.SEMILLA)
    df["atipico_multivariado"] = bosque.fit_predict(X) == -1
    cols = [c for c in df.columns if c.startswith("atipico_")]
    df["atipico_cualquiera"] = df[cols].any(axis=1)
    return df


def suavizar_ruido(df, ventana=7):
    """Columnas suavizadas para visualización; el dato original no se toca."""
    df = df.sort_values(["municipio", "fecha"]).copy()
    for v in ["tmax_c", "tmin_c", "viento_max_kmh"]:
        df[f"{v}_m{ventana}"] = df.groupby("municipio")[v].transform(
            lambda s: s.rolling(ventana, center=True, min_periods=ventana // 2 + 1).mean())
    df[f"precip_mm_acum{ventana}"] = df.groupby("municipio")["precip_mm"].transform(
        lambda s: s.rolling(ventana, min_periods=1).sum())
    return df


# ------------------------------------------------------------- normalización
def ajustar_escalado(df, variables=None):
    """Parámetros de min-max y z-score. Se guardan para reusarlos con datos nuevos."""
    variables = variables or cfg.VARIABLES
    return {v: {"min": float(df[v].min()), "max": float(df[v].max()),
                "media": float(df[v].mean()), "desv": float(df[v].std(ddof=1))}
            for v in variables}


def aplicar_escalado(df, params):
    df = df.copy()
    for v, p in params.items():
        rango = (p["max"] - p["min"]) or 1.0
        df[f"{v}_minmax"] = (df[v] - p["min"]) / rango
        df[f"{v}_z"] = (df[v] - p["media"]) / (p["desv"] or 1.0)
    return df


# ------------------------------------------------- discretización y jerarquías
def discretizar(df):
    """Tres técnicas: umbrales de dominio, frecuencia igual y ancho igual."""
    df = df.copy()
    df["tmax_categoria"] = pd.cut(df["tmax_c"], cfg.BINS_TMAX, labels=cfg.ETIQ_TMAX)
    df["precip_categoria"] = pd.cut(df["precip_mm"], cfg.BINS_PRECIP, labels=cfg.ETIQ_PRECIP)
    df["tmin_cuartil"] = pd.qcut(df["tmin_c"], 4, labels=["Q1_baja", "Q2", "Q3", "Q4_alta"])
    df["viento_rango"] = pd.cut(df["viento_max_kmh"], bins=4, labels=["R1_leve", "R2", "R3", "R4_fuerte"])
    df["dia_lluvioso"] = df["precip_mm"] >= 1.0
    return df


def agregar_jerarquias(df):
    """fecha -> mes -> trimestre -> temporada -> año; municipio -> zona -> estado."""
    df = df.copy()
    df["anio"] = df["fecha"].dt.year
    df["trimestre"] = df["fecha"].dt.quarter
    df["mes_nombre"] = df["mes"].map(lambda m: MESES[int(m) - 1])
    df["anio_mes"] = df["fecha"].dt.strftime("%Y-%m")
    df["temporada"] = np.where(df["mes"].isin(cfg.MESES_LLUVIA), "lluvias", "secas")
    df["zona"] = df["municipio"].map(lambda m: cfg.MUNICIPIOS[m]["zona"])
    df["estado"] = cfg.ESTADO
    return df


# --------------------------------------------------------------------- reducción
def reducir_mensual(df):
    """Reducción por agregación: diario -> mensual, conservando los extremos."""
    g = df.groupby(["municipio", "anio_mes"], sort=True)
    m = g.agg(
        n_dias=("fecha", "size"),
        tmax_media=("tmax_c", "mean"), tmax_max=("tmax_c", "max"),
        tmin_media=("tmin_c", "mean"), tmin_min=("tmin_c", "min"),
        precip_total_mm=("precip_mm", "sum"),
        dias_lluvia=("dia_lluvioso", "sum"),
        viento_medio=("viento_max_kmh", "mean"), viento_max=("viento_max_kmh", "max"),
        n_atipicos=("atipico_cualquiera", "sum"),
    ).round(3).reset_index()
    return m


def seleccion_variables(df, umbral=0.90, variables=None):
    """Reducción por selección: de cada par con |r| > umbral se descarta una variable."""
    variables = variables or cfg.VARIABLES
    corr = df[variables].corr()
    descartar, pares = set(), []
    for i, a in enumerate(variables):
        for b in variables[i + 1:]:
            if abs(corr.loc[a, b]) > umbral and a not in descartar and b not in descartar:
                pares.append((a, b, float(corr.loc[a, b])))
                descartar.add(b)
    return {"correlaciones": corr, "pares_redundantes": pares,
            "conservadas": [v for v in variables if v not in descartar],
            "descartadas": sorted(descartar)}
