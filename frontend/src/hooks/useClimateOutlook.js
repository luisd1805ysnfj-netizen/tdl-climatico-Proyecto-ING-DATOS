import { useCallback, useEffect, useState } from 'react'
import { getClimateOutlook } from '../services/openMeteo'

export function useClimateOutlook(location) {
  const [result, setResult] = useState({ requestKey: '', outlook: null, error: '' })
  const [refreshKey, setRefreshKey] = useState(0)
  const refresh = useCallback(() => setRefreshKey((value) => value + 1), [])
  const latitude = location?.latitude
  const longitude = location?.longitude
  const requestKey = Number.isFinite(latitude) && Number.isFinite(longitude)
    ? `${latitude},${longitude}:${refreshKey}`
    : ''

  useEffect(() => {
    if (!requestKey) return undefined

    const controller = new AbortController()
    getClimateOutlook({ latitude, longitude }, controller.signal)
      .then((outlook) => setResult({ requestKey, outlook, error: '' }))
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') {
          setResult({
            requestKey,
            outlook: null,
            error: requestError instanceof Error ? requestError.message : String(requestError),
          })
        }
      })

    return () => controller.abort()
  }, [latitude, longitude, requestKey])

  const isCurrentRequest = result.requestKey === requestKey
  return {
    outlook: isCurrentRequest ? result.outlook : null,
    loading: Boolean(requestKey) && !isCurrentRequest,
    error: isCurrentRequest ? result.error : '',
    refresh,
  }
}
