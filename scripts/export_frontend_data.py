import json
import shutil
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DIARIO = RAIZ / "data" / "oro" / "clima_oro_diario.csv"
MENSUAL = RAIZ / "data" / "oro" / "clima_oro_mensual.csv"
LINaje = RAIZ / "data" / "oro" / "reporte_linaje.json"
PLATA = RAIZ / "data" / "plata" / "reporte_puerta_calidad.json"
PSP = RAIZ / "calidad" / "psp_metricas.json"
DESTINO = RAIZ / "frontend" / "public" / "data" / "observatorio.json"


def ejecutar():
    diario = pd.read_csv(DIARIO, parse_dates=["fecha"])
    mensual = pd.read_csv(MENSUAL)
    linaje = json.loads(LINaje.read_text(encoding="utf-8")) if LINaje.exists() else {}
    puerta = json.loads(PLATA.read_text(encoding="utf-8")) if PLATA.exists() else {}
    psp = json.loads(PSP.read_text(encoding="utf-8")) if PSP.exists() else {}
    resumen = []
    for municipio, grupo in diario.groupby("municipio"):
        resumen.append({
            "municipio": municipio,
            "filas": len(grupo),
            "tmax_media": round(float(grupo["tmax_c"].mean()), 2),
            "tmin_media": round(float(grupo["tmin_c"].mean()), 2),
            "precip_total_mm": round(float(grupo["precip_mm"].sum()), 2),
            "viento_max_kmh": round(float(grupo["viento_max_kmh"].max()), 2),
        })
    comparativa = []
    mensual["anio"] = mensual["anio_mes"].str.slice(0, 4).astype(int)
    for municipio, grupo in mensual.groupby("municipio"):
        prior_years = {}
        for year, year_group in grupo.sort_values("anio").groupby("anio"):
            available_months = int(year_group["n_dias"].gt(0).sum())
            tmax_mean = float(year_group["tmax_media"].mean())
            tmin_mean = float(year_group["tmin_media"].mean())
            precip_total = float(year_group["precip_total_mm"].sum())
            wind_mean = float(year_group["viento_medio"].mean())
            historical = [item for item in prior_years.values()]
            history_tmax = (
                sum(item["promedio_historico_tmax_c"] for item in historical) / len(historical)
                if historical else None
            )
            history_tmin = (
                sum(item["promedio_historico_tmin_c"] for item in historical) / len(historical)
                if historical else None
            )
            history_precip = (
                sum(item["promedio_historico_precip_anual_mm"] for item in historical) / len(historical)
                if historical else None
            )
            history_wind = (
                sum(item["promedio_historico_viento_medio_kmh"] for item in historical) / len(historical)
                if historical else None
            )
            def variation(recent, historical_value):
                if historical_value is None or historical_value == 0:
                    return None
                return round((recent - historical_value) / abs(historical_value) * 100, 2)
            record = {
                "municipio": municipio,
                "anio": int(year),
                "meses_disponibles": available_months,
                "meses_esperados": 12,
                "datos_completos": available_months == 12,
                "tmax_media_c": round(tmax_mean, 2),
                "tmin_media_c": round(tmin_mean, 2),
                "precip_anual_mm": round(precip_total, 2),
                "viento_medio_kmh": round(wind_mean, 2),
                "dispersion_tmax_c": round(float(year_group["tmax_media"].std(ddof=1)), 2) if len(year_group) > 1 else 0.0,
                "dispersion_precip_mm": round(float(year_group["precip_total_mm"].std(ddof=1)), 2) if len(year_group) > 1 else 0.0,
                "promedio_historico_tmax_c": round(history_tmax, 2) if history_tmax is not None else None,
                "promedio_historico_tmin_c": round(history_tmin, 2) if history_tmin is not None else None,
                "promedio_historico_precip_anual_mm": round(history_precip, 2) if history_precip is not None else None,
                "promedio_historico_viento_medio_kmh": round(history_wind, 2) if history_wind is not None else None,
                "variacion_tmax_pct": variation(tmax_mean, history_tmax),
                "variacion_tmin_pct": variation(tmin_mean, history_tmin),
                "variacion_precip_pct": variation(precip_total, history_precip),
                "variacion_viento_pct": variation(wind_mean, history_wind),
            }
            comparativa.append(record)
            prior_years[int(year)] = {
                "promedio_historico_tmax_c": tmax_mean,
                "promedio_historico_tmin_c": tmin_mean,
                "promedio_historico_precip_anual_mm": precip_total,
                "promedio_historico_viento_medio_kmh": wind_mean,
            }
    payload = {
        "generado_desde": "data/oro",
        "periodo": {
            "inicio": diario["fecha"].min().strftime("%Y-%m-%d"),
            "fin": diario["fecha"].max().strftime("%Y-%m-%d"),
        },
        "municipios": resumen,
        "mensual": mensual.to_dict(orient="records"),
        "comparativa_interanual": comparativa,
        "linaje": linaje,
        "calidad": puerta,
        "psp": psp,
    }
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    for nombre in ("resultados_e1.json", "resultados_e2.json", "resultados_e3.json"):
        origen = RAIZ / "laboratorio" / nombre
        if origen.exists():
            (DESTINO.parent / nombre).write_text(origen.read_text(encoding="utf-8"), encoding="utf-8")
    biplot = RAIZ / "laboratorio" / "pca_biplot.png"
    if biplot.exists():
        shutil.copy2(biplot, DESTINO.parent / "pca_biplot.png")
    print(DESTINO)


if __name__ == "__main__":
    ejecutar()
