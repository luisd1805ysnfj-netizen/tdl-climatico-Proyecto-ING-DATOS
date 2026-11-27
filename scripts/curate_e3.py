"""Valida y publica el oro diario como CSV y Parquet curados para E3."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CURATED_COLUMNS = [
    "fecha",
    "municipio",
    "estado",
    "lat_grid",
    "lon_grid",
    "elevacion_m",
    "tmax_c",
    "tmin_c",
    "precip_mm",
    "viento_max_kmh",
    "fuente",
    "fuentes_usadas",
    "n_fuentes",
    "fecha_captura",
    "fila_agregada",
    "tmax_c_imputado",
    "tmin_c_imputado",
    "precip_mm_imputado",
    "viento_max_kmh_imputado",
    "atipico_cualquiera",
    "id_registro",
    "archivo_origen",
    "bronce_sha256",
    "bronce_fila",
    "bronce_ref",
    "origen_tmax_c",
    "origen_tmin_c",
    "origen_precip_mm",
    "origen_viento_max_kmh",
]
CLIMATE_COLUMNS = ["tmax_c", "tmin_c", "precip_mm", "viento_max_kmh"]
FLOAT_COLUMNS = [
    "lat_grid",
    "lon_grid",
    "elevacion_m",
    *CLIMATE_COLUMNS,
]
BOOLEAN_COLUMNS = [
    "fila_agregada",
    "tmax_c_imputado",
    "tmin_c_imputado",
    "precip_mm_imputado",
    "viento_max_kmh_imputado",
    "atipico_cualquiera",
]
CATEGORY_COLUMNS = ["municipio", "estado", "fuente", "fuentes_usadas"]


def curate_frame(source):
    missing_columns = sorted(set(CURATED_COLUMNS) - set(source.columns))
    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas del oro diario: {missing_columns}")

    data = source[CURATED_COLUMNS].copy()
    for column in ("fecha", "fecha_captura"):
        parsed = pd.to_datetime(data[column], errors="coerce")
        if parsed.isna().any():
            raise ValueError(f"{column} contiene fechas nulas o inválidas")
        data[column] = parsed.dt.strftime("%Y-%m-%d")

    for column in FLOAT_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce", downcast="float")
    for column, dtype in (("n_fuentes", "uint8"), ("bronce_fila", "uint16")):
        values = pd.to_numeric(data[column], errors="coerce")
        if (
            values.isna().any()
            or (values < 0).any()
            or (values % 1 != 0).any()
            or values.max() > np.iinfo(dtype).max
        ):
            raise ValueError(f"{column} debe contener enteros no negativos dentro de {dtype}")
        data[column] = values.astype(dtype)

    for column in BOOLEAN_COLUMNS:
        values = data[column].astype(str).str.strip().str.lower().map({
            "true": True,
            "false": False,
            "1": True,
            "0": False,
        })
        if values.isna().any():
            raise ValueError(f"{column} contiene valores booleanos inválidos o nulos")
        data[column] = values.astype(bool)

    for column in CATEGORY_COLUMNS:
        data[column] = data[column].astype("category")

    nulls = data.isna().sum()
    if nulls.any():
        raise ValueError(f"El dataset tiene nulos en campos requeridos: {nulls[nulls > 0].to_dict()}")
    if not np.isfinite(data[FLOAT_COLUMNS].to_numpy(dtype="float64")).all():
        raise ValueError("El dataset contiene valores numéricos infinitos o no finitos")
    if (data["tmax_c"] < data["tmin_c"]).any():
        raise ValueError("Se encontraron registros con tmax_c menor que tmin_c")
    hashes = data["bronce_sha256"].astype(str).str.lower()
    if not hashes.str.fullmatch(r"[0-9a-f]{64}").all():
        raise ValueError("bronce_sha256 debe ser una huella SHA-256 hexadecimal de 64 caracteres")
    references = data["bronce_ref"].astype(str).str.rsplit("|", n=2, expand=True)
    if (
        references.shape[1] != 3
        or not references[0].eq(data["archivo_origen"].astype(str)).all()
        or not references[1].eq(hashes.str[:12]).all()
        or not references[2].eq(data["bronce_fila"].astype(str)).all()
    ):
        raise ValueError("bronce_ref no coincide con archivo_origen, bronce_sha256 y bronce_fila")
    for variable in CLIMATE_COLUMNS:
        origin_column = f"origen_{variable}"
        origin = data[origin_column].astype(str)
        valid_origin = origin.str.fullmatch(
            r"[^|]+\|[0-9a-fA-F]{12}\|\d+|IMPUTADO:.+|SIN_DATO"
        )
        if not valid_origin.all():
            raise ValueError(f"{origin_column} contiene referencias de linaje inválidas")
        if not origin.str.startswith("IMPUTADO:").equals(data[f"{variable}_imputado"]):
            raise ValueError(f"{origin_column} no coincide con la bandera de imputación")
    if data["id_registro"].duplicated().any():
        raise ValueError("id_registro debe ser único")
    if data.duplicated(["fecha", "municipio"]).any():
        raise ValueError("Hay más de un registro por municipio y fecha")

    return data.sort_values(["fecha", "municipio"], kind="stable").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "data" / "oro" / "clima_oro_diario.csv",
        help="CSV oro diario producido por pipeline.run_pipeline",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "curated",
        help="directorio de destino",
    )
    args = parser.parse_args()
    source = args.source if args.source.is_absolute() else ROOT / args.source
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    if not source.is_file():
        raise FileNotFoundError(f"No existe el oro diario: {source}")

    data = curate_frame(pd.read_csv(source))
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "observatorio_climatico_agricola_curado.csv"
    parquet_path = output_dir / "observatorio_climatico_agricola_curado.parquet"
    data.to_csv(csv_path, index=False, encoding="utf-8", float_format="%.6f")
    data.to_parquet(parquet_path, index=False, engine="pyarrow", compression="snappy")

    print(f"Dataset curado: {len(data)} filas x {len(data.columns)} columnas")
    print(f"Fechas: {data['fecha'].min()} a {data['fecha'].max()}")
    print(f"Municipios: {', '.join(sorted(data['municipio'].astype(str).unique()))}")
    print(f"CSV: {csv_path}")
    print(f"Parquet: {parquet_path}")


if __name__ == "__main__":
    main()
