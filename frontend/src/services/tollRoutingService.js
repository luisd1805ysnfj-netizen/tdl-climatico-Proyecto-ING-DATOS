const TOLLGURU_PROXY_URL = '/api/route-tolls'
const OSRM_ROUTING_URL = 'https://router.project-osrm.org/route/v1/driving'

function validatePoint(point, label) {
  if (!Array.isArray(point) || point.length !== 2 ||
      !Number.isFinite(point[0]) || !Number.isFinite(point[1]) ||
      point[0] < -90 || point[0] > 90 || point[1] < -180 || point[1] > 180) {
    throw new TypeError(`${label} requiere coordenadas válidas [latitud, longitud]`)
  }
}

function decodePolyline(encodedPolyline) {
  if (typeof encodedPolyline !== 'string' || encodedPolyline.length === 0) {
    throw new Error('El proveedor no devolvió la geometría de una ruta')
  }
  const coordinates = []
  let index = 0
  let latitude = 0
  let longitude = 0
  const readDelta = () => {
    let result = 0
    let shift = 0
    let byte
    do {
      if (index >= encodedPolyline.length || shift > 30) {
        throw new Error('El proveedor devolvió una geometría de ruta inválida')
      }
      byte = encodedPolyline.charCodeAt(index++) - 63
      if (byte < 0 || byte > 63) throw new Error('El proveedor devolvió una geometría de ruta inválida')
      result |= (byte & 0x1f) << shift
      shift += 5
    } while (byte >= 0x20)
    return result & 1 ? ~(result >> 1) : result >> 1
  }

  while (index < encodedPolyline.length) {
    latitude += readDelta()
    longitude += readDelta()
    coordinates.push([latitude / 1e5, longitude / 1e5])
  }
  return coordinates
}

function normalizeToll(toll, index, routeCurrency) {
  if (!Number.isFinite(toll.lat) || !Number.isFinite(toll.lng)) return null
  const priceOptions = [
    ['cashCost', 'Efectivo'],
    ['tagPriCost', 'Tag preferente'],
    ['tagCost', 'Tag'],
    ['tagSecCost', 'Tag secundario'],
    ['prepaidCardCost', 'Tarjeta prepago'],
    ['licensePlateCost', 'Placa'],
  ]
  const priceOption = priceOptions.find(([key]) => Number.isFinite(toll[key]))
  return {
    id: toll.id ?? `${toll.name ?? 'caseta'}-${index}`,
    name: toll.name || 'Nombre no proporcionado por la API',
    road: toll.road || 'Carretera no especificada',
    latitude: toll.lat,
    longitude: toll.lng,
    price: priceOption ? toll[priceOption[0]] : null,
    paymentMethod: priceOption?.[1] ?? null,
    currency: toll.currency || routeCurrency || null,
    isCongestionZone: toll.isCongestionZone === true,
  }
}

function normalizeTollGuruRoute(route, index, routeCurrency, origin, destination) {
  const coordinates = decodePolyline(route.polyline)
  const distanceMeters = route.summary?.distance?.value
  const durationSeconds = route.summary?.duration?.value
  if (coordinates.length < 2 || coordinates.some((point) => point.some((value) => !Number.isFinite(value))) ||
      !Number.isFinite(distanceMeters) || !Number.isFinite(durationSeconds)) {
    throw new Error('TollGuru devolvió datos incompletos para una ruta')
  }

  const trafficSeconds = route.summary?.durationInTraffic?.value
  const tolls = (route.tolls ?? [])
    .map((toll, tollIndex) => normalizeToll(toll, tollIndex, routeCurrency))
    .filter(Boolean)
  const cashTotal = route.costs?.cash
  const minimumTotal = route.costs?.minimumTollCost
  const totalAmount = Number.isFinite(cashTotal)
    ? cashTotal
    : Number.isFinite(minimumTotal)
      ? minimumTotal
      : route.summary?.hasTolls === false ? 0 : null

  return {
    id: `tollguru-${index}`,
    origin,
    destination,
    coordinates,
    distanceKm: distanceMeters / 1000,
    durationSeconds,
    trafficSeconds: Number.isFinite(trafficSeconds) ? trafficSeconds : null,
    tolls,
    tollTotal: Number.isFinite(totalAmount)
      ? {
          amount: totalAmount,
          currency: routeCurrency || tolls[0]?.currency || null,
          paymentMethod: Number.isFinite(cashTotal) ? 'Efectivo' : 'menor tarifa informada',
        }
      : null,
    name: route.summary?.name || `Ruta ${index + 1}`,
  }
}

