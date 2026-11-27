import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchCropRequirements } from '../services/cropRequirements'

export function useCropRequirements() {
  const [result, setResult] = useState({ data: null, error: '', loading: false })
  const requestController = useRef(null)
  const endpoint = import.meta.env.VITE_CROP_REQUIREMENTS_API

  const refresh = useCallback(async () => {
    if (!endpoint) {
      setResult({ data: null, error: '', loading: false })
      return
    }
    requestController.current?.abort()
    const controller = new AbortController()
    requestController.current = controller
    setResult((previous) => ({ ...previous, error: '', loading: true }))
    try {
      const data = await fetchCropRequirements(endpoint, controller.signal)
      if (!controller.signal.aborted) setResult({ data, error: '', loading: false })
    } catch (error) {
      if (error.name !== 'AbortError' && !controller.signal.aborted) {
        setResult({
          data: null,
          error: error instanceof Error ? error.message : String(error),
          loading: false,
        })
      }
    } finally {
      if (!controller.signal.aborted) requestController.current = null
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

  return { ...result, refresh, isConfigured: Boolean(endpoint) }
}
