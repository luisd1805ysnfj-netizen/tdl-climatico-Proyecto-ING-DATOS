import { useCallback, useEffect, useRef, useState } from 'react'
import { crops } from '../data/agtechData'

const cropNames = new Set(crops.map(({ name }) => name))
const unavailableMessage = 'Dato no disponible / Pendiente de conexión a API oficial'

function parseTimestamp(value, label) {
  if (typeof value !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}T/.test(value) ||
      Number.isNaN(Date.parse(value))) {
    throw new Error(`${label} debe ser una fecha ISO válida`)
  }
  return value
}

function validateSource(source) {
  if (!source || typeof source !== 'object' ||
      typeof source.name !== 'string' || !source.name.trim() ||
      typeof source.url !== 'string' || typeof source.license !== 'string' || !source.license.trim()) {
    throw new Error('La API debe declarar source.name, source.url y source.license')
  }
  let url
  try {
    url = new URL(source.url)
  } catch {
    throw new Error('source.url debe ser una URL HTTPS válida')
  }
  if (url.protocol !== 'https:') throw new Error('source.url debe usar HTTPS')
  return {
    name: source.name.trim(),
    url: url.toString(),
    license: source.license.trim(),
  }
}

function normalizeQuote(cropName, quote, sourceDate) {
  if (!cropNames.has(cropName)) {
    throw new Error(`Cultivo no reconocido en la respuesta de precios: "${cropName}"`)
  }
  if (!quote || typeof quote !== 'object' ||
      typeof quote.price !== 'number' || !Number.isFinite(quote.price) || quote.price < 0 ||
      !['MXN', 'USD'].includes(quote.currency) ||
      typeof quote.unit !== 'string' || !quote.unit.trim()) {
    throw new Error(`Cotización inválida para "${cropName}": se requiere price, currency MXN/USD y unit`)
  }
  return {
    price: quote.price,
    currency: quote.currency,
    unit: quote.unit.trim(),
    region: typeof quote.region === 'string' && quote.region.trim() ? quote.region.trim() : null,
    updatedAt: quote.updatedAt ? parseTimestamp(quote.updatedAt, `updatedAt de "${cropName}"`) : sourceDate,
  }
}

function normalizeQuotes(value, sourceDate) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Las cotizaciones deben ser un objeto indexado por cultivo')
  }
  return Object.fromEntries(
    Object.entries(value).map(([cropName, quote]) => [
      cropName,
      normalizeQuote(cropName, quote, sourceDate),
    ]),
  )
}

function normalizeBuyers(value, source, updatedAt) {
  if (value === undefined) return []
  if (!Array.isArray(value)) throw new Error('buyers debe ser una lista')
  return value.map((buyer, index) => {
    if (!buyer || typeof buyer !== 'object' ||
        (typeof buyer.id !== 'string' && typeof buyer.id !== 'number') ||
        typeof buyer.name !== 'string' || !buyer.name.trim() ||
        typeof buyer.city !== 'string' || !buyer.city.trim() ||
        typeof buyer.country !== 'string' || !buyer.country.trim() ||
        !Number.isFinite(buyer.lat) || buyer.lat < -90 || buyer.lat > 90 ||
        !Number.isFinite(buyer.lng) || buyer.lng < -180 || buyer.lng > 180 ||
        !Array.isArray(buyer.crops)) {
      throw new Error(`Comprador inválido en la posición ${index + 1}`)
    }
    const buyerCrops = [...new Set(buyer.crops)]
    if (buyerCrops.some((cropName) => !cropNames.has(cropName))) {
      throw new Error(`El comprador "${buyer.name}" incluye cultivos no reconocidos`)
    }
    return {
      id: buyer.id,
      name: buyer.name.trim(),
      city: buyer.city.trim(),
      country: buyer.country.trim(),
      state: typeof buyer.state === 'string' ? buyer.state.trim() : '',
      lat: buyer.lat,
      lng: buyer.lng,
      crops: buyerCrops,
      prices: normalizeQuotes(buyer.prices ?? {}, updatedAt),
      minimumOrder: typeof buyer.minimumOrder === 'string' && buyer.minimumOrder.trim()
        ? buyer.minimumOrder.trim()
        : null,
      deliveryTerms: typeof buyer.deliveryTerms === 'string' && buyer.deliveryTerms.trim()
        ? buyer.deliveryTerms.trim()
        : null,
      trend30Days: typeof buyer.trend30Days === 'string' && buyer.trend30Days.trim()
        ? buyer.trend30Days.trim()
        : null,
      localClimate: typeof buyer.localClimate === 'string' && buyer.localClimate.trim()
        ? buyer.localClimate.trim()
        : null,
      source,
      updatedAt: buyer.updatedAt ? parseTimestamp(buyer.updatedAt, `updatedAt de "${buyer.name}"`) : updatedAt,
    }
  })
}

