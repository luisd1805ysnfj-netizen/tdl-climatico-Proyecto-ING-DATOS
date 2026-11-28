import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing, Holt
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, adfuller, pacf

RAIZ = Path(__file__).resolve().parents[1]
DIARIO = RAIZ / "data" / "oro" / "clima_oro_diario.csv"
SALIDA = RAIZ / "laboratorio" / "resultados_e1.json"


def ejecutar():
    df = pd.read_csv(DIARIO, parse_dates=["fecha"])
    municipios = {}
    for municipio, grupo in df.groupby("municipio"):
        serie = grupo.sort_values("fecha").set_index("fecha")["precip_mm"].resample("ME").sum().dropna()
        if len(serie) < 24:
            continue
        adf = adfuller(serie, result_object=False)
        serie_diff = serie.diff().dropna()
        adf_diff = adfuller(serie_diff, result_object=False)
        shapiro = stats.shapiro(serie) if len(serie) >= 3 else (float("nan"), float("nan"))
        try:
            descomposicion = seasonal_decompose(serie, model="additive", period=12, extrapolate_trend="period")
            decomposition = {
                "model": "additive",
                "seasonal_mean": round(float(descomposicion.seasonal.mean()), 6),
                "residual_std": round(float(descomposicion.resid.dropna().std(ddof=1)), 6),
                "trend_last": round(float(descomposicion.trend.dropna().iloc[-1]), 6),
            }
        except (ValueError, FloatingPointError):
            decomposition = {"model": "not_available", "reason": "No fue posible descomponer la serie mensual"}

        acf_values = acf(serie, nlags=min(12, len(serie) // 3), fft=True).tolist()
        pacf_values = pacf(serie, nlags=min(12, len(serie) // 3), method="ywm").tolist()

        train_size = max(24, int(len(serie) * 0.8))
        train, test = serie.iloc[:train_size], serie.iloc[train_size:]
        horizon = len(test)
        model_predictions = {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model_predictions["simple"] = np.repeat(train.iloc[-1], horizon)
            try:
                model_predictions["holt"] = Holt(train, initialization_method="estimated").fit(
                    optimized=True
                ).forecast(horizon).to_numpy()
            except (ValueError, TypeError, FloatingPointError):
                model_predictions["holt"] = np.repeat(train.iloc[-1], horizon)
            try:
                hw = ExponentialSmoothing(
                    train, trend="add", seasonal="add", seasonal_periods=12,
                    initialization_method="estimated"
                ).fit(optimized=True)
                model_predictions["holt_winters"] = hw.forecast(horizon).to_numpy()
            except (ValueError, TypeError, FloatingPointError):
                model_predictions["holt_winters"] = np.repeat(train.iloc[-1], horizon)
            try:
                arima = ARIMA(train, order=(1, 1, 1)).fit()
                model_predictions["arima"] = arima.forecast(steps=horizon).to_numpy()
            except (ValueError, TypeError, FloatingPointError):
                model_predictions["arima"] = np.repeat(train.iloc[-1], horizon)

        model_metrics = {}
        residual_test = {}
        for name, predictions in model_predictions.items():
            actual = test.to_numpy()
            errors = actual - predictions
            mae = float(np.mean(np.abs(errors)))
            rmse = float(np.sqrt(np.mean(errors ** 2)))
            mask = actual != 0
            mape = float(np.mean(np.abs(errors[mask] / actual[mask])) * 100) if mask.any() else None
            ljung = acorr_ljungbox(pd.Series(errors).dropna(), lags=[min(10, len(errors) - 1)], return_df=True)
            residual_test[name] = {
                "ljung_box_p_valor": round(float(ljung["lb_pvalue"].iloc[-1]), 6),
                "media_residual": round(float(np.mean(errors)), 6),
                "varianza_residual": round(float(np.var(errors, ddof=1)), 6),
            }
            model_metrics[name] = {
                "MAE": round(mae, 6),
                "RMSE": round(rmse, 6),
                "MAPE_pct": None if mape is None else round(mape, 6),
            }

        forecast_steps = 6
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                selected = ExponentialSmoothing(
                    serie, trend="add", seasonal="add", seasonal_periods=12,
                    initialization_method="estimated"
                ).fit(optimized=True)
                forecast_values = selected.forecast(forecast_steps).to_numpy()
                residuals = serie.to_numpy() - selected.fittedvalues.to_numpy()
            except (ValueError, TypeError, FloatingPointError):
                forecast_values = np.repeat(serie.iloc[-1], forecast_steps)
                residuals = serie.to_numpy() - serie.iloc[-1]
        sigma = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0
        last_date = serie.index[-1]
        future_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=forecast_steps, freq="ME")
        forecasts = [
            {
                "fecha": date.strftime("%Y-%m"),
                "pronostico": round(float(value), 6),
                "limite_inferior_95": round(float(value - 1.96 * sigma), 6),
                "limite_superior_95": round(float(value + 1.96 * sigma), 6),
            }
            for date, value in zip(future_dates, forecast_values)
        ]

        cross_corr = {}
        for other_variable in ("tmax_c", "tmin_c", "viento_max_kmh"):
            if other_variable not in df.columns:
                continue
            other = grupo.sort_values("fecha").set_index("fecha")[other_variable].resample("ME").mean().dropna()
            aligned = pd.concat([serie.rename("y"), other.rename("x")], axis=1).dropna()
            cross_corr[other_variable] = {
                str(lag): round(float(aligned["y"].corr(aligned["x"].shift(lag))), 6)
                for lag in range(-3, 4)
            }

        municipios[municipio] = {
            "n_meses": len(serie),
            "media": round(float(serie.mean()), 3),
            "mediana": round(float(serie.median()), 3),
            "desviacion": round(float(serie.std(ddof=1)), 3),
            "descomposicion": decomposition,
            "adf": {
                "estadistico": None if pd.isna(adf[0]) else round(float(adf[0]), 6),
                "p_valor": None if pd.isna(adf[1]) else round(float(adf[1]), 6),
                "rezagos": int(adf[2]),
            },
            "diferenciacion": {
                "adf_estadistico": None if pd.isna(adf_diff[0]) else round(float(adf_diff[0]), 6),
                "adf_p_valor": None if pd.isna(adf_diff[1]) else round(float(adf_diff[1]), 6),
                "n_observaciones": len(serie_diff),
            },
            "acf": [round(float(value), 6) for value in acf_values],
            "pacf": [round(float(value), 6) for value in pacf_values],
            "correlacion_cruzada": cross_corr,
            "modelos_prueba": model_metrics,
            "residuos": residual_test,
            "pronostico_6_meses": forecasts,
            "shapiro": {
                "estadistico": None if pd.isna(shapiro[0]) else round(float(shapiro[0]), 6),
                "p_valor": None if pd.isna(shapiro[1]) else round(float(shapiro[1]), 6),
            },
        }
    resultado = {
        "tipo": "caracterizacion_series_mensuales",
        "variable": "precip_mm",
        "unidad": "mm",
        "municipios": municipios,
        "nota": "ADF evalua estacionariedad; Shapiro complementa caracterizacion univariada.",
    }
    SALIDA.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(SALIDA)


if __name__ == "__main__":
    ejecutar()
