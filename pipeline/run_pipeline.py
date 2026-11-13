"""Ejecuta el flujo completo sin intervención manual:

    bronce -> integración -> PUERTA DE CALIDAD -> plata -> oro

Uso:  python -m pipeline.run_pipeline
"""
import json
from datetime import datetime

import pandas as pd

from . import config as cfg
from . import integracion as integ
from . import limpieza as lim
from . import oro
from . import puerta_calidad as puerta


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

    # 4) Oro: escalado, discretización, jerarquías y reducción
    params = lim.ajustar_escalado(plata)
    diario, mensual = oro.construir_oro(plata, params)
    diario.to_csv(dir_oro / "clima_oro_diario.csv", index=False, encoding="utf-8")
    mensual.to_csv(dir_oro / "clima_oro_mensual.csv", index=False, encoding="utf-8")
    (dir_oro / "params_escalado.json").write_text(json.dumps(params, indent=2), encoding="utf-8")
    oro.diccionario_df().to_csv(dir_oro / "diccionario_datos.csv", index=False, encoding="utf-8")
    log(f"[oro] diario={len(diario)} filas · mensual={len(mensual)} filas "
        f"(reducción {100 * (1 - len(mensual) / len(diario)):.1f}%)")

    reporte = {
        "ejecutado": datetime.now().isoformat(timespec="seconds"),
        "bronce_registros": int(len(crudo)),
        "duplicados_captura": int(len(duplicados)),
        "puerta": rep_puerta,
        "cuarentena_total": int(len(cuarentena)),
        "faltantes": diag.to_dict(orient="records"),
        "imputados": {v: int(plata[f"{v}_imputado"].sum()) for v in cfg.VARIABLES},
        "atipicos": {c: int(plata[c].sum()) for c in plata.columns if c.startswith("atipico_")},
        "plata_filas": int(len(plata)),
        "oro_diario_filas": int(len(diario)),
        "oro_mensual_filas": int(len(mensual)),
        "reduccion_pct": round(100 * (1 - len(mensual) / len(diario)), 2),
    }
    (dir_plata / "reporte_puerta_calidad.json").write_text(
        json.dumps(reporte, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {"plata": plata, "oro_diario": diario, "oro_mensual": mensual,
            "cuarentena": cuarentena, "reporte": reporte}


if __name__ == "__main__":
    ejecutar()
