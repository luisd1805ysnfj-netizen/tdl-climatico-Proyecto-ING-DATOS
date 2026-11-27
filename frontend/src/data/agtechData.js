const configuredMxnPerUsd = Number(import.meta.env?.VITE_MXN_PER_USD_RATE)
export const REFERENCE_MXN_PER_USD = Number.isFinite(configuredMxnPerUsd) && configuredMxnPerUsd > 0
  ? configuredMxnPerUsd
  : 20

export const crops = [
  { name: 'Zanahoria', type: 'verdura', compatibility: 95, climate: { temp: [15, 24], humidity: [45, 75] }, price: 10.8, trend: 'up', trendValue: '+4.2%' },
  { name: 'Cebolla', type: 'verdura', compatibility: 92, climate: { temp: [13, 25], humidity: [40, 70] }, price: 8.4, trend: 'flat', trendValue: '+0.8%' },
  { name: 'Zarzamora', type: 'fruta', compatibility: 89, climate: { temp: [15, 25], humidity: [55, 80] }, price: 42.5, trend: 'up', trendValue: '+6.1%' },
  { name: 'Maíz', type: 'verdura', compatibility: 84, climate: { temp: [18, 30], humidity: [45, 75] }, price: 6.2, trend: 'up', trendValue: '+2.4%' },
  { name: 'Tomate', type: 'verdura', compatibility: 78, climate: { temp: [18, 29], humidity: [45, 70] }, price: 14.3, trend: 'flat', trendValue: '-0.6%' },
  { name: 'Aguacate', type: 'fruta', compatibility: 91, climate: { temp: [16, 28], humidity: [60, 85] }, price: 28.6, trend: 'up', trendValue: '+5.3%' },
  { name: 'Limón', type: 'fruta', compatibility: 88, climate: { temp: [20, 32], humidity: [50, 80] }, price: 18.2, trend: 'up', trendValue: '+3.4%' },
  { name: 'Fresa', type: 'fruta', compatibility: 90, climate: { temp: [12, 24], humidity: [55, 80] }, price: 38.4, trend: 'up', trendValue: '+7.2%' },
  { name: 'Chile Jalapeño', type: 'verdura', compatibility: 87, climate: { temp: [20, 30], humidity: [45, 75] }, price: 16.8, trend: 'flat', trendValue: '+1.1%' },
  { name: 'Papa', type: 'verdura', compatibility: 93, climate: { temp: [10, 22], humidity: [55, 80] }, price: 7.9, trend: 'flat', trendValue: '+0.5%' },
  { name: 'Pepino', type: 'verdura', compatibility: 86, climate: { temp: [18, 30], humidity: [55, 80] }, price: 9.6, trend: 'up', trendValue: '+2.1%' },
  { name: 'Brócoli', type: 'verdura', compatibility: 85, climate: { temp: [12, 23], humidity: [50, 80] }, price: 15.4, trend: 'flat', trendValue: '-0.4%' },
  { name: 'Mango', type: 'fruta', compatibility: 83, climate: { temp: [24, 35], humidity: [55, 85] }, price: 19.8, trend: 'up', trendValue: '+4.8%' },
  { name: 'Plátano', type: 'fruta', compatibility: 82, climate: { temp: [24, 32], humidity: [65, 90] }, price: 8.8, trend: 'flat', trendValue: '+0.9%' },
  { name: 'Calabacita', type: 'verdura', compatibility: 84, climate: { temp: [18, 30], humidity: [45, 75] }, price: 11.3, trend: 'up', trendValue: '+2.6%' },
  { name: 'Uva', type: 'fruta', compatibility: 80, climate: { temp: [15, 30], humidity: [35, 65] }, price: 31.2, trend: 'up', trendValue: '+3.9%' },
  { name: 'Coco', type: 'fruta', compatibility: 84, climate: { temp: [24, 32], humidity: [65, 90] }, price: 12.5, trend: 'up', trendValue: '+3.1%' },
  { name: 'Papaya', type: 'fruta', compatibility: 82, climate: { temp: [24, 35], humidity: [60, 85] }, price: 11.8, trend: 'up', trendValue: '+2.8%' },
  { name: 'Sandía', type: 'fruta', compatibility: 81, climate: { temp: [22, 35], humidity: [40, 75] }, price: 8.6, trend: 'flat', trendValue: '+1.4%' },
  { name: 'Melón', type: 'fruta', compatibility: 80, climate: { temp: [20, 34], humidity: [40, 70] }, price: 12.4, trend: 'up', trendValue: '+2.2%' },
  { name: 'Chile verde', type: 'verdura', compatibility: 86, climate: { temp: [20, 30], humidity: [45, 75] }, price: 15.2, trend: 'up', trendValue: '+2.6%' },
]

