"""Fuente especializada geoespacial (OpenStreetMap): uso de suelo agrícola por municipio.

Dos partes:
1) Puro Python (sin GeoPandas): leer bronce, validar geometrías, mandar lo inválido a cuarentena.
2) GeoPandas: unión espacial parcelas <-> círculo de análisis, área agrícola en hectáreas.

Pregunta que responde: ¿cuánta superficie agrícola queda expuesta al clima de cada punto
de la malla de Open-Meteo (radio de OSM_RADIO_M)? Es un proxy de exposición, no un padrón
catastral: OpenStreetMap es mapeo voluntario y está incompleto (ver docs/etica-datos.md).
"""
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import config as cfg
from . import integracion as integ

PATRON_OSM = re.compile(r"osm_agricola_(?P<mun>[a-z_]+)_(?P<fecha>\d{8})\.json$")


# ---------------------------------------------------------------- bronce -> parcelas
def _fecha_archivo(ruta):
    return PATRON_OSM.search(ruta.name).group("fecha")


def cargar_osm_bronce(directorio=None):
    """Lee la captura MÁS RECIENTE de cada municipio.

    Devuelve (parcelas, centros): `parcelas` con una fila por polígono y su linaje
    (archivo|huella|posición); `centros` {municipio: (lat, lon, radio_m)}.
    """
    directorio = Path(directorio or cfg.DIR_BRONCE)
    mas_reciente = {}
    for ruta in sorted(directorio.glob("osm_agricola_*.json"), key=_fecha_archivo):
        mas_reciente[PATRON_OSM.search(ruta.name).group("mun")] = ruta
    if not mas_reciente:
        raise FileNotFoundError(f"No hay archivos osm_agricola_* en {directorio}")
    filas, centros = [], {}
    for mun, ruta in mas_reciente.items():
        contenido = ruta.read_bytes()
        sha = integ.huella_archivo(contenido)
        doc = json.loads(contenido.decode("utf-8"))
        centros[mun] = (doc["centro"]["lat"], doc["centro"]["lon"], doc.get("radio_m", cfg.OSM_RADIO_M))
        fecha = datetime.strptime(PATRON_OSM.search(ruta.name).group("fecha"), "%Y%m%d")
        filas += [{
            "municipio": mun, "osm_id": el["id"], "uso": el.get("tags", {}).get("landuse"),
            "cultivo": next((el["tags"][k] for k in ("crop", "trees", "produce") if k in el.get("tags", {})), None),
            "coords": [(p["lon"], p["lat"]) for p in el.get("geometry", [])],
            "archivo_origen": ruta.name, "bronce_sha256": sha,
            "bronce_ref": f"{ruta.name}|{sha[:12]}|{i}",
            "fecha_ingesta": fecha, "osm_timestamp": doc.get("osm3s", {}).get("timestamp_osm_base"),
        } for i, el in enumerate(doc["elements"])]
    columnas = ["municipio", "osm_id", "uso", "cultivo", "coords", "archivo_origen", "bronce_sha256",
                "bronce_ref", "fecha_ingesta", "osm_timestamp"]
    return pd.DataFrame(filas, columns=columnas), centros


# ------------------------------------------------------------------ validación
def _motivos(fila):
    motivos = []
    if fila.uso not in cfg.OSM_USOS_AGRICOLAS:
        motivos.append(f"uso: fuera de catálogo agrícola (valor={fila.uso})")
    c = fila.coords
    if len(c) < 4:
        motivos.append(f"geometría: menos de 4 vértices (valor={len(c)})")
    elif c[0] != c[-1]:
        motivos.append("geometría: polígono no cerrado (primer y último vértice distintos)")
    (lat_min, lat_max), (lon_min, lon_max) = cfg.LIMITES_COORD["lat"], cfg.LIMITES_COORD["lon"]
    if any(not (lon_min <= x <= lon_max and lat_min <= y <= lat_max) for x, y in c):
        motivos.append("coordenadas: vértice fuera del estado de Colima")
    return motivos


def validar_parcelas(parcelas):
    """Puerta de calidad geoespacial. Devuelve (válidas, cuarentena); nada se borra en silencio."""
    parcelas = parcelas.reset_index(drop=True)
    motivos = [_motivos(f) for f in parcelas.itertuples()]
    duplicado = parcelas.duplicated(["municipio", "osm_id"], keep="first")
    motivos = [m + (["unicidad: osm_id repetido en el municipio"] if d else [])
               for m, d in zip(motivos, duplicado, strict=True)]
    malo = pd.Series([bool(m) for m in motivos], dtype=bool)
    cuarentena = parcelas[malo].assign(
        motivo_rechazo=[" | ".join(m) for m in motivos if m],
        fecha_rechazo=datetime.now().isoformat(timespec="seconds"))
    return parcelas[~malo].reset_index(drop=True), cuarentena.reset_index(drop=True)


