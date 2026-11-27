const monthNames = new Intl.DateTimeFormat('es', { month: 'short', timeZone: 'UTC' })

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))
const average = (values) => values.length
  ? values.reduce((sum, value) => sum + value, 0) / values.length
  : null

function monthLabel(date) {
  const label = monthNames.format(date).replace('.', '')
  return label.charAt(0).toUpperCase() + label.slice(1)
}

function seasonalBaseline(latitude, month) {
  const warmestMonth = latitude < 0 ? 1 : 7
  const radians = (2 * Math.PI * (month - warmestMonth)) / 12
  const seasonalAmplitude = clamp(Math.abs(latitude) * 0.22, 1, 11)
  return 27 - Math.min(Math.abs(latitude), 55) * 0.32 + seasonalAmplitude * Math.cos(radians)
}

function fallbackOutlook(latitude, humidity, currentTemperature) {
  const now = new Date()
  return Array.from({ length: 5 }, (_, index) => {
    const date = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + index, 1))
    const month = date.getUTCMonth() + 1
    const historical = seasonalBaseline(latitude, month)
    const currentBias = clamp(currentTemperature - seasonalBaseline(latitude, now.getUTCMonth() + 1), -3, 3)
    const forecast = historical + currentBias * (1 - index * 0.13)
    return {
      month: monthLabel(date),
      historico: Math.round(historical * 10) / 10,
      predicción: Math.round(forecast * 10) / 10,
      humedad: Math.round(clamp(humidity + 7 * Math.sin((month / 12) * 2 * Math.PI), 35, 95)),
      lluvia: null,
    }
  })
}

function describeClimate(latitude, temperature, humidity) {
  const winterMonths = latitude < 0 ? [5, 6, 7] : [11, 0, 1]
  const summerMonths = latitude < 0 ? [11, 0, 1] : [5, 6, 7]
  const month = new Date().getUTCMonth()
  if (temperature < 12 && humidity < 55) return 'Frío y seco'
  if (humidity >= 75 && temperature >= 22) return 'Tropical húmedo'
  if (temperature < 16 && humidity >= 65) return 'Frío y húmedo'
  if (humidity < 50 && temperature >= 25) return 'Cálido y seco'
  if (winterMonths.includes(month) && temperature < 20) return 'Invierno templado'
  if (summerMonths.includes(month) && temperature >= 22) return 'Verano cálido'
  return 'Templado y estable'
}

export function createFallbackClimateOutlook(latitude, fallback) {
  const temperature = fallback?.temperature ?? seasonalBaseline(latitude, new Date().getUTCMonth() + 1)
  const humidity = fallback?.humidity ?? clamp(68 - Math.abs(latitude) * 0.2, 45, 80)
  const chart = fallbackOutlook(latitude, humidity, temperature)
  const temps = chart.map((item) => item.predicción)
  return {
    chart,
    range: `${Math.round(Math.min(...temps))}° — ${Math.round(Math.max(...temps))}°C`,
    summary: describeClimate(latitude, average(temps), humidity),
    humidity: Math.round(humidity),
    current: fallback ?? null,
    source: 'Estimación estacional por latitud (sin conexión)',
    isFallback: true,
  }
}

async function fetchJson(url, signal) {
  const response = await fetch(url, { signal })
  if (!response.ok) throw new Error(`Open-Meteo respondió HTTP ${response.status}`)
  return response.json()
}

async function fetchCurrentWeather(latitude, longitude, signal) {
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    timezone: 'auto',
    current: 'temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,apparent_temperature,weather_code',
  })
  const result = await fetchJson(`https://api.open-meteo.com/v1/forecast?${params}`, signal)
  const current = result.current
  if (!current) throw new Error('Open-Meteo no devolvió condiciones actuales')
  return {
    temperature: Math.round(current.temperature_2m),
    humidity: Math.round(current.relative_humidity_2m),
    rain: Math.round(current.precipitation * 10) / 10,
    wind: Math.round(current.wind_speed_10m),
    feels: Math.round(current.apparent_temperature),
    condition: describeWeatherCode(current.weather_code),
  }
}

function describeWeatherCode(code) {
  if ([0].includes(code)) return 'Despejado'
  if ([1, 2].includes(code)) return 'Parcialmente nublado'
  if ([3].includes(code)) return 'Nublado'
  if ([45, 48].includes(code)) return 'Neblina'
  if ([51, 53, 55, 56, 57].includes(code)) return 'Llovizna'
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return 'Lluvia'
  if ([71, 73, 75, 77, 85, 86].includes(code)) return 'Nieve'
  if ([95, 96, 99].includes(code)) return 'Tormenta'
  return 'Condiciones variables'
}

