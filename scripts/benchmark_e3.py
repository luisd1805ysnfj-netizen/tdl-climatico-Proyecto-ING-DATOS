"""Reproduce y compara el pipeline base y el optimizado sobre el mismo bronce."""
import argparse
import csv
import io
import json
import os
import statistics
import subprocess
import sys
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASELINE_REVISION = "b96c6f878ec8b4ae2e460045b0fedcc8385277b4"
RUNNER = r'''
import hashlib
import json
import os
import sys
import tracemalloc
from pathlib import Path
from time import perf_counter

import pandas as pd

sys.path.insert(0, os.environ["E3_CODE_ROOT"])
from pipeline.run_pipeline import ejecutar

output = Path(os.environ["E3_OUTPUT"])
output.mkdir(parents=True, exist_ok=True)
tracemalloc.start()
start = perf_counter()
result = ejecutar(
    dir_bronce=Path(os.environ["E3_BRONZE"]),
    dir_plata=output / "plata",
    dir_oro=output / "oro",
    dir_cuarentena=output / "cuarentena",
    dir_tablero=output / "tablero",
    verbose=False,
)
elapsed = perf_counter() - start
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

def frame_digest(frame):
    digest = hashlib.sha256()
    digest.update("\x1f".join(map(str, frame.columns)).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(frame, index=False).to_numpy().tobytes())
    return digest.hexdigest()

report = result["reporte"]
critical = {"tmax_c", "tmin_c", "precip_mm", "viento_max_kmh"}
missing_before = sum(
    int(row["faltantes"])
    for row in report["faltantes"]
    if row["variable"] in critical
)
quality_rejected = int(report["puerta"]["registros_en_cuarentena"])
frames = {
    "plata": result["plata"],
    "oro_diario": result["oro_diario"],
    "oro_mensual": result["oro_mensual"],
}
result_data = {
    "elapsed_seconds": elapsed,
    "peak_tracemalloc_mib": peak / (1024 * 1024),
    "bronze_rows": int(report["bronce_registros"]),
    "duplicate_capture_rows": int(report["duplicados_captura"]),
    "schema_or_quality_rejected_rows": quality_rejected,
    "discarded_or_quarantined_rows": int(report["duplicados_captura"]) + quality_rejected,
    "critical_missing_before_imputation": missing_before,
    "critical_missing_after_imputation": int(
        result["plata"][["tmax_c", "tmin_c", "precip_mm", "viento_max_kmh"]].isna().sum().sum()
    ),
    "imputed_critical_values": sum(int(value) for value in report["imputados"].values()),
    "silver_rows": int(report["plata_filas"]),
    "gold_daily_rows": int(report["oro_diario_filas"]),
    "gold_monthly_rows": int(report["oro_mensual_filas"]),
    "lineage_values_checked": int(report["linaje"]["valores_revisados"]),
    "lineage_failures": int(report["linaje"]["fallos"]),
    "frame_sha256": {name: frame_digest(frame) for name, frame in frames.items()},
}
print(json.dumps(result_data, ensure_ascii=False))
'''


