# Declaración de ética y legalidad de datos

Observatorio de Inteligencia Climática y Gestión de Riesgos Agrícolas · Colima, Tecomán y Manzanillo
Equipo: [COMPLETAR: integrantes] · Última revisión de términos: 17 de noviembre de 2026 · Versión de la entrega E2

> Los términos de uso cambian. Antes de entregar, **vuelvan a abrir cada enlace de la sección 5** y confirmen que lo
> escrito aquí sigue vigente; cambien la fecha de revisión. Los campos `[COMPLETAR]` son observaciones que solo ustedes
> pueden hacer (lo que dice cada `robots.txt` el día que lo leyeron).

## 1. Resumen

| Fuente | Qué aporta | Datos personales | Licencia de los datos | Uso |
|---|---|---|---|---|
| Open-Meteo (API de archivo) | Clima diario: temperatura, lluvia y viento | No | CC BY 4.0 | Académico, no comercial |
| OpenStreetMap vía Overpass API | Uso de suelo agrícola (polígonos) | No, tras el saneamiento de la sección 3 | ODbL 1.0 | Académico |

Ninguna fuente se obtiene con *scraping* de páginas web: ambas son **APIs públicas documentadas** pensadas para acceso
programático. Aun así se aplican las reglas del proyecto: User-Agent honesto, pausa entre peticiones, reintentos con espera y
respeto a los límites publicados.

## 2. Base legal y términos de uso, por fuente

### 2.1 Open-Meteo (`archive-api.open-meteo.com`)
- **Términos:** la API gratuita es solo para **uso no comercial**, con menos de 10,000 llamadas al día, 5,000 por hora y 600
  por minuto, y exige aceptar la licencia de datos CC BY 4.0.
- **Nuestro consumo:** 3 peticiones por captura diaria (una por municipio) más la descarga histórica inicial. Es
  aproximadamente 0.03 % del límite diario.
- **Licencia CC BY 4.0:** obliga a dar crédito, enlazar la licencia e indicar si se hicieron cambios. Cumplimiento: el tablero y el mapa
  muestran "Weather data by Open-Meteo.com" con enlace, y la documentación declara que los datos fueron transformados (limpieza,
  imputación marcada, agregación mensual).
- **Implicación comercial (importante):** el modelo de negocio del proyecto contempla suscripciones. Mientras el
  observatorio sea académico, el uso gratuito es válido. **Si algún día se cobra por él, se necesita una suscripción comercial de
  Open-Meteo o una instancia propia** (el servidor es de código abierto).
- **Fuentes y robots.txt:** `https://archive-api.open-meteo.com/robots.txt` — leído el [COMPLETAR fecha]. Lo que dice: [COMPLETAR].
  Conclusión: [COMPLETAR, p. ej. "no restringe el acceso a la ruta /v1/archive" o la restricción que encuentren].

### 2.2 OpenStreetMap vía Overpass (`overpass-api.de`)
- **Términos:** el servidor público de Overpass está pensado para **consultas manuales y de bajo volumen**; quien lo use desde un
  script debe identificarse con un User-Agent propio y puede ser limitado (error 429) o bloqueado si abusa.
- **Nuestro consumo:** 3 consultas por captura, con 5 s de pausa entre ellas, reintentos con espera exponencial y un espejo de
  respaldo. La captura es **mensual o manual**, nunca por hora: el uso de suelo cambia despacio.
- **Licencia ODbL 1.0:** exige atribución ("© colaboradores de OpenStreetMap"), y que las **bases de datos derivadas** se compartan
  bajo la misma licencia (*share-alike*). Cumplimiento: la atribución aparece en el mapa, el tablero y dentro de cada
  archivo de bronce (campo `osm3s.copyright`).
- **Decisión pendiente para E3 (publicación del dataset):** la capa derivada de OSM (`osm_parcelas.geojson`) es una extracción
  sustancial, así que debe publicarse bajo ODbL. Las tablas de clima van bajo CC BY 4.0. Se publicarán **separadas** con su licencia
  cada una. Esto es una interpretación del equipo, no asesoría legal.
- **robots.txt:** `https://overpass-api.de/robots.txt` — leído el [COMPLETAR fecha]. Lo que dice: [COMPLETAR].
  Conclusión: [COMPLETAR].

