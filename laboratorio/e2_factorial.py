import json
from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

RAIZ = Path(__file__).resolve().parents[1]
DIARIO = RAIZ / "data" / "oro" / "clima_oro_diario.csv"
SALIDA = RAIZ / "laboratorio" / "resultados_e2.json"


def ejecutar():
    df = pd.read_csv(DIARIO, parse_dates=["fecha"])
    df = df.dropna(subset=["municipio", "precip_mm", "tmax_c"])
    df["temporada_mensual"] = pd.cut(
        df["mes"],
        bins=[0, 3, 6, 9, 12],
        labels=["ene_mar", "abr_jun", "jul_sep", "oct_dic"],
        include_lowest=True,
    ).astype(str)

    formula = "precip_mm ~ C(municipio) * C(temporada_mensual)"
    model = ols(formula, data=df).fit()
    table = sm.stats.anova_lm(model, typ=2)
    anova = {
        str(term): {
            "sum_sq": round(float(row["sum_sq"]), 6),
            "df": int(row["df"]),
            "F": None if pd.isna(row.get("F")) else round(float(row["F"]), 6),
            "p_valor": None if pd.isna(row.get("PR(>F)")) else round(float(row["PR(>F)"]), 6),
        }
        for term, row in table.iterrows()
    }

    residuals = model.resid
    shapiro = residuals.sample(min(500, len(residuals)), random_state=42)
    from scipy import stats
    normalidad = stats.shapiro(shapiro)

    design = {
        "tipo": "analisis_observacional_exploratorio",
        "advertencia": (
            "No corresponde a un experimento aleatorizado ni a una corrida agrícola "
            "controlada. Los factores municipio y temporada de calendario provienen "
            "de datos observados de Open-Meteo."
        ),
        "respuesta": "precip_mm",
        "factores": {
            "municipio": ["colima", "manzanillo", "tecoman"],
            "temporada_mensual": ["ene_mar", "abr_jun", "jul_sep", "oct_dic"],
        },
        "matriz_completo": "3 x 4 = 12 combinaciones",
        "matriz_fraccionada": "No se dispone de experimentos aleatorizados ni réplicas controladas",
        "alias": "No aplicable: no existe diseño fraccionado ejecutado",
        "ahorro_corridas_pct": None,
        "n_observaciones": len(df),
        "anova_tipo_2": anova,
        "supuestos": {
            "shapiro_residuos": {
                "n": len(shapiro),
                "estadistico": round(float(normalidad.statistic), 6),
                "p_valor": round(float(normalidad.pvalue), 6),
            },
            "media_residuos": round(float(residuals.mean()), 6),
            "varianza_residuos": round(float(residuals.var(ddof=1)), 6),
        },
        "confirmacion_tratamiento_optimo": {
            "estado": "Pendiente",
            "razon": "No existe experimento controlado ni corrida de confirmación.",
        },
    }
    SALIDA.write_text(json.dumps(design, indent=2, ensure_ascii=False), encoding="utf-8")
    print(SALIDA)


if __name__ == "__main__":
    ejecutar()
