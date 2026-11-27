const TOLLGURU_URL = 'https://apis.tollguru.com/toll/v2/origin-destination-waypoints'
const allowedVehicleTypes = new Set(['2AxlesAuto', '3AxlesTruck'])

const jsonResponse = (status, data) => new Response(JSON.stringify(data), {
  status,
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
})

const validPoint = (point) =>
  point && Number.isFinite(point.lat) && Number.isFinite(point.lng) &&
  point.lat >= -90 && point.lat <= 90 && point.lng >= -180 && point.lng <= 180

export async function handleRouteTollsRequest(request) {
  if (request.method !== 'POST') {
    return jsonResponse(405, { error: 'El método debe ser POST.' })
  }

  const originHeader = request.headers.get('origin')
  if (!originHeader) return jsonResponse(403, { error: 'La solicitud debe originarse en la aplicación web.' })
  try {
    if (new URL(originHeader).origin !== new URL(request.url).origin) {
      return jsonResponse(403, { error: 'Origen de solicitud no permitido.' })
    }
  } catch {
    return jsonResponse(403, { error: 'Origen de solicitud inválido.' })
  }

  let input
  try {
    input = await request.json()
  } catch {
    return jsonResponse(400, { error: 'El cuerpo debe ser JSON válido.' })
  }

  const origin = input?.origin
  const destination = input?.destination
  const vehicleType = input?.vehicleType
  if (!validPoint(origin) || !validPoint(destination) || !allowedVehicleTypes.has(vehicleType)) {
    return jsonResponse(400, { error: 'Origen, destino o tipo de vehículo inválido.' })
  }

  const apiKey = process.env.TOLLGURU_API_KEY
  if (!apiKey) {
    return jsonResponse(503, { error: 'Configura TOLLGURU_API_KEY como secreto del servicio proxy.' })
  }

  let upstream
  try {
    upstream = await fetch(TOLLGURU_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
      },
      body: JSON.stringify({
        from: { lat: origin.lat, lng: origin.lng },
        to: { lat: destination.lat, lng: destination.lng },
        waypoints: [],
        serviceProvider: 'gmaps',
        vehicle: { type: vehicleType },
        directionsFlag: true,
        departure_time: new Date().toISOString(),
      }),
      signal: AbortSignal.timeout(20000),
    })
  } catch (error) {
    const message = error.name === 'TimeoutError'
      ? 'TollGuru tardó demasiado en responder.'
      : 'No se pudo conectar con TollGuru.'
    return jsonResponse(502, { error: message })
  }

  let data
  try {
    data = await upstream.json()
  } catch {
    return jsonResponse(502, { error: 'TollGuru devolvió una respuesta inválida.' })
  }
  if (!upstream.ok) {
    return jsonResponse(502, { error: `TollGuru respondió HTTP ${upstream.status}.` })
  }
  if (typeof data.status !== 'string' || data.status.toLowerCase() !== 'ok' ||
      !Array.isArray(data.routes) || data.routes.length === 0) {
    return jsonResponse(502, { error: 'TollGuru no devolvió rutas viables para este trayecto.' })
  }

  return jsonResponse(200, {
    ...data,
    queriedAt: new Date().toISOString(),
  })
}
