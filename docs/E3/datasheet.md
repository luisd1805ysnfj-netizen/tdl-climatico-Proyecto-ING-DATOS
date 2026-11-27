# Datasheet for Datasets · E3

## Identificación

- **Dataset:** Observatorio Climático y Agrícola curado (capa oro diaria).
- **Versión:** candidata para E3; el tag Git `e3` queda pendiente de la publicación
  final.
- **Archivos:** [`CSV`](../../data/curated/observatorio_climatico_agricola_curado.csv) ·
  [`Parquet`](../../data/curated/observatorio_climatico_agricola_curado.parquet).
- **Licencia:** [CC BY 4.0](../../data/curated/LICENSE-DATA.md).
- **Fecha de generación verificada:** 2026-11-26, hora local del equipo.

## 1. Motivación

El dataset se creó como evidencia reproducible del proyecto académico
Observatorio Climático y Agrícola. Reúne observaciones diarias de clima para
Colima, Manzanillo y Tecomán, con variables y referencias de linaje adecuadas
para análisis exploratorio de tendencias y contexto agrícola. Fue elaborado por
el equipo del proyecto (Luis / Luis David, según la documentación del
repositorio); no hay un registro de contribuciones individuales por cada fila o
transformación.

No es una estación meteorológica, una predicción del tiempo ni un conjunto de
precios agrícolas.

## 2. Composición

- **Filas y columnas:** 3,294 × 29.
- **Periodo de las observaciones:** 2023-11-23 a 2026-11-24.
- **Ingestas de bronce representadas:** 2026-11-09 a 2026-11-26.
- **Cobertura:** estado de Colima; 1,098 días por municipio: Colima, Manzanillo
  y Tecomán.
- **Extensión de la malla meteorológica:** latitud 18.875219–19.226713°,
  longitud −104.304047 a −103.709198°; elevación 37–495 m.
- **Fuente observada en esta versión:** `open-meteo-archive` (una fuente por
  registro). No hay observaciones del SMN ni capturas OSM en este dataset.
- **Nulos:** 0 en las 29 columnas.
- **Filas agregadas al calendario:** 0. **Valores climáticos imputados:** 0.
- **Atípicos marcados y conservados:** 197 filas.
- **Linaje:** 13,176 valores climáticos revisados, 13,176 trazables y 0 fallos.

### Diccionario de datos

Los rangos numéricos son los observados en esta versión. Los campos `fecha` y
`fecha_captura` se serializan como `AAAA-MM-DD`. Parquet conserva tipos compactos
(`float32`, `uint8`, `uint16` y categorías); CSV representa las variables
decimales con seis posiciones.

| Columna | Tipo publicado | Unidad | Descripción y dominio observado |
|---|---|---|---|
| `fecha` | texto ISO-8601 | día | Fecha calendario local; 2023-11-23 a 2026-11-24. |
| `municipio` | categoría / texto | — | Municipio normalizado: `colima`, `manzanillo`, `tecoman` (1,098 filas cada uno). |
| `estado` | categoría / texto | — | Entidad federativa; `Colima` en todas las filas. |
| `lat_grid` | `float32` | grados | Latitud de la celda real de la malla de Open-Meteo; 18.875219–19.226713. |
| `lon_grid` | `float32` | grados | Longitud de la celda real de la malla; −104.304047 a −103.709198. |
| `elevacion_m` | `float32` | m | Elevación informada para la celda; 37–495. |
| `tmax_c` | `float32` | °C | Temperatura máxima diaria a 2 m; 22.0–39.0. |
| `tmin_c` | `float32` | °C | Temperatura mínima diaria a 2 m; 13.0–28.4. |
| `precip_mm` | `float32` | mm | Precipitación diaria; 0–168.9. |
| `viento_max_kmh` | `float32` | km/h | Velocidad máxima diaria del viento a 10 m; 5.3–43.8. |
| `fuente` | categoría / texto | — | Fuente principal; `open-meteo-archive`. |
| `fuentes_usadas` | categoría / texto | — | Fuentes combinadas para el día; `open-meteo-archive`. |
| `n_fuentes` | `uint8` | fuentes | Número de fuentes que reportaron el día; 1 en todos los registros. |
| `fecha_captura` | texto ISO-8601 | día | Fecha de ingesta del archivo de bronce; 2026-11-09 a 2026-11-26. |
| `fila_agregada` | booleano | — | Indica si el día se creó para completar el calendario; `false` en 3,294 filas. |
| `tmax_c_imputado` | booleano | — | Indica imputación de temperatura máxima; `false` en todas las filas. |
| `tmin_c_imputado` | booleano | — | Indica imputación de temperatura mínima; `false` en todas las filas. |
| `precip_mm_imputado` | booleano | — | Indica imputación de precipitación; `false` en todas las filas. |
| `viento_max_kmh_imputado` | booleano | — | Indica imputación de viento; `false` en todas las filas. |
| `atipico_cualquiera` | booleano | — | Marca compuesta de anomalías; 197 `true`, 3,097 `false`. Las filas se conservan. |
| `id_registro` | texto | — | Identificador único estable `municipio|AAAA-MM-DD`; 3,294 valores únicos. |
| `archivo_origen` | texto | — | Archivo JSON de bronce principal; 39 archivos distintos en esta versión. |
| `bronce_sha256` | texto hexadecimal | — | Huella SHA-256 completa del archivo de bronce (64 caracteres). |
| `bronce_fila` | `uint16` | índice | Posición de la fila en el archivo de bronce; 0–1,077. |
| `bronce_ref` | texto | — | Referencia compuesta `archivo|sha256-12|fila`. |
| `origen_tmax_c` | texto | — | Linaje del valor de temperatura máxima: archivo, huella corta y fila; o `IMPUTADO:<método>` si aplica. |
| `origen_tmin_c` | texto | — | Linaje del valor de temperatura mínima; mismo formato que `origen_tmax_c`. |
| `origen_precip_mm` | texto | — | Linaje de la precipitación; mismo formato que `origen_tmax_c`. |
| `origen_viento_max_kmh` | texto | — | Linaje del viento; mismo formato que `origen_tmax_c`. |