# ---------------------------------------------------------------- GeoPandas
def a_geodataframe(parcelas):
    """Polígonos válidos en WGS84 (EPSG:4326)."""
    import geopandas as gpd
    from shapely.geometry import Polygon

    gdf = gpd.GeoDataFrame(parcelas.drop(columns=["coords"]),
                           geometry=[Polygon(c) for c in parcelas["coords"]], crs="EPSG:4326")
    gdf["geometry"] = gdf.geometry.make_valid()
    return gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].reset_index(drop=True)


def resumen_agricola(gdf, centros, crs=None):
    """Unión espacial parcelas <-> círculo de cada municipio y área agrícola en hectáreas.

    - `sjoin` asigna cada parcela al círculo que realmente toca (no se confía en la etiqueta).
    - El área usa la UNIÓN de polígonos recortada al círculo: si dos polígonos de OSM se
      traslapan no se cuentan dos veces y el porcentaje nunca pasa de 100.
    """
    import geopandas as gpd
    from shapely.geometry import Point

    crs = crs or cfg.CRS_PROYECTADO
    proy = gdf.to_crs(crs)
    circulos = gpd.GeoDataFrame(
        {"mun_circulo": list(centros)},
        geometry=[gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(crs).iloc[0].buffer(radio)
                  for lat, lon, radio in centros.values()], crs=crs)
    unidas = gpd.sjoin(proy, circulos, how="inner", predicate="intersects")
    filas = []
    for fila in circulos.itertuples():
        mun, circulo = fila.mun_circulo, fila.geometry
        sub = unidas[unidas["mun_circulo"] == mun]
        area_circulo_ha = circulo.area / 10_000
        info = {"municipio": mun, "radio_agricola_km": centros[mun][2] / 1000, "n_parcelas": len(sub),
                "n_parcelas_con_cultivo": int(sub["cultivo"].notna().sum()), "area_agricola_ha": 0.0}
        if len(sub):
            info["area_agricola_ha"] = round(sub.geometry.union_all().intersection(circulo).area / 10_000, 2)
            for uso, g in sub.groupby("uso"):
                info[f"area_{uso}_ha"] = round(g.geometry.union_all().intersection(circulo).area / 10_000, 2)
            origen = sub.iloc[0]
            info.update(archivo_origen=origen["archivo_origen"], bronce_sha256=origen["bronce_sha256"],
                        fecha_ingesta=origen["fecha_ingesta"], osm_timestamp=origen["osm_timestamp"])
        info["pct_area_agricola"] = round(100 * info["area_agricola_ha"] / area_circulo_ha, 2)
        info["area_circulo_ha"] = round(area_circulo_ha, 2)
        filas.append(info)
    df = pd.DataFrame(filas)
    for uso in cfg.OSM_USOS_AGRICOLAS:  # el esquema es el mismo aunque un uso no aparezca
        col = f"area_{uso}_ha"
        df[col] = df[col].fillna(0.0) if col in df else 0.0
    return df


def procesar(dir_bronce=None, dir_plata=None, dir_oro=None, dir_cuarentena=None, log=print):
    """Bronce OSM -> validación -> unión espacial -> plata (GeoJSON) y oro (contexto por municipio)."""
    dir_plata, dir_oro = Path(dir_plata or cfg.DIR_PLATA), Path(dir_oro or cfg.DIR_ORO)
    dir_cuarentena = Path(dir_cuarentena or cfg.DIR_CUARENTENA)
    for d in (dir_plata, dir_oro, dir_cuarentena):
        d.mkdir(parents=True, exist_ok=True)

    parcelas, centros = cargar_osm_bronce(dir_bronce)
    validas, rechazadas = validar_parcelas(parcelas)
    if len(rechazadas):
        ruta = dir_cuarentena / f"cuarentena_osm_{datetime.now():%Y%m%d_%H%M%S}.csv"
        rechazadas.drop(columns=["coords"]).to_csv(ruta, index=False, encoding="utf-8")
    log(f"[osm] {len(parcelas)} polígonos · válidos {len(validas)} · cuarentena {len(rechazadas)}")

    gdf = a_geodataframe(validas)
    contexto = resumen_agricola(gdf, centros)
    (dir_plata / "osm_parcelas.geojson").write_text(gdf.to_json(), encoding="utf-8")
    contexto.to_csv(dir_oro / "oro_contexto_agricola.csv", index=False, encoding="utf-8")
    log("[osm] contexto agrícola: " + ", ".join(
        f"{r.municipio} {r.area_agricola_ha:,.0f} ha ({r.pct_area_agricola:.1f} %)" for r in contexto.itertuples()))
    return {"contexto": contexto, "parcelas": gdf, "centros": centros,
            "poligonos": len(parcelas), "cuarentena": len(rechazadas)}
