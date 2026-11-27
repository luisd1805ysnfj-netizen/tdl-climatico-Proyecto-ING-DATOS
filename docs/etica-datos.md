# Ética, legalidad y gobernanza de datos

Observatorio Climático y Mercado · Última revisión documental: 27 de noviembre
de 2026.

> Esta revisión describe los servicios y datos presentes en el repositorio. No
> constituye asesoría legal ni sustituye la revisión de los términos vigentes
> del proveedor, endpoint, plan o caso de uso concreto.

## 1. Fuentes y estado de conexión

| Fuente | Uso en el proyecto | Estado / licencia relevante | Atribución y límite |
|---|---|---|---|
| Open-Meteo Archive API | Captura histórica de Bronce | Integrada; CC BY 4.0 y términos del servicio | API gratuita solo para uso no comercial; atribuir y declarar cambios |
| Open-Meteo Forecast / Seasonal | Datos climáticos del frontend | Integradas desde el navegador | Atribución visible; valores de modelo/reanálisis, no mediciones verificadas en parcela |
| OpenStreetMap / Overpass API | Ubicaciones mapeadas en el frontend; extractor geoespacial experimental | ODbL 1.0; no hay captura OSM real persistida | Atribuir a colaboradores OSM; el punto no verifica comprador o producto |
| OpenStreetMap tiles | Mapa interactivo | Tiles públicos sujetos a su política de uso | © OpenStreetMap contributors; no descarga masiva, precarga ni uso offline no permitido |
| Frankfurter | Conversión de referencia MXN/USD | Conectada; tasa diaria indicativa | No es precio intradía ni tasa de liquidación; confirmar condiciones antes de redistribuir |
| OSRM público | Ruta de respaldo | Conectado como servicio público de referencia | Geometría/distancia/tiempo estimado; no ofrece tráfico real ni tarifas; no usar como backend de alto volumen |
| TollGuru | Tarifas/rutas, opcional | Solo conectado si el proxy de servidor tiene `TOLLGURU_API_KEY` | La clave es secreta de servidor, nunca `VITE_*`; datos sujetos al plan y condiciones |
| Mercado / rangos agronómicos | Endpoints opcionales | No hay proveedor oficial de mercado conectado por defecto | Catálogo local ilustrativo; metadatos de fuente declarados no certifican autorización |

El proyecto no implementa *scraping* de páginas web. Usa endpoints API
documentados donde se indica; que un endpoint responda no demuestra por sí solo
que cualquier volumen, finalidad o redistribución esté autorizado. La
disponibilidad de la API tampoco sustituye la licencia de los datos.

## 2. Términos, políticas y límites

### 2.1 Open-Meteo

- Términos: <https://open-meteo.com/en/terms>. Licencia de datos:
  <https://open-meteo.com/en/licence>.
- La API gratuita se limita a usos no comerciales según los términos del
  proveedor y requiere atribución CC BY 4.0. El proyecto es académico; cualquier
  explotación comercial requiere contratar o conseguir permisos compatibles.
- El histórico es reanálisis/modelo asociado a una celda de malla, no una
  observación garantizada en la ubicación marcada. Se conservan las coordenadas
  efectivamente devueltas por la API.
- `https://archive-api.open-meteo.com/robots.txt` fue consultado el
  2026-11-26 y devolvió `User-agent: *` y `Disallow: /`. No se usa para autorizar
  rastreo: la aplicación consulta el endpoint API documentado y no raspa páginas.
  Deben respetarse los términos, límites y atribución vigentes.

### 2.2 OpenStreetMap y Overpass

- Derechos y atribución OSM: <https://www.openstreetmap.org/copyright>.
  Overpass API: <https://wiki.openstreetmap.org/wiki/Overpass_API>.
- Los datos OSM están sujetos a ODbL 1.0. Una base derivada sustancial puede
  tener obligaciones *share-alike*; la extracción OSM no se mezcla con el
  dataset climático CC BY.
- El extractor `extractors/osm_overpass.py` tiene pruebas offline, pero no se
  encontró una captura real `osm_agricola_*.json`. No ejecutar la captura real
  hasta revisar la política vigente del endpoint y confirmar que el volumen
  previsto está permitido.
- El frontend consulta Overpass para ubicaciones de un radio de 40 km y mantiene
  una caché de 15 minutos solo en memoria del navegador. La caché local no
  limita el volumen agregado de usuarios en un despliegue público.
- `https://overpass-api.de/robots.txt` fue consultado el 2026-11-26 y devolvió
  `Disallow: /api/` y `Disallow: /munin/`. Robots es una política para
  rastreadores, no una licencia ni una autorización contractual. El proyecto no
  infiere permiso automatizado de la disponibilidad técnica; para producción,
  confirmar directamente la política aplicable y considerar un servicio
  contratado o una instancia propia autorizada.
