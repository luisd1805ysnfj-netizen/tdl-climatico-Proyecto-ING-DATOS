# Relatoría E2 · Observatorio de Inteligencia Climática (Colima, Tecomán y Manzanillo)

Equipo registrado en E0: Luis Alfredo Ruiz Fuentes y Ariadna Andrea Muñoz Andrade · Periodo documentado: 17 al 27 de noviembre de 2026

> Los integrantes constan en E0. Las horas individuales y una URL de interfaz
> público no están registradas, por lo que no se asignan ni inventan.

## 1. Qué nos propusimos
Integrar una fuente especializada al observatorio, garantizar que **cada valor de
la capa oro** se pueda rastrear hasta su archivo de bronce y fecha de ingesta, y
documentar ética y legalidad. Open-Meteo está integrado; el extractor geoespacial
OSM se conserva como experimental y no tiene captura real. Metas: (a) 100 % de
los valores de oro con origen verificable o imputado declarado; (b) cero
etiquetas personales en bronce; (c) no automatizar fuentes sin revisar sus
términos y límites.

## 2. Qué hicimos
| Fecha | Qué | Quién | Horas |
|---|---|---|---|
| 17-nov | Elección de OpenStreetMap sobre DENUE y diseño del linaje | Equipo | Pendiente de bitácora individual |
| 17-nov | Huella SHA-256, posición y referencia por registro; verificación automática | Equipo | Pendiente de bitácora individual |
| 17-nov | Extractor de Overpass con lista blanca, reintentos y pruebas offline | Equipo | Pendiente de bitácora individual; no hay captura real |
| 23-nov | Consolidación documental de E2 | Equipo | Pendiente de bitácora individual |
| 26-nov | Regeneración y verificación del pipeline con datos actuales | Equipo | 13,176 valores sin fallos de linaje |
| 27-nov | Revisión documental de E2 y límites de las fuentes | Revisión del repositorio | Sin captura real OSM; el tag `e2` ya existe, no se movió |

## 3. Qué decidimos y por qué
- **Open-Meteo integrado; OSM experimental.** El flujo de clima está operativo y trazable. El extractor OSM usa una API documentada,
  pero no se capturaron datos reales; que no requiera token no demuestra autorización o capacidad para despliegue. DENUE tampoco está
  conectado y necesitaría verificar su proceso de acceso y condiciones.
- **Círculo de 10 km alrededor de la celda de clima, no el límite municipal.** Así la capa agrícola habla del mismo punto que el
  clima (usamos `lat_grid`/`lon_grid`, no las coordenadas pedidas). Descartamos el límite municipal por no depender aún del Marco
  Geoestadístico; la contrapartida (el círculo de Manzanillo incluye mar) está declarada en la ética y en la interfaz React.
- **Lista blanca de etiquetas en vez de lista negra.** Con una lista negra, una etiqueta personal nueva se colaría; con lista
  blanca solo pasa lo que decidimos conservar. Se aplica **antes de guardar** en bronce.
- **Huella con saltos de línea normalizados.** Git en Windows puede convertir `LF` en `CRLF`; si la huella dependiera de eso, el mismo
  archivo daría huellas distintas en Windows y en el CI de GitHub (Linux) y el linaje se rompería. Normalizamos antes de calcular el SHA-256.
- **El linaje detiene el pipeline.** Si un valor no se puede rastrear, `run_pipeline` falla: preferimos un rojo visible a un oro
  que no podemos defender.
- **No capturar OSM todavía.** Aunque el uso de suelo cambia despacio, `robots.txt` del endpoint público presenta `Disallow: /api/`.
  Antes de ejecutar la captura se debe confirmar la política aplicable y el volumen permitido o usar un servicio/instancia autorizada.

## 4. Qué salió mal y cómo lo corregimos
- Defecto #1 (interfaz, código → pruebas): al agregar columnas de fecha al oro mensual, `.round(3)` sobre todo el
  DataFrame empezó a emitir una advertencia de pandas porque no aplica a fechas. Se redondean ahora solo las columnas numéricas.
- Defecto #2 (datos, diseño → revisión): el porcentaje de cobertura agrícola de Manzanillo se calcula sobre un círculo que
  incluye mar, así que subestima la cobertura en tierra. No se corrigió en esta etapa; se documentó como sesgo y queda como mejora.
- Defecto #3 (entrega, estructura): parte de E2 quedó dentro de carpetas anidadas. Se corrigió usando la raíz como fuente principal. La verificación local actual registra 74 aprobadas y 3 omitidas.
- Defecto #4 (publicación): en una revisión anterior no existía el tag `e2` ni archivos reales OSM. El tag `e2` ya existe en el repositorio actual; no se movió durante esta auditoría. La captura real sigue pendiente de revisión de política y términos.

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
- Commits: se utiliza el historial verificable disponible en el repositorio actual.
- Captura real de OSM: pendiente. No hay archivos `osm_agricola_*.json` ni `bitacora_osm.csv` reales; las pruebas OSM son offline. La aplicación web sí consulta Overpass para ubicaciones mapeadas, con caché en memoria del navegador; no se presenta esa consulta como una captura OSM guardada.
- Pruebas: [`tests/test_linaje.py`](../tests/test_linaje.py) · [`tests/test_osm_offline.py`](../tests/test_osm_offline.py) · Resultado local actual: 74 aprobadas y 3 omitidas.
- Reporte de linaje: [`data/oro/reporte_linaje.json`](../data/oro/reporte_linaje.json)
- Interfaz React: [`frontend/src/App.jsx`](../frontend/src/App.jsx)

## Uso de IA generativa
Se utilizó asistencia de IA para redactar el borrador del extractor de OSM, la unión espacial, el linaje, las pruebas y las
plantillas de ética y relatoría. El código se ejecutó localmente y se verificó con pruebas; antes de cualquier captura real deben
confirmarse manualmente los términos vigentes, el `robots.txt` y la política de uso de Overpass. Cada integrante debe poder explicar
cualquier parte del código y sus decisiones.
