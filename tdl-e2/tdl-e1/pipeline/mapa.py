"""Mapa cartográfico (Folium) del uso agrícola de OpenStreetMap con el clima de cada punto."""
import json
from pathlib import Path

ATRIBUCION = ("Uso de suelo: © contribuyentes de OpenStreetMap (licencia ODbL). "
              "Clima: Open-Meteo (CC BY 4.0). Observatorio TDL.")
COLORES = {"tecoman": "#1b9e77", "colima": "#d95f02", "manzanillo": "#7570b3"}


def construir_mapa(gdf, contexto, centros, ruta_html, tolerancia_grados=0.00005):
    """Escribe un HTML autocontenido con círculos de análisis, parcelas y cifras por municipio."""
    import folium

    mapa = folium.Map(location=[19.1, -103.9], zoom_start=9, tiles="OpenStreetMap", control_scale=True)
    simple = gdf[["municipio", "uso", "cultivo", "geometry"]].copy()
    simple["geometry"] = simple.geometry.simplify(tolerancia_grados, preserve_topology=True)
    simple["cultivo"] = simple["cultivo"].fillna("sin dato")
    capa = folium.FeatureGroup(name="Uso agrícola (OSM)", show=True)
    folium.GeoJson(
        json.loads(simple.to_json()),
        style_function=lambda f: {"color": COLORES.get(f["properties"]["municipio"], "#555"),
                                  "weight": 0.6, "fillOpacity": 0.45},
        tooltip=folium.GeoJsonTooltip(fields=["uso", "cultivo"], aliases=["Uso", "Cultivo"]),
    ).add_to(capa)
    capa.add_to(mapa)

    por_mun = contexto.set_index("municipio")
    for mun, (lat, lon, radio) in centros.items():
        r = por_mun.loc[mun]
        folium.Circle((lat, lon), radius=radio, color=COLORES.get(mun, "#555"), weight=2,
                      fill=False, dash_array="6").add_to(mapa)
        folium.Marker(
            (lat, lon), tooltip=mun.capitalize(),
            popup=folium.Popup(f"<b>{mun.capitalize()}</b><br>Radio: {radio / 1000:.0f} km<br>"
                               f"Superficie agrícola: {r.area_agricola_ha:,.0f} ha<br>"
                               f"Cobertura del círculo: {r.pct_area_agricola:.1f} %<br>"
                               f"Parcelas con cultivo declarado: {int(r.n_parcelas_con_cultivo)} de {int(r.n_parcelas)}",
                               max_width=280)).add_to(mapa)
    folium.LayerControl().add_to(mapa)
    mapa.get_root().html.add_child(folium.Element(
        f'<div style="position:fixed;bottom:8px;left:8px;z-index:9999;background:white;padding:4px 8px;'
        f'font-size:11px;border-radius:4px;max-width:70%">{ATRIBUCION}</div>'))
    ruta = Path(ruta_html)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    mapa.save(str(ruta))
    return ruta
