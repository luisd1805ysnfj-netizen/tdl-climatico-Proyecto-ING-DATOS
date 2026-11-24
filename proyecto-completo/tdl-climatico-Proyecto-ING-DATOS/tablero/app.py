"""Tablero público del Observatorio de Inteligencia Climática de Colima (Streamlit).

Lee SOLO los archivos que produce el pipeline (data/oro, data/plata, tablero/mapa_agricola.html);
no consulta ninguna API, así que siempre muestra datos que ya pasaron la puerta de calidad.

Local:  streamlit run tablero/app.py
Nube:   share.streamlit.io -> repositorio -> main file: tablero/app.py
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

RAIZ = Path(__file__).resolve().parents[1]
ORO, PLATA, TABLERO = RAIZ / "data" / "oro", RAIZ / "data" / "plata", RAIZ / "tablero"
NOMBRES = {"tecoman": "Tecomán", "colima": "Colima", "manzanillo": "Manzanillo"}
VARIABLES = {"tmax_media": "Temperatura máxima media (°C)", "tmin_media": "Temperatura mínima media (°C)",
             "precip_total_mm": "Lluvia total del mes (mm)", "viento_max": "Viento máximo del mes (km/h)"}

st.set_page_config(page_title="Observatorio Climático · Colima", page_icon="🌦️", layout="wide")


@st.cache_data
def leer_csv(ruta):
    return pd.read_csv(ruta) if Path(ruta).exists() else None


@st.cache_data
def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8")) if Path(ruta).exists() else None


mensual = leer_csv(ORO / "clima_oro_mensual.csv")
contexto = leer_csv(ORO / "oro_contexto_agricola.csv")
puerta = leer_json(PLATA / "reporte_puerta_calidad.json")
linaje = leer_json(ORO / "reporte_linaje.json")

st.title("🌦️ Observatorio de Inteligencia Climática · Colima")
st.caption("Clima diario de Colima, Tecomán y Manzanillo, con el uso agrícola del territorio "
           "y la evidencia de calidad de los datos. Proyecto integrador TRUSTED DATA LAB.")

if mensual is None:
    st.error("Todavía no hay datos en data/oro. Ejecuten: python -m pipeline.run_pipeline")
    st.stop()

tab_clima, tab_mapa, tab_calidad, tab_fuentes = st.tabs(
    ["📈 Clima", "🗺️ Mapa agrícola", "✅ Calidad y linaje", "📚 Fuentes y licencias"])

with tab_clima:
    c1, c2 = st.columns([1, 2])
    variable = c1.selectbox("Variable", list(VARIABLES), format_func=VARIABLES.get)
    municipios = c2.multiselect("Municipios", list(NOMBRES), default=list(NOMBRES), format_func=NOMBRES.get)
    datos = mensual[mensual["municipio"].isin(municipios)]
    if datos.empty:
        st.info("Elijan al menos un municipio.")
    else:
        tabla = datos.pivot_table(index="anio_mes", columns="municipio", values=variable)
        st.line_chart(tabla.rename(columns=NOMBRES))
        st.caption(f"{VARIABLES[variable]} · {len(datos)} meses · valores agregados desde la capa oro diaria.")

with tab_mapa:
    html = TABLERO / "mapa_agricola.html"
    if contexto is None or not html.exists():
        st.info("La capa agrícola aún no se ha generado. Capturen OpenStreetMap "
                "(python -m extractors.osm_overpass) y vuelvan a correr el pipeline.")
    else:
        st.markdown("**¿Cuánta superficie agrícola queda alrededor de cada punto de clima?** "
                    "Círculos de análisis sobre la malla de Open-Meteo; polígonos de uso agrícola de OpenStreetMap.")
        components.html(html.read_text(encoding="utf-8"), height=620, scrolling=True)
        columnas = ["municipio", "radio_agricola_km", "area_agricola_ha", "pct_area_agricola",
                    "n_parcelas", "n_parcelas_con_cultivo", "fecha_ingesta"]
        st.dataframe(contexto[[c for c in columnas if c in contexto]], hide_index=True)
        st.warning("Lectura con cuidado: OpenStreetMap es mapeo voluntario y está incompleto; la cifra es un "
                   "mínimo, no un censo agrícola. En Manzanillo el círculo incluye mar, por lo que el porcentaje "
                   "subestima la cobertura sobre tierra.")

with tab_calidad:
    st.subheader("Puerta de calidad (bronce → plata)")
    if puerta:
        p = puerta["puerta"]
        a, b, c = st.columns(3)
        a.metric("Registros recibidos", f"{p['registros_recibidos']:,}")
        b.metric("Aprobados", f"{p['registros_aprobados']:,}")
        c.metric("En cuarentena", f"{p['registros_en_cuarentena']:,}")
        st.caption("Lo que no cumple las reglas no se borra: va a data/cuarentena con su motivo.")
    st.subheader("Linaje: ¿de dónde sale cada valor?")
    if linaje:
        a, b, c, d = st.columns(4)
        a.metric("Valores revisados", f"{linaje['valores_revisados']:,}")
        b.metric("Rastreables a bronce", f"{linaje['trazables']:,}")
        c.metric("Imputados (declarados)", f"{linaje['imputados']:,}")
        d.metric("Fallos de trazabilidad", f"{linaje['fallos']:,}")
        st.caption("Cada valor de la capa oro apunta a su archivo de bronce, su huella SHA-256 y su posición; "
                   "la prueba abre el archivo y compara.")

with tab_fuentes:
    st.markdown("""
**Clima:** Weather data by [Open-Meteo.com](https://open-meteo.com/) · licencia
[CC BY 4.0](https://open-meteo.com/en/licence) · uso no comercial.

**Uso de suelo agrícola:** © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors ·
Open Database License (ODbL).

**Privacidad:** el observatorio no captura datos personales. Las etiquetas de OpenStreetMap que pueden
identificar personas (nombres, dueños, teléfonos, direcciones) se eliminan antes de guardar nada.

Detalle completo en `docs/etica-datos.md` del repositorio.
""")
