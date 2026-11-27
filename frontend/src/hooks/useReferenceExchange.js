import { useCallback, useEffect, useState } from 'react'
import { getReferenceExchangeRate } from '../services/referenceExchange'

export function useReferenceExchange() {
  const [rate, setRate] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async (signal) => {
    setLoading(true)
    setError('')
    try {
      const result = await getReferenceExchangeRate(signal)
      if (!signal?.aborted) setRate(result)
    } catch (requestError) {
      if (requestError.name !== 'AbortError' && !signal?.aborted) {
        setRate(null)
        setError(requestError instanceof Error ? requestError.message : String(requestError))
      }
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    Promise.resolve().then(() => refresh(controller.signal))
    return () => controller.abort()
  }, [refresh])

  return { rate, loading, error, refresh }
}