function normalizeTollGuruResponse(data, origin, destination) {
  if (!data || typeof data !== 'object') {
    throw new Error('El proxy devolvió una respuesta inválida')
  }
  if (typeof data.status !== 'string' || data.status.toLowerCase() !== 'ok' ||
      !Array.isArray(data.routes) || data.routes.length === 0) {
    throw new Error('TollGuru no encontró rutas viables')
  }

  const currency = data.summary?.currency ?? null
  const routes = data.routes
    .map((route, index) => normalizeTollGuruRoute(route, index, currency, origin, destination))
    .sort((a, b) => (a.trafficSeconds ?? a.durationSeconds) - (b.trafficSeconds ?? b.durationSeconds))
  const fastest = routes[0]
  const alternatives = routes.slice(1).sort((a, b) =>
    (a.tollTotal?.amount ?? Number.POSITIVE_INFINITY) -
    (b.tollTotal?.amount ?? Number.POSITIVE_INFINITY),
  )
  const selectedRoutes = [fastest, ...alternatives].slice(0, 2)

  if (selectedRoutes[1]) {
    selectedRoutes[1].selectionLabel =
      selectedRoutes[1].tollTotal && fastest.tollTotal &&
      selectedRoutes[1].tollTotal.currency === fastest.tollTotal.currency &&
      selectedRoutes[1].tollTotal.amount < fastest.tollTotal.amount
        ? 'Alternativa · menor peaje'
        : 'Ruta alternativa'
  }

  return {
    mode: 'api',
    provider: 'TollGuru',
    queriedAt: data.queriedAt || new Date().toISOString(),
    trafficAvailable: selectedRoutes.some((route) => route.trafficSeconds !== null),
    routes: selectedRoutes.map((route, index) => ({
      ...route,
      selectionLabel: index === 0 ? 'Principal · más rápida' : route.selectionLabel,
    })),
    fallbackNotice: '',
  }
}

async function getOsrmAlternatives(origin, destination, vehicleType, signal, reason) {
  const coordinates = `${origin[1]},${origin[0]};${destination[1]},${destination[0]}`
  const params = new URLSearchParams({
    alternatives: '2',
    overview: 'full',
    geometries: 'geojson',
    steps: 'false',
  })
  const response = await fetch(`${OSRM_ROUTING_URL}/${coordinates}?${params}`, { signal })
  if (!response.ok) throw new Error(`OSRM respondió HTTP ${response.status}`)
  const result = await response.json()
  if (result.code !== 'Ok' || !Array.isArray(result.routes) || result.routes.length === 0) {
    throw new Error('OSRM no encontró rutas viables entre el origen y el destino')
  }

  const routes = result.routes
    .filter((route) => route.geometry?.coordinates?.length &&
      Number.isFinite(route.distance) && Number.isFinite(route.duration))
    .sort((a, b) => a.duration - b.duration)
    .slice(0, 2)
    .map((route, index) => ({
      id: `osrm-${index}`,
      name: index === 0 ? 'Ruta principal' : 'Ruta alternativa',
      selectionLabel: index === 0 ? 'Principal · más rápida' : 'Ruta alternativa',
      origin,
      destination,
      coordinates: route.geometry.coordinates.map(([longitude, latitude]) => [latitude, longitude]),
      distanceKm: route.distance / 1000,
      durationSeconds: route.duration,
      trafficSeconds: null,
      tolls: [],
      tollTotal: null,
      currency: null,
    }))

  if (routes.length === 0) throw new Error('OSRM no devolvió geometrías de ruta válidas')
  return {
    mode: 'simulation',
    provider: 'OSRM público',
    queriedAt: new Date().toISOString(),
    trafficAvailable: false,
    routes,
    fallbackNotice: `Modo simulación: ${reason} Configura TOLLGURU_API_KEY en el proxy /api/route-tolls para consultar tráfico y tarifas de casetas en tiempo real.`,
    vehicleType,
  }
}

export async function getRouteAlternatives(
  origin,
  destination,
  { vehicleType = '2AxlesAuto', signal } = {},
) {
  validatePoint(origin, 'El origen')
  validatePoint(destination, 'El destino')
  if (!['2AxlesAuto', '3AxlesTruck'].includes(vehicleType)) {
    throw new TypeError('Selecciona un perfil de vehículo compatible')
  }

  try {
    const response = await fetch(TOLLGURU_PROXY_URL, {
      method: 'POST',
      signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        origin: { lat: origin[0], lng: origin[1] },
        destination: { lat: destination[0], lng: destination[1] },
        vehicleType,
      }),
    })
    const data = await response.json()
    if (!response.ok) {
      const message = typeof data?.error === 'string'
        ? data.error
        : `El proxy de TollGuru respondió HTTP ${response.status}`
      throw new Error(message)
    }
    return normalizeTollGuruResponse(data, origin, destination)
  } catch (error) {
    if (error.name === 'AbortError') throw error
    return getOsrmAlternatives(origin, destination, vehicleType, signal, error.message)
  }
}