export const regions = {
  AMERICA: { label: 'América (Norte, Centro y Sudamérica)', city: 'Panamá, Panamá · referencia continental', temperature: 23, humidity: 68, rain: 12, wind: 9, feels: 24, condition: 'Templado y parcialmente nublado', mapCenter: [12, -82], latitude: 8.98, longitude: -79.52, zoom: 3 },
  Colima: { label: 'Colima, México', city: 'Colima, México', temperature: 27, humidity: 68, rain: 8, wind: 9, feels: 29, condition: 'Cálido y húmedo', mapCenter: [19.08, -103.85], latitude: 18.91, longitude: -103.88, zoom: 8 },
  'Estados Unidos': { label: 'Estados Unidos', city: 'McAllen, Texas', temperature: 27, humidity: 63, rain: 9, wind: 13, feels: 29, condition: 'Cálido y parcialmente soleado', mapCenter: [37.1, -96], latitude: 26.2034, longitude: -98.23, zoom: 4 },
  México: { label: 'México', city: 'Celaya, Guanajuato', temperature: 24, humidity: 64, rain: 8, wind: 11, feels: 25, condition: 'Templado', mapCenter: [20.52, -100.81], latitude: 20.52, longitude: -100.81, zoom: 5 },
  Colombia: { label: 'Colombia', city: 'Bogotá, Cundinamarca', temperature: 18, humidity: 74, rain: 16, wind: 7, feels: 18, condition: 'Fresco y húmedo', mapCenter: [4.57, -74.1], latitude: 4.57, longitude: -74.1, zoom: 5 },
  Perú: { label: 'Perú', city: 'Ica, Ica', temperature: 22, humidity: 58, rain: 3, wind: 13, feels: 23, condition: 'Templado y seco', mapCenter: [-14.07, -75.73], latitude: -14.07, longitude: -75.73, zoom: 5 },
  Chile: { label: 'Chile', city: 'Curicó, Maule', temperature: 19, humidity: 61, rain: 7, wind: 16, feels: 18, condition: 'Templado', mapCenter: [-34.98, -71.24], latitude: -34.98, longitude: -71.24, zoom: 5 },
  Ecuador: { label: 'Ecuador', city: 'Ambato, Tungurahua', temperature: 17, humidity: 76, rain: 14, wind: 6, feels: 17, condition: 'Fresco y húmedo', mapCenter: [-1.24, -78.62], latitude: -1.24, longitude: -78.62, zoom: 6 },
  Brasil: { label: 'Brasil', city: 'São Paulo, SP', temperature: 24, humidity: 70, rain: 11, wind: 10, feels: 25, condition: 'Tropical húmedo', mapCenter: [-23.55, -46.63], latitude: -23.55, longitude: -46.63, zoom: 5 },
  Argentina: { label: 'Argentina', city: 'Buenos Aires', temperature: 21, humidity: 62, rain: 8, wind: 12, feels: 21, condition: 'Templado y estable', mapCenter: [-34.6, -58.38], latitude: -34.6, longitude: -58.38, zoom: 5 },
  Caribe: { label: 'Caribe', city: 'Santo Domingo', temperature: 28, humidity: 78, rain: 14, wind: 16, feels: 32, condition: 'Tropical húmedo', mapCenter: [18.5, -69.9], latitude: 18.5, longitude: -69.9, zoom: 5 },
}