- Tiles: <https://operations.osmfoundation.org/policies/tiles/>. Se usa la capa
  interactiva estándar, con atribución visible y sin descargas masivas.

### 2.3 Rutas, cambio y APIs opcionales

- OSRM público solo aporta rutas de referencia. El modo de respaldo no presenta
  tráfico ni tarifas de peaje como datos reales.
- TollGuru se consulta desde un proxy de servidor; la clave vive en el secreto
  `TOLLGURU_API_KEY` y nunca debe incluirse en el bundle del navegador. La
  cotización y cobertura dependen del contrato/plan configurado.
- Frankfurter devuelve una tasa diaria de referencia MXN/USD. No representa una
  operación cambiaria ni sustituye la moneda original de una cotización.
- `VITE_MARKET_PRICES_API` y `VITE_CROP_REQUIREMENTS_API` son conectores
  opcionales. La aplicación puede validar metadatos declarados (`source`, URL,
  licencia y fecha), pero no puede certificar que el proveedor tenga derechos
  para redistribuir los datos.
- No se conecta SNIIM, USDA AMS ni SMN/CONAGUA por defecto. El catálogo local
  visible de precios, mínimos y rangos de cultivo es ilustrativo, no cotización,
  comprador, tarifa ni rango agronómico oficial.

## 3. Privacidad y minimización

El pipeline meteorológico no guarda nombres, teléfonos, correos ni otros
identificadores personales. El extractor OSM aplica una lista blanca antes de
escribir en Bronce. Esto no significa que la aplicación web no procese datos de
ubicación:

- El navegador solicita permiso para GPS solo cuando la persona pulsa “Usar mi
  ubicación”; también puede marcar una parcela manualmente.
- Las coordenadas seleccionadas se envían a proveedores externos para solicitar
  clima, ubicaciones o rutas. La interfaz lo informa en “Fuentes y API”.
- El frontend no guarda deliberadamente la ubicación en un perfil ni en
  `localStorage`; la conserva en memoria durante la sesión. La retención de
  registros de red por proveedores queda bajo sus políticas.
- No incluir coordenadas de parcelas privadas en reportes públicos sin
  consentimiento. Revisar la legislación de privacidad vigente antes de publicar
  el servicio.

## 4. Sesgos y límites de interpretación

| Riesgo | Efecto | Mitigación |
|---|---|---|
| Malla meteorológica y reanálisis | No representa necesariamente el microclima de una parcela | Mostrar fuente, fechas y coordenadas de malla; no tratarlo como medición de estación |
| Cobertura OSM voluntaria | Puede omitir mercados, comercios y usos de suelo | Denominar “ubicación mapeada”; nunca afirmar que compra un cultivo |
| Áreas circulares de consulta | Pueden incluir zonas vecinas o mar | No presentarlas como límites municipales ni como censo |
| Referencias locales | Pueden confundirse con precios/ofertas reales | Etiqueta “ilustrativo/no oficial” visible y fuente pendiente |
| Compatibilidad climática | No incluye suelo, variedad, fenología ni manejo | No presentarla como recomendación agronómica o predicción de rendimiento |
| Rutas públicas | Cobertura, latencia y disponibilidad variables | Separar distancia/tiempo estimados de tráfico y tarifas conectados |
| Faltantes y anomalías | Un valor marcado no necesariamente es error | Conservar marcas, linaje y cuarentena; no borrar en silencio |

## 5. Linaje, secretos y referencias consultadas

Cada valor climático de Oro se rastrea al archivo Bronce mediante nombre,
huella SHA-256, fila y fecha de ingesta; los valores imputados deben declarar el
método. La puerta de calidad conserva registros inválidos en cuarentena con
motivo. Gitleaks está configurado en CI; la revisión actual no encontró claves
API asignadas en el código activo. Mantener TollGuru como secreto de servidor y
no subir `.env.local`.

Referencias consultadas:

- Open-Meteo: <https://open-meteo.com/en/terms> ·
  <https://open-meteo.com/en/licence> ·
  <https://archive-api.open-meteo.com/robots.txt>.
- OSM: <https://www.openstreetmap.org/copyright> ·
  <https://operations.osmfoundation.org/policies/tiles/> ·
  <https://overpass-api.de/robots.txt>.
- Overpass API: <https://wiki.openstreetmap.org/wiki/Overpass_API>.
- OSRM: <https://project-osrm.org/docs/v5.24.0/api/>.
- TollGuru: <https://tollguru.com/toll-api>.
- Frankfurter: <https://frankfurter.dev/>.

Las políticas pueden cambiar; verificar las condiciones vigentes del endpoint,
licencia y finalidad antes de cada despliegue público o comercial.
