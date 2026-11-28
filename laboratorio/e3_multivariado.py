import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.formula.api import ols
from statsmodels.multivariate.manova import MANOVA

RAIZ = Path(__file__).resolve().parents[1]
DIARIO = RAIZ / "data" / "oro" / "clima_oro_diario.csv"
SALIDA = RAIZ / "laboratorio" / "resultados_e3.json"
VARIABLES = ["tmax_c", "tmin_c", "precip_mm", "viento_max_kmh", "elevacion_m"]


def ejecutar():
    df = pd.read_csv(DIARIO)
    variables = VARIABLES
    x = df[variables].dropna()
    x_std = StandardScaler().fit_transform(x)
    pca = PCA(n_components=min(5, x_std.shape[1]))
    pca.fit(x_std)
    cargas = pca.components_.T
    scores = pca.transform(x_std)

    cov = np.cov(x_std.T)
    inv_cov = np.linalg.pinv(cov)
    center = x_std.mean(axis=0)
    mahal = np.einsum("ij,jk,ik->i", x_std - center, inv_cov, x_std - center)
    mahal_sorted = np.sort(mahal)
    chi_quantiles = stats.chi2.ppf((np.arange(1, len(mahal_sorted) + 1) - 0.5) / len(mahal_sorted), df=len(VARIABLES))
    mardia_n = len(x)
    centered = x_std - x_std.mean(axis=0)
    inv_cov_observed = np.linalg.pinv(np.cov(centered.T))
    squared = np.einsum("ij,jk,ik->i", centered, inv_cov_observed, centered)
    n = len(centered)
    skewness = float(np.sum(squared ** 3) / (n ** 2))
    kurtosis = float(np.sum(squared ** 2) / n)
    expected_kurtosis = len(VARIABLES) * (len(VARIABLES) + 2)

    municipio = df.loc[x.index, "municipio"]
    manova = MANOVA.from_formula(
        "tmax_c + tmin_c + precip_mm + viento_max_kmh + elevacion_m ~ C(municipio)",
        data=pd.DataFrame({
            "municipio": municipio,
            "tmax_c": x["tmax_c"].to_numpy(),
            "tmin_c": x["tmin_c"].to_numpy(),
            "precip_mm": x["precip_mm"].to_numpy(),
            "viento_max_kmh": x["viento_max_kmh"].to_numpy(),
            "elevacion_m": x["elevacion_m"].to_numpy(),
        }),
    )
    manova_result = manova.mv_test()
    c_mun = manova_result.results["C(municipio)"]["stat"]
    wilks = None
    pillai = None
    for row_name, row in c_mun.iterrows():
        if "Wilks" in str(row_name):
            wilks = {str(key): round(float(value), 6) if np.isscalar(value) else str(value) for key, value in row.items()}
        if "Pillai" in str(row_name):
            pillai = {str(key): round(float(value), 6) if np.isscalar(value) else str(value) for key, value in row.items()}

    univariate = {}
    for variable in VARIABLES:
        fit = ols(f"{variable} ~ C(municipio)", data=pd.DataFrame({
            "municipio": municipio,
            variable: x[variable].to_numpy(),
        })).fit()
        table = sm.stats.anova_lm(fit, typ=2)
        row = table.loc["C(municipio)"]
        univariate[variable] = {
            "F": round(float(row["F"]), 6),
            "p_valor": round(float(row["PR(>F)"]), 6),
        }
    biplot_path = RAIZ / "laboratorio" / "pca_biplot.png"
    fig, ax = plt.subplots(figsize=(9, 7))
    for municipio_name in sorted(df.loc[x.index, "municipio"].unique()):
        mask = df.loc[x.index, "municipio"].to_numpy() == municipio_name
        ax.scatter(scores[mask, 0], scores[mask, 1], s=12, alpha=0.45, label=municipio_name)
    for i, variable in enumerate(VARIABLES):
        ax.arrow(0, 0, cargas[i, 0] * 4, cargas[i, 1] * 4,
                 head_width=0.12, head_length=0.12, fc="#355740", ec="#355740", alpha=0.8)
        ax.text(cargas[i, 0] * 4.3, cargas[i, 1] * 4.3, variable,
                fontsize=9, color="#355740")
    ax.axhline(0, color="#ccd4cc", linewidth=0.8)
    ax.axvline(0, color="#ccd4cc", linewidth=0.8)
    ax.set_xlabel("Componente principal 1")
    ax.set_ylabel("Componente principal 2")
    ax.set_title("Biplot PCA multivariado")
    ax.legend()
    fig.tight_layout()
    fig.savefig(biplot_path, dpi=160)
    plt.close(fig)

    salida = {
        "tipo": "PCA_MANOVA",
        "n_observaciones": len(x),
        "variables": variables,
        "estandarizacion": "StandardScaler",
        "varianza_explicada": [round(float(v), 6) for v in pca.explained_variance_ratio_],
        "varianza_acumulada": [round(float(v), 6) for v in np.cumsum(pca.explained_variance_ratio_)],
        "cargas": {
            variables[i]: [round(float(v), 6) for v in cargas[i]]
            for i in range(len(variables))
        },
        "component_names": [
            "PC1_ambiente_termico",
            "PC2_tmin_precipitacion",
            "PC3_viento_precipitacion",
            "PC4_viento_elevacion",
            "PC5_contraste_residual",
        ],
        "normalidad_multivariada": {
            "metodo": "Aproximacion Mardia/curtosis multivariada",
            "n": mardia_n,
            "asimetria_cubica": round(skewness, 6),
            "curtosis_observada": round(kurtosis, 6),
            "curtosis_esperada_aprox": expected_kurtosis,
            "estado": "Diagnostico aproximado; no sustituye Henze-Zirkler",
        },
        "mahalanobis_qq": {
            "n": len(mahal_sorted),
            "distancias": [round(float(value), 6) for value in mahal_sorted[:500]],
            "cuantiles_chi2": [round(float(value), 6) for value in chi_quantiles[:500]],
        },
        "manova": {
            "factor": "municipio",
            "wilks": wilks,
            "pillai": pillai,
            "estado": "Resultados extraidos de statsmodels; revisar detalle si alguna tabla no expone Wilks/Pillai",
        },
        "anova_separados": univariate,
        "biplot": "laboratorio/pca_biplot.png",
    }
    SALIDA.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(SALIDA)


if __name__ == "__main__":
    ejecutar()