export async function getClimateOutlook({ latitude, longitude, fallback }, signal) {
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    throw new TypeError('Se requieren coordenadas válidas para consultar el clima')
  }

  const today = new Date()
  const endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - 2))
  const startDate = new Date(Date.UTC(endDate.getUTCFullYear() - 4, 0, 1))
  const formatDate = (date) => date.toISOString().slice(0, 10)
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    timezone: 'auto',
    daily: 'temperature_2m_mean,precipitation_sum',
    hourly: 'relative_humidity_2m',
    start_date: formatDate(startDate),
    end_date: formatDate(endDate),
  })

  try {
    const [history, current] = await Promise.all([
      fetchJson(`https://archive-api.open-meteo.com/v1/archive?${params}`, signal),
      fetchCurrentWeather(latitude, longitude, signal).catch((error) => {
        if (error.name === 'AbortError') throw error
        return fallback ?? null
      }),
    ])
    const daily = history.daily
    if (!daily?.time?.length || !daily.temperature_2m_mean?.length) throw new Error('Open-Meteo no devolvió serie histórica')

    const now = new Date()
    const months = Array.from({ length: 5 }, (_, index) => new Date(Date.UTC(
      now.getUTCFullYear(), now.getUTCMonth() + index, 1,
    )))
    const outlook = months.map((date, index) => {
      const month = date.getUTCMonth() + 1
      const historicalValues = daily.time.reduce((values, day, i) => {
        const parsed = new Date(`${day}T00:00:00Z`)
        if (parsed.getUTCMonth() + 1 === month && Number.isFinite(daily.temperature_2m_mean[i])) {
          values.push(daily.temperature_2m_mean[i])
        }
        return values
      }, [])
      const historicalMean = average(historicalValues) ?? seasonalBaseline(latitude, month)
      const currentBias = current?.temperature == null
        ? 0
        : clamp(current.temperature - seasonalBaseline(latitude, now.getUTCMonth() + 1), -3, 3)
      const historicalHumidity = average((daily.hourly?.time ?? []).reduce((values, hour, i) => {
        if (Number(hour.slice(5, 7)) === month &&
            Number.isFinite(daily.hourly.relative_humidity_2m[i])) {
          values.push(daily.hourly.relative_humidity_2m[i])
        }
        return values
      }, [])) ?? current?.humidity ?? 65
      const currentMonthHumidity = average((daily.hourly?.time ?? []).reduce((values, hour, i) => {
        if (Number(hour.slice(5, 7)) === now.getUTCMonth() + 1 &&
            Number.isFinite(daily.hourly.relative_humidity_2m[i])) {
          values.push(daily.hourly.relative_humidity_2m[i])
        }
        return values
      }, [])) ?? current?.humidity ?? historicalHumidity
      const humidityBias = current?.humidity == null ? 0 : current.humidity - currentMonthHumidity
      return {
        month: monthLabel(date),
        historico: Math.round(historicalMean * 10) / 10,
        predicción: Math.round((historicalMean + currentBias * (1 - index * 0.13)) * 10) / 10,
        humedad: Math.round(clamp(historicalHumidity + humidityBias * (1 - index * 0.13), 35, 95)),
        lluvia: average(daily.time.reduce((values, day, i) => {
          if (new Date(`${day}T00:00:00Z`).getUTCMonth() + 1 === month &&
              Number.isFinite(daily.precipitation_sum?.[i])) values.push(daily.precipitation_sum[i])
          return values
        }, [])),
      }
    })

    const temps = outlook.map((item) => item.predicción)
    const humidity = average(outlook.map((item) => item.humedad)) ?? current?.humidity ?? 65
    return {
      chart: outlook,
      range: `${Math.round(Math.min(...temps))}° — ${Math.round(Math.max(...temps))}°C`,
      summary: describeClimate(latitude, average(temps), humidity),
      humidity: Math.round(humidity),
      current: current ?? fallback,
      source: 'Open-Meteo Archive · normal estacional de 5 años',
      isFallback: false,
    }
  } catch (error) {
    if (error.name === 'AbortError') throw error
    let current = fallback
    try {
      current = await fetchCurrentWeather(latitude, longitude, signal)
    } catch (currentError) {
      if (currentError.name === 'AbortError') throw currentError
    }
    return createFallbackClimateOutlook(latitude, current)
  }
}
