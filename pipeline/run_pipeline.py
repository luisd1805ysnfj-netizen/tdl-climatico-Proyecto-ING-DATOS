"""Ejecuta el flujo completo sin intervención manual:

    bronce -> integración -> PUERTA DE CALIDAD -> plata -> oro

Uso:  python -m pipeline.run_pipeline
"""
import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import config as cfg
from . import integracion as integ
from . import limpieza as lim
from . import oro
from . import puerta_calidad as puerta


def _contexto_agricola(dir_bronce, dir_plata, dir_oro, dir_cuarentena, log):
    """Fuente especializada (OpenStreetMap): se integra si hay capturas OSM en bronce."""
    carpeta = Path(dir_bronce or cfg.DIR_BRONCE)
    if not list(carpeta.glob("osm_agricola_*.json")):
        log("[osm] sin archivos osm_agricola_* en bronce: capa agrícola omitida")
        return None
    if importlib.util.find_spec("geopandas") is None:
        log("[osm] ADVERTENCIA: geopandas no está instalado; capa agrícola omitida (pip install -r requirements.txt)")
        return None
    from . import geoespacial

    res = geoespacial.procesar(dir_bronce, dir_plata, dir_oro, dir_cuarentena, log=log)
    log("[osm] contexto geoespacial disponible para React")
    return res

def ejecutar(dir_bronce=None, dir_plata=None, dir_oro=None, dir_cuarentena=None, verbose=True):
    dir_plata = dir_plata or cfg.DIR_PLATA
    dir_oro = dir_oro or cfg.DIR_ORO
    dir_cuarentena = dir_cuarentena or cfg.DIR_CUARENTENA
    for d in (dir_plata, dir_oro, dir_cuarentena):
        d.mkdir(parents=True, exist_ok=True)

    def log(msg):
        if verbose:
            print(msg)

    # 1) Bronce + integración (esquemas, unidades, nombres, duplicados)
    crudo = integ.cargar_bronce(dir_bronce)
    integrado, duplicados = integ.integrar(crudo)
    log(f"[bronce] {len(crudo)} registros leídos · {len(duplicados)} duplicados de captura")

    # 2) Puerta de calidad 1: lo inválido va a cuarentena con su motivo
    aprobados, rechazados, rep_puerta = puerta.aplicar_puerta(integrado)
    cuarentena = pd.concat([rechazados, duplicados], ignore_index=True)
    ruta_cuarentena = puerta.guardar_cuarentena(cuarentena, dir_cuarentena)
    log(f"[puerta] aprobados={rep_puerta['registros_aprobados']} "
        f"cuarentena={len(cuarentena)} ({ruta_cuarentena or 'sin archivo: nada que rechazar'})")

    # 3) Plata: consolidación de fuentes + limpieza
    consolidado = integ.consolidar_fuentes(aprobados)
    plata = lim.completar_calendario(consolidado)
    diag = lim.diagnosticar_faltantes(plata)
    plata = lim.imputar(plata)
    plata = lim.marcar_atipicos(plata)
    plata = lim.suavizar_ruido(plata)
    plata.to_csv(dir_plata / "clima_plata.csv", index=False, encoding="utf-8")
    log(f"[plata] {len(plata)} filas · {int(plata['atipico_cualquiera'].sum())} marcadas como atípicas")

    # 4) Fuente especializada geoespacial (OpenStreetMap), si hay capturas en bronce
    osm = _contexto_agricola(dir_bronce, dir_plata, dir_oro, dir_cuarentena, log)

    # 5) Oro: escalado, discretización, jerarquías, linaje y reducción
    params = lim.ajustar_escalado(plata)
    diario, mensual = oro.construir_oro(plata, params, osm["contexto"] if osm else None)
    diario.to_csv(dir_oro / "clima_oro_diario.csv", index=False, encoding="utf-8")
    mensual.to_csv(dir_oro / "clima_oro_mensual.csv", index=False, encoding="utf-8")
    try:
        diario.to_parquet(dir_oro / "clima_oro_diario.parquet", index=False)
        mensual.to_parquet(dir_oro / "clima_oro_mensual.parquet", index=False)
        log("[oro] Parquet diario y mensual escritos")
    except ImportError:
        log("[oro] ADVERTENCIA: pyarrow no está instalado; no se generaron archivos Parquet")
    (dir_oro / "params_escalado.json").write_text(json.dumps(params, indent=2), encoding="utf-8")
    oro.diccionario_df().to_csv(dir_oro / "diccionario_datos.csv", index=False, encoding="utf-8")
    log(f"[oro] diario={len(diario)} filas · mensual={len(mensual)} filas "
        f"(reducción {100 * (1 - len(mensual) / len(diario)):.1f}%)")

    rep_linaje = oro.verificar_linaje(diario, dir_bronce)
    (dir_oro / "reporte_linaje.json").write_text(
        json.dumps(rep_linaje, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"[linaje] {rep_linaje['valores_revisados']} valores revisados · trazables {rep_linaje['trazables']} · "
        f"imputados {rep_linaje['imputados']} · fallos {rep_linaje['fallos']}")
    if rep_linaje["fallos"]:
        raise RuntimeError(f"Linaje roto: {rep_linaje['detalle_fallos'][:3]}")

    reporte = {
        "ejecutado": datetime.now().isoformat(timespec="seconds"),
        "bronce_registros": len(crudo),
        "duplicados_captura": len(duplicados),
        "puerta": rep_puerta,
        "cuarentena_total": len(cuarentena),
        "faltantes": diag.to_dict(orient="records"),
        "imputados": {v: int(plata[f"{v}_imputado"].sum()) for v in cfg.VARIABLES},
        "atipicos": {c: int(plata[c].sum()) for c in plata.columns if c.startswith("atipico_")},
        "plata_filas": len(plata),
        "oro_diario_filas": len(diario),
        "oro_mensual_filas": len(mensual),
        "reduccion_pct": round(100 * (1 - len(mensual) / len(diario)), 2),
        "linaje": {k: v for k, v in rep_linaje.items() if k != "detalle_fallos"},
        "osm": ({"poligonos": osm["poligonos"], "cuarentena": osm["cuarentena"]} if osm else None),
    }
    (dir_plata / "reporte_puerta_calidad.json").write_text(
        json.dumps(reporte, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {"plata": plata, "oro_diario": diario, "oro_mensual": mensual,
            "cuarentena": cuarentena, "reporte": reporte}


if __name__ == "__main__":
    ejecutar()
