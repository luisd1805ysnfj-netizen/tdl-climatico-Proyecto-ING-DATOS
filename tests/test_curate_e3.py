import pandas as pd
import pytest

from scripts.curate_e3 import curate_frame


def _oro_row(**overrides):
    row = {
        "fecha": "2026-01-02T00:00:00",
        "municipio": "colima",
        "estado": "Colima",
        "lat_grid": 19.2,
        "lon_grid": -103.7,
        "elevacion_m": 400.0,
        "tmax_c": 30.0,
        "tmin_c": 20.0,
        "precip_mm": 1.2,
        "viento_max_kmh": 8.0,
        "fuente": "open-meteo-archive",
        "fuentes_usadas": "open-meteo-archive",
        "n_fuentes": 1,
        "fecha_captura": "2026-01-03T00:00:00",
        "fila_agregada": False,
        "tmax_c_imputado": False,
        "tmin_c_imputado": False,
        "precip_mm_imputado": False,
        "viento_max_kmh_imputado": False,
        "atipico_cualquiera": False,
        "id_registro": "colima|2026-01-02",
        "archivo_origen": "clima_historico_colima_20260103.json",
        "bronce_sha256": "a" * 64,
        "bronce_fila": 0,
        "bronce_ref": "clima_historico_colima_20260103.json|aaaaaaaaaaaa|0",
        "origen_tmax_c": "clima_historico_colima_20260103.json|aaaaaaaaaaaa|0",
        "origen_tmin_c": "clima_historico_colima_20260103.json|aaaaaaaaaaaa|0",
        "origen_precip_mm": "clima_historico_colima_20260103.json|aaaaaaaaaaaa|0",
        "origen_viento_max_kmh": "clima_historico_colima_20260103.json|aaaaaaaaaaaa|0",
    }
    row.update(overrides)
    return row


def test_curate_frame_formats_dates_and_keeps_compact_numeric_types():
    result = curate_frame(pd.DataFrame([_oro_row()]))

    assert result.loc[0, "fecha"] == "2026-01-02"
    assert result.loc[0, "fecha_captura"] == "2026-01-03"
    assert str(result["tmax_c"].dtype) == "float32"
    assert result.loc[0, "origen_tmax_c"] == "clima_historico_colima_20260103.json|aaaaaaaaaaaa|0"


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"tmax_c": None}, "nulos en campos requeridos"),
        ({"tmax_c": 18.0}, "tmax_c menor que tmin_c"),
        ({"bronce_sha256": None}, "nulos en campos requeridos"),
    ],
)
def test_curate_frame_rejects_invalid_critical_data(overrides, message):
    with pytest.raises(ValueError, match=message):
        curate_frame(pd.DataFrame([_oro_row(**overrides)]))


def test_curate_frame_rejects_duplicate_municipality_day():
    with pytest.raises(ValueError, match="más de un registro"):
        curate_frame(pd.DataFrame([
            _oro_row(),
            _oro_row(id_registro="otro-id"),
        ]))


def test_curate_frame_rejects_invalid_lineage_hash():
    with pytest.raises(ValueError, match="bronce_sha256"):
        curate_frame(pd.DataFrame([_oro_row(bronce_sha256="hash-invalido")]))
