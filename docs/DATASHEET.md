# DataSheet for Datasets

## Motivación

El dataset resume variables climáticas diarias y mensuales de tres municipios de Colima para análisis académico de riesgos
agrícolas. El conjunto diario se encuentra en `data/oro/clima_oro_diario.csv` y el mensual en
`data/oro/clima_oro_mensual.csv`.

## Composición

- Cobertura histórica: archivos diarios de bronce disponibles en el repositorio.
- Municipios: Colima, Manzanillo y Tecomán.
- Variables principales: temperatura máxima, temperatura mínima, precipitación y viento máximo.
- Última ejecución verificable: 3294 filas diarias y 111 filas mensuales.
- Linaje: 13,176 valores revisados y 0 fallos.

## Procedencia

- Fuente meteorológica: Open-Meteo Archive.
- Fuente geoespacial: implementación de OpenStreetMap vía Overpass, sin captura real incluida actualmente.
- Licencias: Open-Meteo CC BY 4.0; OpenStreetMap ODbL 1.0 donde se publique contenido derivado.

## Recolección y procesamiento

El pipeline sigue Bronce → Plata → Oro:

1. Lectura y normalización de archivos JSON de Open-Meteo.
2. Validación física y registro de defectos en cuarentena.
3. Integración por calendario, imputación declarada y marcado de atípicos.
4. Escalado, discretización, agregaciones mensuales y linaje por registro.

## Usos previstos y no previstos

Usos previstos:

- Investigación académica.
- Visualización climática.
- Evaluación de riesgo agrícola.
- Reproducibilidad de limpieza y linaje.

Usos no previstos:

- Previsión de desastres sin fuentes oficiales adicionales.
- Decisiones agrícolas individuales sin validación local.
- Representar el dataset como un censo de predios agrícolas.

## Distribución

Debe publicarse como dos recursos separables:

- Datos climáticos derivados bajo atribución CC BY 4.0.
- Datos o productos derivados sustancialmente de OSM bajo ODbL 1.0.

## Mantenimiento

- Ejecución reproducible: `python -m pipeline.run_pipeline`.
- Pruebas: `pytest tests/test_linaje.py tests/test_osm_offline.py tests/test_pipeline.py tests/test_open_meteo_offline.py -q`.
- Los datos derivados deben rechazarse si `reporte_linaje.json` contiene fallos.