function formatLastUpdate(timestamp) {
  if (!timestamp) return unavailableMessage
  return new Intl.DateTimeFormat('es-MX', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(timestamp))
}

function getPricesEndpoint(endpoint) {
  const normalized = endpoint.trim().replace(/\/+$/, '')
  if (!normalized) throw new Error('VITE_MARKET_PRICES_API no puede estar vacía')
  const url = new URL(normalized, window.location.origin)
  const isLocalDevelopment = url.hostname === 'localhost'
  if (url.protocol !== 'https:' && !(isLocalDevelopment && url.protocol === 'http:')) {
    throw new Error('La API de precios debe usar HTTPS fuera del entorno local')
  }
  return normalized.endsWith('/prices') ? normalized : `${normalized}/prices`
}

export function useMarketPricesAPI() {
  const [prices, setPrices] = useState({})
  const [buyers, setBuyers] = useState([])
  const [source, setSource] = useState(null)
  const [lastUpdate, setLastUpdate] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [connected, setConnected] = useState(false)
  const requestController = useRef(null)
  const endpoint = import.meta.env.VITE_MARKET_PRICES_API

  const refresh = useCallback(async () => {
    if (!endpoint) return
    requestController.current?.abort()
    const controller = new AbortController()
    requestController.current = controller
    setError('')
    setLoading(true)
    try {
      const response = await fetch(getPricesEndpoint(endpoint), { signal: controller.signal })
      if (!response.ok) throw new Error(`La API de precios respondió HTTP ${response.status}`)
      const payload = await response.json()
      const sourceInfo = validateSource(payload.source)
      const updatedAt = parseTimestamp(payload.updatedAt, 'updatedAt')
      const apiPrices = normalizeQuotes(payload.prices ?? {}, updatedAt)
      const apiBuyers = normalizeBuyers(payload.buyers, sourceInfo, updatedAt)
      if (controller.signal.aborted) return

      setPrices(apiPrices)
      setBuyers(apiBuyers)
      setSource(sourceInfo)
      setLastUpdate(updatedAt)
      setConnected(true)
    } catch (requestError) {
      if (requestError.name !== 'AbortError' && !controller.signal.aborted) {
        setPrices({})
        setBuyers([])
        setSource(null)
        setLastUpdate('')
        setConnected(false)
        setError(requestError instanceof Error ? requestError.message : String(requestError))
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false)
        requestController.current = null
      }
    }
  }, [endpoint])

  useEffect(() => {
    let active = true
    Promise.resolve().then(() => {
      if (active) refresh()
    })
    return () => {
      active = false
      requestController.current?.abort()
    }
  }, [refresh])

  const priceRecords = Object.entries(prices).map(([crop, quote]) => ({
    crop,
    ...quote,
  }))

  return {
    prices,
    priceRecords,
    buyers,
    source,
    loading,
    lastUpdate,
    lastUpdateLabel: formatLastUpdate(lastUpdate),
    refresh,
    error,
    connected,
    isConfigured: Boolean(endpoint),
    unavailableMessage,
  }
}
