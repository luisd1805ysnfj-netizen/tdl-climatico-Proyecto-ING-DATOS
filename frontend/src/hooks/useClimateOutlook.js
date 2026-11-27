import { useEffect, useState } from 'react'
import { getClimateOutlook } from '../services/openMeteo'

export function useClimateOutlook(location, fallback) {
  const [outlook, setOutlook] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!location) return undefined
    const controller = new AbortController()
    setOutlook(null)
    setLoading(true)
    getClimateOutlook({ ...location, fallback }, controller.signal)
      .then(setOutlook)
      .catch((error) => {
        if (error.name !== 'AbortError') console.error('Error al consultar tendencia climática:', error)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [location?.latitude, location?.longitude, fallback?.temperature, fallback?.humidity])

  return { outlook, loading }
}
