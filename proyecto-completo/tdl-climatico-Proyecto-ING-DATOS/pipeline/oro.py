"""Capa oro: tablas listas para análisis, linaje verificable y diccionario de datos."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as cfg
from . import integracion as integ
from . import limpieza as lim

METODO_IMPUTACION = {
    "tmax_c": "interpolacion_temporal_o_climatologia",
    "tmin_c": "interpolacion_temporal_o_climatologia",
    "viento_max_kmh": "interpolacion_temporal_o_climatologia",
    "precip_mm": "knn",
}
# columna de la API de Open-Meteo de la que sale cada variable canónica
CAMPO_OPEN_METEO = {v: k for k, v in integ.RENOMBRE_OPEN_METEO.items()}

DICCIONARIO = [
    # (columna, tabla, tipo, unidad, descripcion)
    ("fecha", "diaria", "fecha", "AAAA-MM-DD", "Día calendario local (America/Mexico_City)."),
    ("municipio", "ambas", "texto", "", "Municipio normalizado: tecoman, colima, manzanillo."),
    ("fuente", "diaria", "texto", "", "Fuente principal del registro."),
    ("fuentes_usadas", "diaria", "texto", "", "Fuentes combinadas para el día (linaje), p. ej. 'open-meteo-archive'."),
    ("n_fuentes", "diaria", "entero", "", "Número de fuentes que reportaron ese día y municipio."),
    ("tmax_c", "diaria", "decimal", "°C", "Temperatura máxima diaria a 2 m."),
    ("tmin_c", "diaria", "decimal", "°C", "Temperatura mínima diaria a 2 m."),
    ("precip_mm", "diaria", "decimal", "mm", "Precipitación total del día."),
    ("viento_max_kmh", "diaria", "decimal", "km/h", "Velocidad máxima del viento a 10 m."),
    ("<variable>_imputado", "diaria", "booleano", "", "True si el valor se imputó (no es observación)."),
    ("dif_<variable>", "diaria", "decimal", "unidad de la variable", "Discrepancia absoluta entre fuentes cuando hay 2 o más."),
    ("fila_agregada", "diaria", "booleano", "", "True si el día no llegó en bronce y se creó como faltante."),
    ("lat_grid / lon_grid", "diaria", "decimal", "grados", "Coordenadas REALES de la celda de malla usada por la fuente."),
    ("elevacion_m", "diaria", "decimal", "m", "Elevación de la celda de malla."),
    ("archivo_origen", "diaria", "texto", "", "Archivo de bronce de la fuente principal del registro (linaje)."),
    ("fecha_captura", "diaria", "fecha", "", "FECHA DE INGESTA: día en que se capturó el archivo de origen a bronce."),
    ("id_registro", "diaria", "texto", "", "Identificador estable del registro: municipio|AAAA-MM-DD."),
    ("origen_<variable>", "diaria", "texto", "", "LINAJE por valor: 'archivo|huella12|fila' en bronce, o IMPUTADO:<método>, o SIN_DATO."),
    ("bronce_sha256 / bronce_fila / bronce_ref", "diaria", "texto", "", "Huella SHA-256 del archivo de bronce, posición del registro dentro de él y referencia compuesta."),
    ("area_agricola_ha", "diaria", "decimal", "ha", "Superficie agrícola (OSM) dentro del radio del punto de clima; atributo fijo por municipio."),
    ("pct_area_agricola", "diaria", "decimal", "%", "Porcentaje del círculo de análisis cubierto por uso agrícola (OSM)."),
    ("radio_agricola_km", "diaria", "decimal", "km", "Radio del círculo de análisis alrededor del punto de la malla de clima."),
    ("z_robusto_<variable>", "diaria", "decimal", "", "Puntaje z modificado de la anomalía (mediana/MAD)."),
    ("atipico_<variable>", "diaria", "booleano", "", "Marca de valor atípico por variable (se conserva el dato)."),
    ("atipico_multivariado", "diaria", "booleano", "", "Marcado por Isolation Forest (combinación rara de variables)."),
    ("atipico_cualquiera", "diaria", "booleano", "", "True si cualquier método lo marcó; revisar antes de concluir."),
    ("<variable>_m7 / precip_mm_acum7", "diaria", "decimal", "", "Suavizado de 7 días (ruido reducido) para visualización."),
    ("<variable>_minmax", "diaria", "decimal", "0 a 1", "Normalización min-max con parámetros en params_escalado.json."),
    ("<variable>_z", "diaria", "decimal", "desv. estándar", "Estandarización z-score con parámetros en params_escalado.json."),
    ("tmax_categoria", "diaria", "categoría", "", "fresco <28 · calido 28-32 · muy_calido 32-35 · extremo >=35 °C."),
    ("precip_categoria", "diaria", "categoría", "", "sin_lluvia · ligera (0-5) · moderada (5-20) · fuerte (20-50) · muy_fuerte (>50 mm)."),
    ("tmin_cuartil", "diaria", "categoría", "", "Cuartil de tmin (discretización por frecuencia igual)."),
    ("viento_rango", "diaria", "categoría", "", "Rango de viento (discretización por ancho igual, 4 rangos)."),
    ("dia_lluvioso", "diaria", "booleano", "", "True si precip_mm >= 1."),
    ("anio, trimestre, mes, mes_nombre, anio_mes", "diaria", "mixto", "", "Jerarquía temporal: día -> mes -> trimestre -> año."),
    ("temporada", "diaria", "texto", "", "lluvias (jun-oct) o secas (nov-may)."),
    ("zona", "diaria", "texto", "", "Jerarquía geográfica: municipio -> zona (Costa/Valle) -> estado."),
    ("estado", "diaria", "texto", "", "Colima."),
    ("n_dias", "mensual", "entero", "", "Días agregados en el mes."),
    ("tmax_media / tmax_max", "mensual", "decimal", "°C", "Media y máximo mensual de tmax."),
    ("tmin_media / tmin_min", "mensual", "decimal", "°C", "Media y mínimo mensual de tmin."),
    ("precip_total_mm", "mensual", "decimal", "mm", "Lluvia acumulada del mes."),
    ("dias_lluvia", "mensual", "entero", "días", "Días con precip_mm >= 1."),
    ("viento_medio / viento_max", "mensual", "decimal", "km/h", "Media y máximo mensual del viento máximo diario."),
    ("n_atipicos", "mensual", "entero", "días", "Días marcados como atípicos en el mes."),
    ("primer_dia / ultimo_dia", "mensual", "fecha", "", "LINAJE mensual: cada fila agrega los registros diarios (id_registro) de ese municipio entre estas fechas."),
    ("ultima_ingesta", "mensual", "fecha", "", "Fecha de captura más reciente entre los días agregados."),
    ("n_dias_imputados", "mensual", "entero", "días", "Días del mes con al menos una variable imputada (no observada)."),
]


def agregar_linaje(df):
    """Agrega `id_registro` y `origen_<variable>`: de dónde salió CADA valor.

    - 'archivo|huella12|fila' -> se puede abrir el archivo de bronce y comprobarlo.
    - 'IMPUTADO:<método>'      -> valor derivado (no observado); se declara, no se esconde.
    - 'SIN_DATO'               -> la fuente nunca midió esa variable.
    """
    df = df.copy()
    df["id_registro"] = df["municipio"] + "|" + df["fecha"].dt.strftime("%Y-%m-%d")
    for v in cfg.VARIABLES:
        origen = df[f"ref_{v}"].fillna("SIN_DATO")
        df[f"origen_{v}"] = np.where(df[f"{v}_imputado"], "IMPUTADO:" + METODO_IMPUTACION[v], origen)
    return df.drop(columns=[f"ref_{v}" for v in cfg.VARIABLES])


def construir_oro(plata, params_escalado, contexto=None):
    """De plata limpia a oro diario y oro mensual (con linaje y, si existe, contexto agrícola)."""
    diario = lim.aplicar_escalado(plata, params_escalado)
    diario = lim.discretizar(diario)
    diario = lim.agregar_jerarquias(diario)
    diario = agregar_linaje(diario)
    if contexto is not None and len(contexto):
        diario = diario.merge(contexto[["municipio", "area_agricola_ha", "pct_area_agricola",
                                        "radio_agricola_km"]], on="municipio", how="left")
    mensual = lim.reducir_mensual(diario)
    return diario, mensual


def _cargar_bronce_json(ruta):
    contenido = Path(ruta).read_bytes()
    return integ.huella_archivo(contenido), json.loads(contenido.decode("utf-8"))


def verificar_linaje(diario, dir_bronce=None):
    """PRUEBA de trazabilidad: cada valor de oro se rastrea hasta su archivo de bronce.

    Para cada valor no imputado: el archivo existe, su huella coincide con la registrada,
    y el valor y la fecha en esa posición del archivo son los mismos que están en oro.
    Devuelve un reporte; `fallos` vacío = todo el oro es rastreable.
    """
    dir_bronce = Path(dir_bronce or cfg.DIR_BRONCE)
    cache, fallos = {}, []
    conteo = {"trazables": 0, "imputados": 0, "sin_dato": 0}

    def cargar(archivo):
        if archivo not in cache:
            ruta = dir_bronce / archivo
            if not ruta.exists():
                cache[archivo] = None
            elif ruta.suffix == ".json":
                cache[archivo] = _cargar_bronce_json(ruta)
            else:
                cache[archivo] = (integ.huella_archivo(ruta.read_bytes()), None)
        return cache[archivo]

    for v in cfg.VARIABLES:
        for idr, fecha, valor, origen in zip(diario["id_registro"], diario["fecha"], diario[v],
                                             diario[f"origen_{v}"], strict=True):
            if origen.startswith("IMPUTADO"):
                conteo["imputados"] += 1
                continue
            if origen == "SIN_DATO":
                conteo["sin_dato"] += 1
                continue
            archivo, sha12, fila = origen.split("|")
            cargado = cargar(archivo)
            if cargado is None:
                fallos.append((idr, v, f"el archivo {archivo} no existe en bronce"))
                continue
            sha, datos = cargado
            if not sha.startswith(sha12):
                fallos.append((idr, v, f"la huella de {archivo} no coincide (archivo modificado)"))
                continue
            if datos is not None:  # JSON de Open-Meteo: se compara fecha y valor en esa posición
                diario_json = datos["daily"]
                i = int(fila)
                if diario_json["time"][i] != fecha.strftime("%Y-%m-%d"):
                    fallos.append((idr, v, f"la fecha en bronce es {diario_json['time'][i]}"))
                    continue
                if not math.isclose(diario_json[CAMPO_OPEN_METEO[v]][i], valor, rel_tol=1e-9, abs_tol=1e-9):
                    fallos.append((idr, v, "el valor en bronce es distinto al de oro"))
                    continue
            conteo["trazables"] += 1
    total = sum(conteo.values()) + len(fallos)
    return {"valores_revisados": total, **conteo, "fallos": len(fallos),
            "detalle_fallos": [list(f) for f in fallos[:50]],
            "pct_trazable_u_origen_declarado": round(100 * (total - len(fallos)) / max(total, 1), 3)}


def diccionario_df():
    return pd.DataFrame(DICCIONARIO, columns=["columna", "tabla", "tipo", "unidad", "descripcion"])


def diccionario_markdown():
    d = diccionario_df()
    filas = ["| Columna | Tabla | Tipo | Unidad | Descripción |", "|---|---|---|---|---|"]
    filas += [f"| `{r.columna}` | {r.tabla} | {r.tipo} | {r.unidad} | {r.descripcion} |"
              for r in d.itertuples()]
    return "\n".join(filas)