### 2.3 Marco legal general
- **Datos personales:** el observatorio no necesita ni captura datos de personas físicas, por lo que el tratamiento queda fuera del
  alcance principal de la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (verifiquen la versión vigente).
  Aun así se aplica el principio de **minimización**: lo que no se necesita no se guarda.
- **Reglas del proyecto:** cero datos personales; scraping ético; todo reproducible.

## 3. Privacidad: riesgos y mitigaciones

| Riesgo | Dónde puede aparecer | Mitigación aplicada | Evidencia |
|---|---|---|---|
| Nombres de propietarios u operadores | Etiquetas `name`, `operator`, `owner` de los polígonos de OSM | **Lista blanca** de etiquetas (`landuse`, `crop`, `trees`, `produce`, `orchard`, `plant`, `irrigation`); el resto se elimina **antes de escribir en bronce** | `extractors/osm_overpass.py::sanear_elementos` y prueba `test_se_eliminan_los_datos_personales_antes_de_guardar` |
| Teléfonos, correos, direcciones | Etiquetas `phone`, `email`, `addr:*`, `contact:*` | Misma lista blanca | Misma prueba |
| Identificar a un dueño por la forma de su terreno | Polígonos de huertas visibles en el mapa | Solo uso de suelo y cultivo; sin dueños ni direcciones; geometría simplificada en el mapa; cifras publicadas por municipio, no por predio | `pipeline/mapa.py` |
| Rastro del saneamiento con datos sensibles | Bitácoras y reportes | El reporte de saneamiento guarda **cuántas etiquetas y de qué clave** se descartaron, nunca sus valores | `documento["saneamiento"]` en cada archivo de bronce |
| Datos del equipo | Repositorio | Sin credenciales en el repositorio; `gitleaks` en cada push | `.github/workflows/ci.yml` |

## 4. Sesgos conocidos y cómo se mitigan

| Sesgo | Efecto sobre las conclusiones | Mitigación |
|---|---|---|
| **Mapeo voluntario incompleto** (OSM) | Subestima la superficie agrícola, sobre todo en zonas rurales poco mapeadas | Se presenta como **mínimo**, no como censo; advertencia visible en el tablero; contraste futuro con DENUE o el Marco Geoestadístico |
| **Solo polígonos simples** (`way`) | Las parcelas grandes mapeadas como multipolígono (relaciones) no se cuentan | Limitación declarada; las relaciones quedan fuera de la consulta a propósito para no depender de reconstruir geometrías complejas |
| **Círculo, no límite municipal** | Incluye predios de municipios vecinos y, en Manzanillo, **mar** (el porcentaje de cobertura se subestima) | Se usa como indicador de exposición del punto de clima, no del municipio; mejora prevista con el Marco Geoestadístico |
| **Reanálisis de malla, no estación** (Open-Meteo) | Suaviza extremos de lluvia y viento; la celda tiene otra elevación que el punto pedido (p. ej. la malla de Colima está a ~495 m) | Se guardan `lat_grid`, `lon_grid` y `elevacion_m` reales en cada registro; los extremos se marcan como atípicos y no se borran; contraste previsto con datos del SMN |
| **Imputación** | Un valor imputado no es una observación | Cada valor imputado se declara en la columna `origen_<variable>` (`IMPUTADO:<método>`) y en `<variable>_imputado` |
| **Sobreinterpretar** | Confundir "marcado como atípico" con "error" | Los atípicos se marcan y se conservan; se revisan contra fuentes externas antes de concluir |

## 5. Referencias consultadas (verificar vigencia antes de entregar)
- Términos de Open-Meteo: https://open-meteo.com/en/terms · Licencia de datos: https://open-meteo.com/en/licence
- Derechos de autor y licencia de OpenStreetMap: https://www.openstreetmap.org/copyright
- Política de uso del servidor público de Overpass: wiki de OpenStreetMap, página *Overpass API*
- [COMPLETAR: enlaces a los `robots.txt` leídos y fecha de lectura]

## 6. Trazabilidad como práctica ética
Un dato que no se puede rastrear no se puede corregir ni cuestionar. Por eso cada valor de la capa oro lleva su origen
(`origen_<variable>`: archivo de bronce, huella SHA-256 y posición) o se declara derivado, y una prueba automática lo verifica
en cada ejecución (`reporte_linaje.json`).
