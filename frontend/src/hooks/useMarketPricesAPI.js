import { useState } from 'react'
import { crops } from '../data/agtechData'

const simulatedPrices = Object.fromEntries(
  crops.map(({ name, price }) => [name, { price, currency: 'MXN', unit: 'kg' }]),
)

const formatLastUpdate = () => new Intl.DateTimeFormat('es-MX', {
  day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
}).format(new Date())

export function useMarketPricesAPI() {
  const [prices, setPrices] = useState(simulatedPrices)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(formatLastUpdate)
  const [error, setError] = useState('')
  const [connected, setConnected] = useState(false)

  const refresh = async () => {
    setLoading(true)
    setError('')
    try {
      const endpoint = import.meta.env.VITE_MARKET_PRICES_API
      if (endpoint) {
        const response = await fetch(`${endpoint.replace(/\/$/, '')}/prices`)
        if (!response.ok) throw new Error(`Error al consultar precios: ${response.status}`)
        const payload = await response.json()
        if (!payload.prices || typeof payload.prices !== 'object') {
          throw new Error('La API de precios debe responder con un objeto "prices".')
        }
        const apiPrices = Object.fromEntries(Object.entries(payload.prices).map(([name, quote]) => {
          if (
            !quote ||
            typeof quote.price !== 'number' ||
            !Number.isFinite(quote.price) ||
            quote.price < 0 ||
            !['MXN', 'USD'].includes(quote.currency) ||
            quote.unit !== 'kg'
          ) {
            throw new Error(`Precio inválido para "${name}": se requiere price numérico, currency MXN/USD y unit "kg".`)
          }
          return [name, quote]
        }))
        setPrices({ ...simulatedPrices, ...apiPrices })
        setLastUpdate(formatLastUpdate())
        setConnected(true)
      }
    } catch (requestError) {
      setConnected(false)
      setError(requestError instanceof Error ? requestError.message : String(requestError))
    } finally {
      setLoading(false)
    }
  }

  return {
    prices,
    loading,
    lastUpdate,
    refresh,
    error,
    connected,
    isLive: Boolean(import.meta.env.VITE_MARKET_PRICES_API),
  }
}