const rawBuyers = [
  { id: 1, name: 'Central de Abasto Celaya', city: 'Celaya', country: 'México', lat: 20.522, lng: -100.812, crops: ['Zanahoria', 'Cebolla', 'Tomate', 'Maíz'], prices: { Zanahoria: 10.8, Cebolla: 8.4, Tomate: 14.3, Maíz: 6.2 }, trend: 'up', trendValue: '+4.2%', localWeather: '24°C · Parcialmente nublado' },
  { id: 2, name: 'AgroCompras Bajío', city: 'Irapuato', country: 'México', lat: 20.676, lng: -101.356, crops: ['Zanahoria', 'Zarzamora', 'Cebolla'], prices: { Zanahoria: 11.2, Zarzamora: 43.1, Cebolla: 8.7 }, trend: 'up', trendValue: '+5.1%', localWeather: '23°C · Humedad 62%' },
  { id: 3, name: 'Mercado Mayorista CDMX', city: 'Iztapalapa', country: 'México', lat: 19.36, lng: -99.07, crops: ['Zanahoria', 'Cebolla', 'Tomate', 'Maíz'], prices: { Zanahoria: 10.5, Cebolla: 8.2, Tomate: 13.9, Maíz: 6.1 }, trend: 'flat', trendValue: '+0.7%', localWeather: '22°C · Nublado' },
  { id: 4, name: 'Frutas del Valle', city: 'Corferias', country: 'Colombia', lat: 4.657, lng: -74.103, crops: ['Zarzamora', 'Tomate', 'Cebolla'], prices: { Zarzamora: 38.9, Tomate: 12.8, Cebolla: 7.9 }, trend: 'up', trendValue: '+3.8%', localWeather: '18°C · llovizna' },
  { id: 5, name: 'Corabastos', city: 'Bogotá', country: 'Colombia', lat: 4.633, lng: -74.144, crops: ['Zanahoria', 'Cebolla', 'Maíz', 'Tomate'], prices: { Zanahoria: 9.7, Cebolla: 7.6, Maíz: 5.9, Tomate: 13.2 }, trend: 'flat', trendValue: '+1.1%', localWeather: '17°C · Humedad 74%' },
  { id: 6, name: 'AgroMercado Antioquia', city: 'Medellín', country: 'Colombia', lat: 6.244, lng: -75.581, crops: ['Zarzamora', 'Tomate', 'Zanahoria'], prices: { Zarzamora: 40.2, Tomate: 14.1, Zanahoria: 9.9 }, trend: 'up', trendValue: '+6.4%', localWeather: '20°C · Lluvioso' },
  { id: 7, name: 'Gran Mercado Mayorista', city: 'Santa Anita', country: 'Perú', lat: -12.043, lng: -76.973, crops: ['Zanahoria', 'Cebolla', 'Tomate', 'Maíz'], prices: { Zanahoria: 8.9, Cebolla: 7.1, Tomate: 12.4, Maíz: 5.7 }, trend: 'up', trendValue: '+3.3%', localWeather: '22°C · Nublado' },
  { id: 8, name: 'Terminal Agrícola Ica', city: 'Ica', country: 'Perú', lat: -14.067, lng: -75.728, crops: ['Zanahoria', 'Cebolla', 'Maíz'], prices: { Zanahoria: 8.6, Cebolla: 6.9, Maíz: 5.4 }, trend: 'flat', trendValue: '-0.2%', localWeather: '24°C · Seco' },
  { id: 9, name: 'Exportadora Sierra Norte', city: 'Trujillo', country: 'Perú', lat: -8.111, lng: -79.028, crops: ['Zarzamora', 'Zanahoria', 'Cebolla'], prices: { Zarzamora: 36.8, Zanahoria: 8.7, Cebolla: 7.0 }, trend: 'up', trendValue: '+4.9%', localWeather: '21°C · Soleado' },
  { id: 10, name: 'Lo Valledor', city: 'Santiago', country: 'Chile', lat: -33.487, lng: -70.674, crops: ['Zanahoria', 'Cebolla', 'Tomate', 'Maíz'], prices: { Zanahoria: 11.4, Cebolla: 9.2, Tomate: 15.8, Maíz: 7.1 }, trend: 'up', trendValue: '+2.7%', localWeather: '20°C · Viento suave' },
  { id: 11, name: 'Mercado Curicó', city: 'Curicó', country: 'Chile', lat: -34.983, lng: -71.239, crops: ['Zarzamora', 'Zanahoria', 'Tomate'], prices: { Zarzamora: 44.9, Zanahoria: 10.9, Tomate: 15.2 }, trend: 'up', trendValue: '+5.6%', localWeather: '18°C · Parcialmente nublado' },
  { id: 12, name: 'Terminal Sur Talca', city: 'Talca', country: 'Chile', lat: -35.426, lng: -71.655, crops: ['Zarzamora', 'Cebolla', 'Maíz'], prices: { Zarzamora: 43.8, Cebolla: 8.9, Maíz: 6.8 }, trend: 'flat', trendValue: '+1.3%', localWeather: '17°C · Fresco' },
  { id: 13, name: 'Mercado Mayor Ambato', city: 'Ambato', country: 'Ecuador', lat: -1.249, lng: -78.616, crops: ['Zanahoria', 'Cebolla', 'Tomate'], prices: { Zanahoria: 9.3, Cebolla: 7.8, Tomate: 13.5 }, trend: 'up', trendValue: '+3.1%', localWeather: '17°C · Humedad 76%' },
  { id: 14, name: 'Centro de Acopio Quito', city: 'Quito', country: 'Ecuador', lat: -0.218, lng: -78.512, crops: ['Zarzamora', 'Tomate', 'Zanahoria', 'Cebolla'], prices: { Zarzamora: 39.7, Tomate: 13.8, Zanahoria: 9.5, Cebolla: 8.0 }, trend: 'flat', trendValue: '+0.9%', localWeather: '16°C · Nublado' },
  { id: 15, name: 'AgroGuayas', city: 'Guayaquil', country: 'Ecuador', lat: -2.189, lng: -79.889, crops: ['Maíz', 'Cebolla', 'Tomate'], prices: { Maíz: 6.0, Cebolla: 7.5, Tomate: 12.9 }, trend: 'up', trendValue: '+2.8%', localWeather: '27°C · Húmedo' },
  { id: 16, name: 'CEASA Campinas', city: 'Campinas', country: 'Brasil', lat: -22.909, lng: -47.062, crops: ['Zanahoria', 'Cebolla', 'Tomate', 'Maíz'], prices: { Zanahoria: 9.1, Cebolla: 7.3, Tomate: 13.1, Maíz: 5.8 }, trend: 'up', trendValue: '+3.7%', localWeather: '25°C · Parcialmente nublado' },
  { id: 17, name: 'Mercado Del Sur', city: 'Montevideo', country: 'Uruguay', lat: -34.901, lng: -56.164, crops: ['Zanahoria', 'Cebolla', 'Tomate'], prices: { Zanahoria: 10.2, Cebolla: 8.1, Tomate: 14.0 }, trend: 'flat', trendValue: '+0.4%', localWeather: '19°C · Viento litoral' },
  { id: 18, name: 'Central Buenos Aires', city: 'Buenos Aires', country: 'Argentina', lat: -34.603, lng: -58.381, crops: ['Zanahoria', 'Cebolla', 'Maíz', 'Tomate'], prices: { Zanahoria: 10.7, Cebolla: 8.6, Maíz: 6.4, Tomate: 14.6 }, trend: 'up', trendValue: '+2.2%', localWeather: '21°C · Soleado' },
  { id: 19, name: 'McAllen Produce Terminal', city: 'McAllen', country: 'Estados Unidos', lat: 26.2034, lng: -98.2300, crops: ['Zanahoria', 'Cebolla', 'Tomate', 'Aguacate', 'Limón', 'Chile Jalapeño'], prices: { Zanahoria: 0.82, Cebolla: 0.68, Tomate: 1.24, Aguacate: 2.18, Limón: 1.35, 'Chile Jalapeño': 1.42 }, currency: 'USD', trend: 'up', trendValue: '+5.8%', localWeather: '27°C · Húmedo' },
  { id: 20, name: 'Laredo International Cold Storage', city: 'Laredo', country: 'Estados Unidos', lat: 27.5064, lng: -99.5075, crops: ['Cebolla', 'Maíz', 'Papa', 'Aguacate', 'Chile Jalapeño', 'Limón'], prices: { Cebolla: 0.71, Maíz: 0.48, Papa: 0.52, Aguacate: 2.26, 'Chile Jalapeño': 1.38, Limón: 1.31 }, currency: 'USD', trend: 'up', trendValue: '+4.6%', localWeather: '29°C · Seco' },
  { id: 21, name: 'Nogales Fresh Produce Hub', city: 'Nogales', country: 'Estados Unidos', lat: 31.3404, lng: -110.9343, crops: ['Tomate', 'Pepino', 'Calabacita', 'Chile Jalapeño', 'Aguacate', 'Uva'], prices: { Tomate: 1.18, Pepino: 0.74, Calabacita: 0.88, 'Chile Jalapeño': 1.44, Aguacate: 2.11, Uva: 2.72 }, currency: 'USD', trend: 'up', trendValue: '+6.2%', localWeather: '26°C · Despejado' },
  { id: 22, name: 'Salinas Valley Distribution', city: 'Salinas', country: 'Estados Unidos', lat: 36.6744, lng: -121.6581, crops: ['Zanahoria', 'Cebolla', 'Brócoli', 'Fresa', 'Pepino'], prices: { Zanahoria: 0.79, Cebolla: 0.65, Brócoli: 1.42, Fresa: 3.18, Pepino: 0.69 }, currency: 'USD', trend: 'flat', trendValue: '+1.3%', localWeather: '19°C · Brisa marina' },
  { id: 23, name: 'Miami Hispanic Produce Market', city: 'Miami', country: 'Estados Unidos', lat: 25.7617, lng: -80.1918, crops: ['Mango', 'Plátano', 'Aguacate', 'Limón', 'Fresa', 'Tomate'], prices: { Mango: 1.52, Plátano: 0.66, Aguacate: 2.32, Limón: 1.29, Fresa: 3.25, Tomate: 1.16 }, currency: 'USD', trend: 'up', trendValue: '+5.1%', localWeather: '28°C · Húmedo' },
  { id: 24, name: 'Chicago International Produce', city: 'Chicago', country: 'Estados Unidos', lat: 41.8781, lng: -87.6298, crops: ['Papa', 'Cebolla', 'Maíz', 'Brócoli', 'Tomate', 'Uva'], prices: { Papa: 0.49, Cebolla: 0.63, Maíz: 0.43, Brócoli: 1.36, Tomate: 1.12, Uva: 2.54 }, currency: 'USD', trend: 'flat', trendValue: '+0.8%', localWeather: '16°C · Viento' },
  { id: 25, name: 'Yakima Fruit & Vegetable Exchange', city: 'Yakima', country: 'Estados Unidos', lat: 46.6021, lng: -120.5059, crops: ['Uva', 'Papa', 'Cebolla', 'Brócoli'], prices: { Uva: 2.48, Papa: 0.47, Cebolla: 0.61, Brócoli: 1.31 }, currency: 'USD', trend: 'up', trendValue: '+3.2%', localWeather: '14°C · Fresco' },
  { id: 26, name: 'Atlanta Southeast Produce Depot', city: 'Atlanta', country: 'Estados Unidos', lat: 33.7490, lng: -84.3880, crops: ['Fresa', 'Pepino', 'Calabacita', 'Papa', 'Tomate', 'Maíz'], prices: { Fresa: 3.12, Pepino: 0.67, Calabacita: 0.82, Papa: 0.50, Tomate: 1.09, Maíz: 0.45 }, currency: 'USD', trend: 'up', trendValue: '+2.9%', localWeather: '21°C · Parcialmente nublado' },
]