def _extract_baseline(revision, destination):
    archive = subprocess.run(
        ["git", "archive", "--format=tar", revision, "pipeline", "extractors"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    root = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as bundle:
        for member in bundle.getmembers():
            target = (root / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise RuntimeError(f"Ruta insegura en el baseline: {member.name}") from exc
            if member.issym() or member.islnk():
                raise RuntimeError(f"El baseline contiene un enlace no admitido: {member.name}")
            bundle.extract(member, path=root)


def _run_once(label, code_root, bronze, runs_dir):
    with tempfile.TemporaryDirectory(prefix=f"e3-{label}-", dir=runs_dir) as output_dir:
        env = os.environ.copy()
        env.update({
            "E3_CODE_ROOT": str(code_root),
            "E3_BRONZE": str(bronze),
            "E3_OUTPUT": output_dir,
        })
        completed = subprocess.run(
            [sys.executable, "-c", RUNNER],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"Falló el replay {label} (código {completed.returncode}).\n"
                f"stdout:\n{completed.stdout[-4000:]}\nstderr:\n{completed.stderr[-4000:]}"
            )
        try:
            return json.loads(completed.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"El replay {label} no devolvió JSON válido: {completed.stdout[-2000:]}"
            ) from exc


def _capture_log_summary(path):
    if not path.exists():
        return {"available": False, "path": path.relative_to(ROOT).as_posix()}
    with path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    failures = [row for row in rows if row.get("exito", "").strip().lower() == "false"]
    timeouts = [
        row for row in failures
        if "timeout" in (row.get("error", "") or "").lower()
        or "timed out" in (row.get("error", "") or "").lower()
    ]
    return {
        "available": True,
        "path": path.relative_to(ROOT).as_posix(),
        "attempts": len(rows),
        "successes": len(rows) - len(failures),
        "failed_attempts": len(failures),
        "http_429": sum(row.get("http_status") == "429" for row in failures),
        "timeouts": len(timeouts),
    }


def _summarize(label, samples):
    stable_keys = (
        "bronze_rows",
        "duplicate_capture_rows",
        "schema_or_quality_rejected_rows",
        "discarded_or_quarantined_rows",
        "critical_missing_before_imputation",
        "critical_missing_after_imputation",
        "imputed_critical_values",
        "silver_rows",
        "gold_daily_rows",
        "gold_monthly_rows",
        "lineage_values_checked",
        "lineage_failures",
        "frame_sha256",
    )
    for key in stable_keys:
        if any(sample[key] != samples[0][key] for sample in samples[1:]):
            raise RuntimeError(f"Resultados no deterministas en {label}: {key}")
    return {
        "label": label,
        "runs": len(samples),
        "median_elapsed_seconds": statistics.median(
            sample["elapsed_seconds"] for sample in samples
        ),
        "median_peak_tracemalloc_mib": statistics.median(
            sample["peak_tracemalloc_mib"] for sample in samples
        ),
        **{key: samples[0][key] for key in stable_keys},
    }


def _percent_reduction(before, after):
    return None if before == 0 else round((before - after) / before * 100, 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3, help="repeticiones por variante (default: 3)")
    parser.add_argument(
        "--baseline-revision",
        default=BASELINE_REVISION,
        help="commit que representa el pipeline antes de optimizar",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "E3" / "benchmark.json",
        help="ruta del reporte JSON",
    )
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs debe ser al menos 1")

    bronze = ROOT / "data" / "bronce"
    if not list(bronze.glob("clima_historico_*.json")):
        raise FileNotFoundError(f"No se encontraron capturas de bronce en {bronze}")

    with tempfile.TemporaryDirectory(prefix="e3-benchmark-") as temp:
        temp_root = Path(temp)
        baseline_root = temp_root / "baseline"
        baseline_root.mkdir()
        _extract_baseline(args.baseline_revision, baseline_root)
        baseline_samples = []
        optimized_samples = []
        for _ in range(args.runs):
            baseline_samples.append(_run_once("antes", baseline_root, bronze, temp_root))
            optimized_samples.append(_run_once("despues", ROOT, bronze, temp_root))

    before = _summarize("Antes", baseline_samples)
    after = _summarize("Después", optimized_samples)
    if before["frame_sha256"] != after["frame_sha256"]:
        raise RuntimeError(
            "El pipeline optimizado produjo datos distintos al baseline; "
            "no se generó un reporte de comparación."
        )

    time_reduction = _percent_reduction(
        before["median_elapsed_seconds"], after["median_elapsed_seconds"]
    )
    memory_reduction = _percent_reduction(
        before["median_peak_tracemalloc_mib"], after["median_peak_tracemalloc_mib"]
    )
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "baseline_revision": args.baseline_revision,
        "runtime": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
        },
        "methodology": {
            "runs_per_variant": args.runs,
            "execution_order": "interleaved baseline/optimized pairs",
            "time_metric": "median perf_counter seconds; pipeline replay and output writes",
            "memory_metric": "median tracemalloc peak in MiB; Python allocations only",
            "network": "offline replay of the same bronce files; no HTTP calls",
            "equivalence": "SHA-256 hashes of plata, oro diario and oro mensual must match",
        },
        "capture_log": _capture_log_summary(ROOT / "calidad" / "bitacora_captura.csv"),
        "before": before,
        "after": after,
        "comparison": {
            "elapsed_seconds_reduction_pct": time_reduction,
            "peak_python_memory_reduction_pct": memory_reduction,
            "discarded_or_quarantined_rows_delta": (
                after["discarded_or_quarantined_rows"]
                - before["discarded_or_quarantined_rows"]
            ),
            "schema_or_quality_rejections_delta": (
                after["schema_or_quality_rejected_rows"]
                - before["schema_or_quality_rejected_rows"]
            ),
            "critical_missing_delta": (
                after["critical_missing_before_imputation"]
                - before["critical_missing_before_imputation"]
            ),
            "lineage_failures_delta": after["lineage_failures"] - before["lineage_failures"],
            "output_data_identical": True,
        },
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Antes:   {before['median_elapsed_seconds']:.3f}s · "
          f"{before['median_peak_tracemalloc_mib']:.2f} MiB")
    print(f"Después: {after['median_elapsed_seconds']:.3f}s · "
          f"{after['median_peak_tracemalloc_mib']:.2f} MiB")
    print(f"Paridad de datos: {report['comparison']['output_data_identical']}")
    print(f"Reporte: {output}")


if __name__ == "__main__":
    main()
