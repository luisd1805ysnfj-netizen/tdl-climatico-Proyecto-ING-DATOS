# Observatorio Climático & Mercado

## Desarrollo y despliegue

Desde esta carpeta instala dependencias y arranca Vite:

```powershell
npm install
npm run dev
```

Para validar y previsualizar la versión estática:

```powershell
npm run build
npm run preview
```

El directorio generado para publicar es `dist`. Vercel y Netlify sirven el sitio mediante HTTPS; el proxy de rutas incluido puede ejecutarse como función de servidor en ambos. GitHub Pages solo sirve archivos estáticos, por lo que las rutas TollGuru requieren un proxy externo.

## Clima: Open-Meteo

- **Condiciones actuales/modeladas:** Open-Meteo Forecast API.
- **Proyección:** Open-Meteo Seasonal Forecast API con ECMWF SEAS5/EC46, hasta 214 días solicitados. Es un pronóstico de área de aproximadamente 36 km, sin corrección de sesgo; no equivale a una observación de estación meteorológica.
- **Histórico:** Open-Meteo Historical Weather API. Es información de reanálisis/modelo, no una medición local garantizada.
- La app consulta estos servicios para las coordenadas seleccionadas. Si una consulta no tiene respuesta, muestra “Dato no disponible / Pendiente de conexión a API oficial”; no sustituye campos ausentes con valores locales.
- La atribución visible enlaza a Open-Meteo. Los datos se ofrecen bajo **CC BY 4.0**. El servicio gratuito solo permite uso no comercial; una aplicación comercial debe contratar un plan cuyas condiciones permitan ese uso. Revisa los [términos de Open-Meteo](https://open-meteo.com/en/terms) antes de desplegar.

## Precios agrícolas y puntos regionales

La app muestra un catálogo local ilustrativo para sus 21 cultivos, con rangos climáticos, referencias MXN/USD independientes, mínimos orientativos y 25 coordenadas regionales. **No son precios oficiales, cotizaciones vigentes, ofertas de compra, mínimos confirmados ni compradores/centros de acopio verificados.** Los puntos se identifican en el mapa como referencias geográficas y no deben usarse como destinos comerciales confirmados. Consulta `src/data/referenceCatalog.json`; valida la información directamente con fuentes y compradores antes de tomar decisiones.

Para conectar cotizaciones y compradores reportados por una fuente autorizada, configura `VITE_MARKET_PRICES_API` en `frontend/.env.local`; la app consulta `${VITE_MARKET_PRICES_API}/prices`. Debe ser un origen HTTPS fuera de desarrollo local y responder con:

- `source`: objeto con `name`, `url` HTTPS y `license`.
- `updatedAt`: fecha ISO de la respuesta.
- `prices`: objeto indexado por nombre de cultivo. Cada cotización incluye `price` numérico, `currency` (`MXN` o `USD`), `unit` y opcionalmente `region` y `updatedAt`. Si la unidad es kg o tonelada, la app convierte a precio por kg y muestra MXN/USD con el tipo de cambio de referencia fechado de Frankfurter.
- `buyers` opcional: lista de registros con `id`, `name`, `city`, `country`, `lat`, `lng`, `crops` y `prices` con el mismo formato de cotización. Puede incluir `state`, `updatedAt`, `minimumOrder`, `deliveryTerms`, `trend30Days` y `localClimate`; estos campos solo se presentan cuando la API los entrega.

El endpoint puede integrarse con fuentes autorizadas como SNIIM/Datos Abiertos México o USDA AMS Market News. La app no consulta ni extrae automáticamente sus páginas; un proxy/API debe devolver JSON en el contrato indicado y proteger cualquier clave en el servidor. Una referencia de mercado mayorista no representa una oferta de compra directa al agricultor. La fuente/licencia son metadatos declarados por el endpoint y la interfaz no puede certificar su exactitud, autorización o vigencia. No se implementa scraping. Cuando la API conectada no incluya un cultivo, la tabla muestra el valor local ilustrativo por separado, con su estado no oficial.

Las ubicaciones se consultan en OpenStreetMap mediante Overpass API, limitadas a un radio de 40 km alrededor de la región/coordenada seleccionada y con caché en memoria del navegador de 15 minutos. Se atribuyen a OpenStreetMap contributors y su licencia ODbL. Una ubicación etiquetada como mercado o comercio mayorista no confirma un comprador, que compre el cultivo seleccionado, ni sus mínimos o condiciones de entrega. Esos datos permanecen pendientes hasta que una API autorizada los proporcione. El endpoint público es de bajo volumen; su `robots.txt` consultado el 26-nov-2026 indica `Disallow: /api/`. Eso no determina por sí solo las condiciones contractuales de la API, pero tampoco es una autorización. Antes de desplegar públicamente, confirma la política vigente y el volumen permitido, o usa un servicio/instancia autorizada.

La aplicación pide permiso del navegador solo si el usuario elige “Usar mi ubicación”. Si usa GPS o marca una parcela, las coordenadas se envían a los proveedores necesarios para solicitar clima, ubicaciones o rutas. La app no las conserva en un perfil ni en `localStorage`; permanecen en memoria durante la sesión. La retención de registros del proveedor se rige por sus propias políticas.

## Compatibilidad climática de cultivos

Los 21 cultivos tienen rangos locales orientativos en `src/data/referenceCatalog.json` para que la interfaz calcule y muestre un porcentaje cuando hay clima actual de Open-Meteo. **Estos rangos no se presentan como una fuente agronómica verificada ni sustituyen evaluación profesional.** Para priorizar datos agronómicos respaldados por una fuente, configura `VITE_CROP_REQUIREMENTS_API`; la app consulta `${VITE_CROP_REQUIREMENTS_API}/requirements` por HTTPS. La respuesta debe incluir:

- `source`: `name`, URL `https` y `license` de la fuente agronómica.
- `updatedAt`: fecha ISO de actualización del dataset.
- `crops`: objeto por nombre de cultivo, donde cada registro declara `temperatureC` y `humidityPercent`, cada uno con `min`, `optimum` y `max`.

Los rangos de la API deben estar respaldados por FAO ECOCROP u otra guía técnica; antes de publicarlos, verifica licencia, atribución y permiso de reutilización para el uso previsto. El porcentaje compara la temperatura/humedad actual de Open-Meteo con el óptimo mediante una escala lineal y, cuando hay histórico de Open-Meteo, muestra además el promedio del indicador de los meses históricos disponibles. `Compatible` (>=70%) es solo una clasificación climática de referencia: no evalúa suelo, cultivar, fenología, manejo ni rendimiento y no constituye recomendación agronómica. La interfaz indica si se utilizó el catálogo local ilustrativo o la API configurada.

## Conversión de referencia MXN/USD

La conversión usa `https://api.frankfurter.dev/v2/rate/mxn/usd`, que devuelve una tasa diaria de referencia, no una cotización intradía ni una tasa de liquidación. La interfaz muestra su fecha. Si la API de cambio falla, solo presenta el valor y moneda que entregó la fuente de mercado. La atribución enlaza a Frankfurter; sus tasas provienen de bancos centrales y proveedores documentados en su sitio.

## Rutas, tráfico y casetas

El panel consulta el proxy `/api/route-tolls` con TollGuru. Configura la clave `TOLLGURU_API_KEY` como secreto del servidor; nunca la publiques como una variable `VITE_*`. La moneda de las tarifas se presenta tal como la entrega la API. La hora de consulta no necesariamente es la fecha de vigencia oficial de cada tarifa.

Si TollGuru no está conectado o falla, se consulta el servicio público OSRM para geometría, distancia y tiempo estimado. Ese modo no ofrece tráfico en tiempo real ni tarifas de peaje, y la interfaz no inventa casetas o precios. El servidor público OSRM tiene límites y no debe usarse para cargas masivas ni como servicio de producción sin un proveedor apropiado.

## Mapa y atribución

El mapa usa la capa estándar de OpenStreetMap:

`https://tile.openstreetmap.org/{z}/{x}/{y}.png`

La atribución visible es **© OpenStreetMap contributors** y enlaza a su información de copyright. Respeta la [política de uso de tiles de OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/): uso interactivo normal, sin descarga masiva, precarga ni funcionamiento offline basado en esos tiles. La disponibilidad de la capa no implica que OpenStreetMap verifique compradores, precios o condiciones de rutas.

Los proveedores externos están sujetos a sus propios términos, licencias, cobertura y límites. Antes de un despliegue público o comercial, confirma que cada fuente y plan contratado cubran el uso previsto.
