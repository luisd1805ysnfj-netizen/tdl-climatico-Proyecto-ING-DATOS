import csv
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BITACORA = RAIZ / "calidad" / "bitacora_captura.csv"
SALIDA_JSON = RAIZ / "calidad" / "psp_metricas.json"
SALIDA_CSV = RAIZ / "calidad" / "psp_metricas.csv"


def main():
    df = pd.read_csv(BITACORA, parse_dates=["timestamp_utc"])
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    corridas = df.sort_values("timestamp_utc").groupby("timestamp_utc", sort=True)

    intentos = len(df)
    exitos = int(df["exito"].sum())
    fallos = intentos - exitos
    disponibilidad = round(100 * exitos / intentos, 2) if intentos else None

    fallas = df.loc[~df["exito"]].copy()
    mttr_s = float(fallas["duracion_s"].dropna().mean()) if len(fallas) else 0.0

    fail_times = sorted(df.loc[~df["exito"], "timestamp_utc"].unique())
    prior_uptime = []
    for index, fail in enumerate(fail_times):
        before = df.loc[df["timestamp_utc"] < fail, "timestamp_utc"].max()
        if pd.notna(before):
            prior_uptime.append((fail - before).total_seconds() / 3600)
    mtbf_h = float(pd.Series(prior_uptime).mean()) if prior_uptime else None

    window_start = df["timestamp_utc"].min()
    window_end = df["timestamp_utc"].max()
    registro = {
        "periodo_inicio": window_start.isoformat(),
        "periodo_fin": window_end.isoformat(),
        "registros_de_intentos": intentos,
        "corridas_por_timestamp": int(corridas.ngroups),
        "exitos": exitos,
        "fallos": fallos,
        "disponibilidad_pct": disponibilidad,
        "objetivo_disponibilidad_pct": 95.0,
        "objetivo_alcanzado": bool(disponibilidad is not None and disponibilidad >= 95.0),
        "mttr_segundos": round(mttr_s, 2),
        "mtbf_horas": None if mtbf_h is None else round(mtbf_h, 2),
        "metodologia": (
            "Disponibilidad = éxitos / registros de intento. "
            "MTTR = duración media registrada en fallos. "
            "MTBF = intervalo medio aproximado entre timestamps distintos con fallos "
            "y el último intento registrado antes de cada fallo."
        ),
        "limitacion": (
            "No equivale a SLA de 14 días ni mide Uptime por servicios observados "
            "cada minuto; la bitácora contiene intentos por municipio y no estado "
            "continuo de todos los componentes."
        ),
    }
    SALIDA_JSON.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
    with SALIDA_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(registro))
        writer.writeheader()
        writer.writerow(registro)
    print(SALIDA_JSON)
    print(SALIDA_CSV)


if __name__ == "__main__":
    main()
