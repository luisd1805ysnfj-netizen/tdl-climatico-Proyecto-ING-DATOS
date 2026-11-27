# Relatoría E2 · Observatorio de Inteligencia Climática (Colima, Tecomán y Manzanillo)

Equipo: Luis · Luis David (integrante principal registrado en la bitácora de calidad) · Periodo: 17 al 23 de noviembre de 2026

> Esta versión consolida datos verificables. Los nombres de integrantes, horas individuales y tablero público siguen requiriendo
> información del equipo porque no están presentes de forma inequívoca en el repositorio.

## 1. Qué nos propusimos
Integrar una fuente especializada geoespacial al observatorio, garantizar que **cada valor de la capa oro** se pueda rastrear
hasta su archivo de bronce y su fecha de ingesta, y documentar la ética y legalidad de las dos fuentes. Metas medibles:
(a) un archivo `osm_agricola_*` por municipio que pase la puerta de calidad; (b) 100 % de los valores de oro con origen verificable
o declarado como imputado; (c) cero etiquetas personales en bronce.

## 2. Qué hicimos
| Fecha | Qué | Quién | Horas |
|---|---|---|---|
| 17-nov | Elección de OpenStreetMap sobre DENUE y diseño del linaje | Equipo | Pendiente de bitácora individual |
| 17-nov | Huella SHA-256, posición y referencia por registro; verificación automática | Equipo | Pendiente de bitácora individual |
| 17-nov | Extractor de Overpass con lista blanca, reintentos y espejo; pruebas offline | Equipo | Pendiente de bitácora individual |
| 23-nov | Consolidación final de E2 y publicación del commit `E2_Final` | Equipo | Pendiente de bitácora individual |
| 26-nov | Regeneración y verificación del pipeline con datos actuales | Equipo | 13,176 valores sin fallos de linaje |
| Pendiente | Captura real de OSM y creación del tag oficial `e2` | Equipo | Acción pendiente |

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
- Defecto #1 (interfaz, código → pruebas): al agregar columnas de fecha al oro mensual, `.round(3)` sobre todo el
  DataFrame empezó a emitir una advertencia de pandas porque no aplica a fechas. Se redondean ahora solo las columnas numéricas.
- Defecto #2 (datos, diseño → revisión): el porcentaje de cobertura agrícola de Manzanillo se calcula sobre un círculo que
  incluye mar, así que subestima la cobertura en tierra. No se corrigió en esta etapa; se documentó como sesgo y queda como mejora.
- Defecto #3 (entrega, estructura): parte de E2 quedó dentro de carpetas anidadas. Se corrigió copiando el código funcional a la raíz y verificándolo con 66 pruebas.
- Defecto #4 (publicación): no existía el tag `e2` ni archivos reales de captura OSM. El tag se completará antes de cada entrega y la captura se hará solo bajo una revisión explícita de términos.

## 5. Qué aprendimos
**Ingeniería de Datos.** Un linaje que no se puede comprobar es una promesa. Convertirlo en una prueba que abre los archivos y compara
valores nos obligó a decidir qué es "origen" para un dato imputado (se declara, no se oculta) y para un dato que viene de dos fuentes
(gana la fuente de mayor prioridad, variable por variable). En este equipo, la decisión más importante fue que
la trazabilidad se convierta en una prueba ejecutable y que el pipeline falle si un origen no puede verificarse.

**Análisis Estadístico.** E2 no completó el experimento factorial. En E3, la superficie agrícola puede utilizarse como contexto
por municipio o como bloqueante al comparar dos factores climáticos.

**Calidad en los Sistemas de Información.** La trazabilidad es evidencia de *credibilidad* y *consistencia*; la lista blanca
de etiquetas es evidencia de minimización y *confidencialidad*.

## 6. Evidencias
- Commits: E2_Final (`91bd698`); consolidación posterior en el commit de correcciones E2.
- Captura real de OSM: pendiente. No hay archivos `osm_agricola_*.json` ni `bitacora_osm.csv` reales; las pruebas OSM son offline.
- Pruebas: [`tests/test_linaje.py`](../tests/test_linaje.py) · [`tests/test_osm_offline.py`](../tests/test_osm_offline.py) · Resultado local: 66 aprobadas y 4 omitidas.
- Reporte de linaje: [`data/oro/reporte_linaje.json`](../data/oro/reporte_linaje.json)
- Mapa: [`tablero/mapa_agricola.html`](../tablero/mapa_agricola.html)

## Uso de IA generativa
Se utilizó asistencia de IA para redactar el borrador del extractor de OSM, la unión espacial, el linaje, las pruebas y las
plantillas de ética y relatoría. El código se ejecutó localmente y se verificó con pruebas; antes de cualquier captura real deben
confirmarse manualmente los términos vigentes, el `robots.txt` y la política de uso de Overpass. Cada integrante debe poder explicar
cualquier parte del código y sus decisiones.