const colimaBuyers = [
  { id: 27, name: 'Acopio citrícola regional · referencia', city: 'Tecomán, Colima', country: 'México', state: 'Colima', lat: 18.9089, lng: -103.876, crops: ['Limón', 'Coco', 'Plátano', 'Mango', 'Papaya', 'Sandía', 'Melón', 'Chile verde', 'Tomate'], prices: { Limón: 6.4, Coco: 8.5, Plátano: 7, Mango: 13.5, Papaya: 9.5, Sandía: 5.8, Melón: 8.2, 'Chile verde': 15, Tomate: 14 }, currency: 'MXN', source: 'Precio de referencia; punto no verificado', trend: 'up', trendValue: '+3.2%', localWeather: '28°C · Cálido y húmedo' },
  { id: 28, name: 'Centro de acopio mixto · referencia', city: 'Armería, Colima', country: 'México', state: 'Colima', lat: 18.937, lng: -103.964, crops: ['Limón', 'Coco', 'Plátano', 'Sandía', 'Melón', 'Chile verde'], prices: { Limón: 5.9, Coco: 7.8, Plátano: 6.7, Sandía: 5.6, Melón: 7.9, 'Chile verde': 14.2 }, currency: 'MXN', source: 'Precio de referencia; punto no verificado', trend: 'flat', trendValue: '+1.8%', localWeather: '27°C · Cálido' },
  { id: 29, name: 'Comprador hortofrutícola · referencia', city: 'Manzanillo, Colima', country: 'México', state: 'Colima', lat: 19.052, lng: -104.315, crops: ['Limón', 'Coco', 'Plátano', 'Mango', 'Papaya'], prices: { Limón: 6.8, Coco: 9.2, Plátano: 7.5, Mango: 14.2, Papaya: 10.1 }, currency: 'MXN', source: 'Precio de referencia; punto no verificado', trend: 'up', trendValue: '+2.7%', localWeather: '29°C · Brisa marina' },
  { id: 30, name: 'Mercado regional · referencia', city: 'Colima, Colima', country: 'México', state: 'Colima', lat: 19.2433, lng: -103.725, crops: ['Limón', 'Mango', 'Papaya', 'Tomate', 'Chile verde', 'Coco'], prices: { Limón: 7.1, Mango: 13, Papaya: 10.4, Tomate: 15.2, 'Chile verde': 16, Coco: 8.9 }, currency: 'MXN', source: 'Precio de referencia; punto no verificado', trend: 'flat', trendValue: '+1.2%', localWeather: '26°C · Parcialmente nublado' },
]

