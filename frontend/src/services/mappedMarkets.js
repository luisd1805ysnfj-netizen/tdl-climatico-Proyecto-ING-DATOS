const OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
const CACHE_DURATION_MS = 15 * 60 * 1000
const cache = new Map()

function validateCoordinates(latitude, longitude) {
  if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90 ||
      !Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
    throw new TypeError('Se requieren coordenadas válidas para buscar mercados mapeados')
  }
}

function cacheKey(latitude, longitude) {
  return `${latitude.toFixed(2)},${longitude.toFixed(2)}`
}

function normalizeElements(elements) {
  const locations = new Map()
  for (const element of elements) {
    const tags = element.tags ?? {}
    const latitude = element.lat ?? element.center?.lat
    const longitude = element.lon ?? element.center?.lon
    if (!tags.name || !['node', 'way', 'relation'].includes(element.type) ||
        !Number.isInteger(element.id) ||
        !Number.isFinite(latitude) || latitude < -90 || latitude > 90 ||
        !Number.isFinite(longitude) || longitude < -180 || longitude > 180) continue
    const category = tags.amenity === 'marketplace' ? 'Mercado mapeado' : 'Comercio mayorista mapeado'
    const id = `osm-${element.type}-${element.id}`
    locations.set(id, {
      id,
      name: tags.name,
      city: tags['addr:city'] ?? tags['addr:town'] ?? tags['addr:village'] ?? '',
      country: tags['addr:country_name'] ?? '',
      state: tags['addr:state'] ?? '',
      lat: latitude,
      lng: longitude,
      category,
      source: {
        name: 'OpenStreetMap / Overpass API',
        url: `https://www.openstreetmap.org/${element.type}/${element.id}`,
        license: 'Open Database License (ODbL)',
      },
      crops: [],
      prices: {},
      updatedAt: new Date().toISOString(),
      isMappedPlace: true,
    })
  }
  return [...locations.values()]
}

export async function getMappedMarkets(latitude, longitude, signal, forceRefresh = false) {
  validateCoordinates(latitude, longitude)
  const key = cacheKey(latitude, longitude)
  const cached = cache.get(key)
  if (!forceRefresh && cached && Date.now() - cached.cachedAt < CACHE_DURATION_MS) return cached.locations

  const query = `[out:json][timeout:20];(nwr["amenity"="marketplace"]["name"](around:40000,${latitude},${longitude});nwr["shop"="wholesale"]["name"](around:40000,${latitude},${longitude}););out center tags 50;`
  const controller = new AbortController()
  const abortRequest = () => controller.abort()
  signal?.addEventListener('abort', abortRequest, { once: true })
  const timeout = setTimeout(abortRequest, 25000)
  try {
    const response = await fetch(`${OVERPASS_URL}?data=${encodeURIComponent(query)}`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) throw new Error(`Overpass API respondió HTTP ${response.status}`)
    const payload = await response.json()
    if (!Array.isArray(payload.elements)) throw new Error('Overpass API devolvió una respuesta inválida')

    const locations = normalizeElements(payload.elements)
    cache.set(key, { locations, cachedAt: Date.now() })
    return locations
  } catch (error) {
    if (signal?.aborted) throw error
    if (controller.signal.aborted) throw new Error('Overpass API excedió el tiempo de consulta')
    throw error
  } finally {
    clearTimeout(timeout)
    signal?.removeEventListener('abort', abortRequest)
  }
}
