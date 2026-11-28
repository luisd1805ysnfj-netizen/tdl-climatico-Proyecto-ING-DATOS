import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_resultados_e1_tienen_modelos_e_intervalos():
    datos = json.loads((RAIZ / "laboratorio" / "resultados_e1.json").read_text(encoding="utf-8"))
    assert datos["tipo"] == "caracterizacion_series_mensuales"
    for municipio in datos["municipios"].values():
        assert set(municipio["modelos_prueba"]) >= {"simple", "holt", "holt_winters", "arima"}
        assert len(municipio["pronostico_6_meses"]) == 6
        assert {"MAE", "RMSE", "MAPE_pct"} <= set(next(iter(municipio["modelos_prueba"].values())))


def test_resultados_e2_declaran_estado_observacional():
    datos = json.loads((RAIZ / "laboratorio" / "resultados_e2.json").read_text(encoding="utf-8"))
    assert datos["tipo"] == "analisis_observacional_exploratorio"
    assert "C(municipio):C(temporada_mensual)" in datos["anova_tipo_2"]
    assert datos["confirmacion_tratamiento_optimo"]["estado"] == "Pendiente"


def test_resultados_e3_tienen_pca_mahalanobis_y_manova():
    datos = json.loads((RAIZ / "laboratorio" / "resultados_e3.json").read_text(encoding="utf-8"))
    assert len(datos["variables"]) >= 5
    assert len(datos["varianza_explicada"]) == 5
    assert len(datos["mahalanobis_qq"]["distancias"]) > 0
    assert "wilks" in datos["manova"]
    assert "pillai" in datos["manova"]
    assert datos["biplot"]