const allCropPrices = Object.fromEntries(crops.map(({ name, price }) => [name, price]))
const allCropNames = crops.map(({ name }) => name)
const nationalReferenceBuyer = {
  id: 31,
  name: 'Central de Abasto Guadalajara · referencia',
  city: 'Guadalajara, Jalisco',
  country: 'México',
  state: 'Jalisco',
  lat: 20.6597,
  lng: -103.3496,
  crops: crops.map(({ name }) => name),
  prices: allCropPrices,
  currency: 'MXN',
  unit: 'kg',
  isReference: true,
  source: 'Estimación de mercado de referencia; comprador no verificado',
  trend: 'flat',
  trendValue: '+1.5%',
  localWeather: '24°C · Parcialmente nublado',
}

const universalMarketBuyerIds = new Set([5, 7, 10, 14, 16, 18, 19, 20])
const fillBuyerCatalog = (buyer, currency, conversionFactor = 1) => {
  const prices = Object.fromEntries(crops.map(({ name, price }) => [
    name,
    Number(((currency === 'USD' ? price / REFERENCE_MXN_PER_USD : price) * conversionFactor).toFixed(2)),
  ]))
  const providedPrices = currency === 'USD' && !buyer.currency
    ? Object.fromEntries(Object.entries(buyer.prices).map(([name, price]) => [
      name,
      Number((price / REFERENCE_MXN_PER_USD).toFixed(2)),
    ]))
    : buyer.prices
  return {
    ...buyer,
    crops: allCropNames,
    prices: { ...prices, ...providedPrices },
    currency,
    unit: buyer.unit ?? 'kg',
    isReference: buyer.isReference ?? true,
    source: buyer.source ?? 'Estimación de mercado de referencia; comprador no verificado',
    minimumVolume: buyer.minimumVolume ?? '100 kg (orientativo)',
    conditions: buyer.conditions ?? 'Recepción, calidad, cupo y entrega por confirmar; punto de referencia.',
  }
}

