import { useCallback, useEffect, useRef, useState } from 'react'
import { getMappedMarkets } from '../services/mappedMarkets'

export function useMappedMarkets(location) {
  const [result, setResult] = useState({ key: '', locations: [], loading: false, error: '', queriedAt: '' })
  const [refreshKey, setRefreshKey] = useState(0)
  const handledRefreshKey = useRef(0)
  const refresh = useCallback(() => setRefreshKey((value) => value + 1), [])
  const latitude = location?.latitude
  const longitude = location?.longitude
  const requestKey = Number.isFinite(latitude) && Number.isFinite(longitude)
    ? `${latitude.toFixed(4)},${longitude.toFixed(4)}`
    : ''

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    Promise.resolve().then(async () => {
      if (controller.signal.aborted) return
      setResult((previous) => ({ ...previous, key: requestKey, loading: true, error: '' }))
      try {
        const forceRefresh = refreshKey > handledRefreshKey.current
        const locations = await getMappedMarkets(latitude, longitude, controller.signal, forceRefresh)
        if (!controller.signal.aborted) {
          handledRefreshKey.current = refreshKey
          setResult({ key: requestKey, locations, loading: false, error: '', queriedAt: new Date().toISOString() })
        }
      } catch (error) {
        if (error.name !== 'AbortError' && !controller.signal.aborted) {
          handledRefreshKey.current = refreshKey
          setResult({ key: requestKey, locations: [], loading: false, error: error.message, queriedAt: '' })
        }
      }
    })
    return () => controller.abort()
  }, [latitude, longitude, requestKey, refreshKey])

  return requestKey === result.key
    ? { ...result, refresh }
    : { ...result, locations: [], loading: Boolean(requestKey), error: '', queriedAt: '', refresh }
}
