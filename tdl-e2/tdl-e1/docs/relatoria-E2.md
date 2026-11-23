# Relatoría E2 · Observatorio de Inteligencia Climática (Colima, Tecomán y Manzanillo)

Equipo: [COMPLETAR: integrantes] · Periodo: 17 al 23 de noviembre de 2026

> **Borrador.** Lo que sale del código y de los datos ya está verificado. Los `[COMPLETAR]` (quién hizo qué, horas, números de
> defecto, cifras de OpenStreetMap, resultados de la captura) deben salir de su registro de tiempo, su registro de defectos y de
> correr el pipeline. La rúbrica pide específica, honesta y verificable: no dejen ningún corchete en la versión final, y corrijan
> lo que no coincida con lo que realmente pasó en su equipo.

## 1. Qué nos propusimos
Integrar una fuente especializada geoespacial al observatorio, garantizar que **cada valor de la capa oro** se pueda rastrear
hasta su archivo de bronce y su fecha de ingesta, y documentar la ética y legalidad de las dos fuentes. Metas medibles:
(a) un archivo `osm_agricola_*` por municipio que pase la puerta de calidad; (b) 100 % de los valores de oro con origen verificable
o declarado como imputado; (c) cero etiquetas personales en bronce.

## 2. Qué hicimos
| Fecha | Qué | Quién | Horas |
|---|---|---|---|
| 17-nov | Elección de la fuente (OpenStreetMap sobre DENUE) y diseño del linaje | [COMPLETAR] | [COMPLETAR] |
| 17-nov | Huella SHA-256, posición y referencia por registro; `verificar_linaje` y 9 pruebas de trazabilidad | [COMPLETAR] | [COMPLETAR] |
| 17-nov | Extractor de Overpass con lista blanca de etiquetas, reintentos y espejo; pruebas offline | [COMPLETAR] | [COMPLETAR] |
| [COMPLETAR] | Primera captura real de OSM; revisión de `robots.txt` y términos; `docs/etica-datos.md` | [COMPLETAR] | [COMPLETAR] |
| [COMPLETAR] | Unión espacial en GeoPandas, mapa y tablero en Streamlit | [COMPLETAR] | [COMPLETAR] |
| [COMPLETAR] | Revisión cruzada (Quality Lead) y etiqueta `e2` | [COMPLETAR] | [COMPLETAR] |

## 3. Qué decidimos y por qué
- **OpenStreetMap sobre DENUE.** DENUE es más oficial, pero exige registrar un token y protegerlo como secreto; OSM no pide registro y
  permite consultar polígonos de uso agrícola con un filtro de radio en el servidor. Descartamos las redes sociales y las APIs con
  OAuth porque no responden a nuestra pregunta (riesgo agrícola) y agregan riesgo de privacidad.
- **Círculo de 10 km alrededor de la celda de clima, no el límite municipal.** Así la capa agrícola habla del mismo punto que el
  clima (usamos `lat_grid`/`lon_grid`, no las coordenadas pedidas). Descartamos el límite municipal por no depender aún del Marco
  Geoestadístico; la contrapartida (el círculo de Manzanillo incluye mar) está declarada en la ética y en el tablero.
- **Lista blanca de etiquetas en vez de lista negra.** Con una lista negra, una etiqueta personal nueva se colaría; con lista
  blanca solo pasa lo que decidimos conservar. Se aplica **antes de guardar** en bronce.
- **Huella con saltos de línea normalizados.** Git en Windows puede convertir `LF` en `CRLF`; si la huella dependiera de eso, el mismo
  archivo daría huellas distintas en Windows y en el CI de GitHub (Linux) y el linaje se rompería. Normalizamos antes de calcular el SHA-256.
- **El linaje detiene el pipeline.** Si un valor no se puede rastrear, `run_pipeline` falla: preferimos un rojo visible a un oro
  que no podemos defender.
- **Capturar OSM una vez al mes y no a diario.** El uso de suelo cambia despacio y Overpass es un servicio público para bajo volumen.

## 4. Qué salió mal y cómo lo corregimos
- Defecto #[COMPLETAR] (interfaz, código → pruebas): al agregar columnas de fecha al oro mensual, `.round(3)` sobre todo el
  DataFrame empezó a emitir una advertencia de pandas porque no aplica a fechas. Se redondean ahora solo las columnas numéricas.
- Defecto #[COMPLETAR] (datos, diseño → revisión): el porcentaje de cobertura agrícola de Manzanillo se calcula sobre un círculo que
  incluye mar, así que subestima la cobertura en tierra. No se corrigió en esta etapa; se documentó como sesgo y queda como mejora.
- [COMPLETAR: defectos reales del equipo, p. ej. errores de la primera captura, 429 de Overpass, problemas con GeoPandas en Windows,
  con tiempo de corrección]

## 5. Qué aprendimos
**Ingeniería de Datos.** Un linaje que no se puede comprobar es una promesa. Convertirlo en una prueba que abre los archivos y compara
valores nos obligó a decidir qué es "origen" para un dato imputado (se declara, no se oculta) y para un dato que viene de dos fuentes
(gana la fuente de mayor prioridad, variable por variable). [COMPLETAR: algo propio del equipo.]

**Análisis Estadístico.** [COMPLETAR: conectar con el experimento factorial. Idea: la superficie agrícola es un atributo fijo por
municipio, así que sirve como factor de bloqueo o como variable de contexto al comparar grupos en E3.]

**Calidad en los Sistemas de Información.** [COMPLETAR: conectar con ISO/IEC 25012. Idea: la trazabilidad es evidencia de las
características *credibilidad* y *consistencia*; la lista blanca de etiquetas, de *confidencialidad*.]

## 6. Evidencias
- Commits: [COMPLETAR enlaces]
- Captura real de OSM: [COMPLETAR enlace a `data/bronce/osm_agricola_*.json` y a `calidad/bitacora_osm.csv`]
- Pruebas: [`tests/test_linaje.py`](../tests/test_linaje.py) · [`tests/test_osm_offline.py`](../tests/test_osm_offline.py) · CI: [COMPLETAR enlace a la ejecución verde]
- Reporte de linaje: [`data/oro/reporte_linaje.json`](../data/oro/reporte_linaje.json)
- Mapa: [`tablero/mapa_agricola.html`](../tablero/mapa_agricola.html)

## Uso de IA generativa
Usamos Claude (Anthropic) para generar el borrador del extractor de OSM, la unión espacial, el linaje, las pruebas, el tablero y las
plantillas de ética y relatoría, y para revisar la documentación de las APIs. [COMPLETAR: qué ejecutamos, revisamos y modificamos
nosotros, y qué verificamos a mano (robots.txt, términos).] Cada integrante puede explicar cualquier parte en la defensa.