export const buyers = [
  ...rawBuyers.map((buyer) => {
    const currency = buyer.currency ?? (buyer.country === 'México' ? 'MXN' : 'USD')
    if (universalMarketBuyerIds.has(buyer.id)) {
      return fillBuyerCatalog(buyer, currency, buyer.currency === 'USD' ? 0.94 : 1)
    }
    const providedPrices = currency === 'USD' && !buyer.currency
      ? Object.fromEntries(Object.entries(buyer.prices).map(([name, price]) => [
        name,
        Number((price / REFERENCE_MXN_PER_USD).toFixed(2)),
      ]))
      : buyer.prices
    return {
      ...buyer,
      currency,
      unit: buyer.unit ?? 'kg',
      isReference: buyer.isReference ?? true,
      prices: providedPrices,
      source: buyer.source ?? 'Estimación de mercado de referencia; comprador no verificado',
      minimumVolume: buyer.minimumVolume ?? '100 kg (orientativo)',
      conditions: buyer.conditions ?? 'Recepción, calidad, cupo y entrega por confirmar; punto de referencia.',
    }
  }),
  ...colimaBuyers.map((buyer, index) => {
    const conversionFactor = [1, 0.96, 1.04, 1.08][index]
    const completedBuyer = fillBuyerCatalog(buyer, 'MXN', conversionFactor)
    return {
      ...completedBuyer,
      prices: { ...completedBuyer.prices, ...buyer.prices },
      source: buyer.source,
    }
  }),
  {
    ...nationalReferenceBuyer,
    minimumVolume: '200 kg (orientativo)',
    conditions: 'Recepción y especificación de producto por confirmar; punto de referencia.',
  },
  {
    ...fillBuyerCatalog({
      id: 32,
      name: 'Mercado regional Caribe · referencia',
      city: 'Santo Domingo, República Dominicana',
      country: 'Caribe',
      lat: 18.4861,
      lng: -69.9312,
      crops: allCropNames,
      prices: {},
      trend: 'flat',
      trendValue: '+1.4%',
      localWeather: '28°C · Tropical húmedo',
      source: 'Precio de referencia; punto no verificado',
      minimumVolume: '100 kg (orientativo)',
      conditions: 'Importación y recepción por confirmar; punto de referencia.',
    }, 'USD', 0.92),
  },
]