## 3. Proceso de recolección

La fuente es la [API histórica de Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api),
consultada para los municipios del proyecto. El endpoint devuelve series diarias
asociadas a una celda de malla; por ello las coordenadas publicadas son las
coordenadas de malla devueltas por la API, no una estación en el predio. Las
capturas se guardan en JSON de bronce antes de procesarse.

La licencia CC BY 4.0 cubre las contribuciones y transformaciones del proyecto;
no reemplaza los términos del proveedor ni autoriza uso comercial de datos
obtenidos mediante la API gratuita de Open-Meteo, que es de uso no comercial.

El workflow [`.github/workflows/captura.yml`](../../.github/workflows/captura.yml)
programa captura diaria a las 14:00 UTC (08:00 hora de Colima). En la bitácora
incluida para esta corrida constan 45 intentos: 42 exitosos, 3 fallidos con HTTP
429 y 0 timeouts. Los errores HTTP son eventos de captura; el benchmark del
pipeline no hace solicitudes de red y no los presenta como fallos del replay.

**Limitaciones de origen:** los valores son datos de archivo/modelo en una
malla, no mediciones verificadas en campo. La cobertura se limita a tres
municipios y a las fechas disponibles en los archivos. No se incluyen aquí
parcelas agrícolas de OSM, datos de mercado ni información personal.

## 4. Preprocesamiento, limpieza y etiquetado

El flujo reproducible es Bronce → Plata → Oro:

1. Se valida el patrón de nombre, esquema, unidades, fechas y tipos de cada
   captura; las unidades admitidas se convierten a °C, mm y km/h.
2. Se normalizan nombres de municipio y fechas, y se deduplican capturas de la
   misma fuente. Los duplicados no se borran sin rastro: pasan a cuarentena.
3. La puerta de calidad valida reglas físicas y de esquema. Los registros
   rechazados se separan con su motivo.
4. Se completa el calendario, se diagnostican faltantes y se marcan valores
   atípicos. Las imputaciones se declaran con banderas; las anomalías se
   conservan. En esta versión no hubo días agregados ni imputaciones.
5. Se construye el oro diario y mensual y se comprueba cada valor climático
   contra su archivo de bronce mediante la huella, la fila y el valor original.
6. El script de curación conserva columnas climáticas, banderas y referencias de
   linaje; ordena por fecha y municipio, normaliza fechas ISO, valida unicidad y
   nulos, y reduce tipos para Parquet.

En la última ejecución se leyeron 3,495 filas de bronce: 201 capturas repetidas
fueron a cuarentena; 3,294 pasaron la puerta y 0 fueron rechazadas por calidad.
Las diferencias entre fuentes se mantienen como diagnóstico en las capas
intermedias, no como valores nulos del dataset curado.

## 5. Distribución y mantenimiento

- **CSV:** [`observatorio_climatico_agricola_curado.csv`](../../data/curated/observatorio_climatico_agricola_curado.csv).
- **Parquet:** [`observatorio_climatico_agricola_curado.parquet`](../../data/curated/observatorio_climatico_agricola_curado.parquet).
- **Licencia:** [CC BY 4.0 y atribución](../../data/curated/LICENSE-DATA.md).
- **Frecuencia prevista:** regeneración después de una captura diaria exitosa;
  el pipeline se ejecuta con el bronce guardado y después `scripts/curate_e3.py`
  publica ambos formatos.
- **Reproducción:** `python -m pipeline.run_pipeline` y luego
  `python scripts/curate_e3.py`.
- **Integridad:** revisar `data/oro/reporte_linaje.json`; la ejecución falla si
  hay referencias de linaje rotas.

La cifra de 0 faltantes corresponde a esta versión y no garantiza que futuras
capturas estén completas. Si cambia el esquema, el script de curación falla de
forma explícita hasta que se actualice el diccionario y la validación.

## 6. Usos recomendados y no recomendados

**Recomendados:** análisis exploratorio de tendencias históricas locales,
visualización, prácticas de ingeniería de datos, enseñanza de calidad y linaje,
y contexto climático agregado para estudios agrícolas preliminares.

**No recomendados:** alertas de protección civil, pronóstico hiperlocal,
decisiones de riego o aplicación de insumos sin sensores/validación local,
estimación de rendimiento o pérdidas, ni inferencias para otros municipios o
países. Los atípicos son señales para revisión, no errores confirmados.

## 7. Consideraciones éticas

La colección meteorológica no contiene identificadores personales. La
interpretación debe considerar la resolución de malla, el sesgo geográfico de
solo tres municipios y las limitaciones de los datos modelados. La licencia y
atribución aplicables se describen en
[`LICENSE-DATA.md`](../../data/curated/LICENSE-DATA.md).
