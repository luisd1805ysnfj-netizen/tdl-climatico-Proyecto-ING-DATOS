const CURRENT_URL = 'https://api.open-meteo.com/v1/forecast'
const SEASONAL_URL = 'https://seasonal-api.open-meteo.com/v1/seasonal'
const HISTORICAL_URL = 'https://archive-api.open-meteo.com/v1/archive'

const numberOrNull = (value) => Number.isFinite(value) ? value : null
const average = (values) => values.length
  ? values.reduce((sum, value) => sum + value, 0) / values.length
  : null

function formatMonth(period) {
  const date = new Date(`${period}-01T00:00:00Z`)
  return new Intl.DateTimeFormat('es-MX', {
    month: 'short',
    year: '2-digit',
    timeZone: 'UTC',
  }).format(date).replace('.', '')
}

export function describeWeatherCode(code) {
  const descriptions = {
    0: 'Despejado',
    1: 'Mayormente despejado',
    2: 'Parcialmente nublado',
    3: 'Nublado',
    45: 'Niebla',
    48: 'Niebla engelante',
    51: 'Llovizna ligera',
    53: 'Llovizna moderada',
    55: 'Llovizna intensa',
    56: 'Llovizna engelante ligera',
    57: 'Llovizna engelante intensa',
    61: 'Lluvia ligera',
    63: 'Lluvia moderada',
    65: 'Lluvia intensa',
    66: 'Lluvia engelante ligera',
    67: 'Lluvia engelante intensa',
    71: 'Nevada ligera',
    73: 'Nevada moderada',
    75: 'Nevada intensa',
    77: 'Granos de nieve',
    80: 'Chubascos ligeros',
    81: 'Chubascos moderados',
    82: 'Chubascos intensos',
    85: 'Chubascos de nieve ligeros',
    86: 'Chubascos de nieve intensos',
    95: 'Tormenta',
    96: 'Tormenta con granizo ligero',
    99: 'Tormenta con granizo intenso',
  }
  return Number.isInteger(code) ? descriptions[code] ?? null : null
}

async function fetchJson(url, signal) {
  const response = await fetch(url, { signal })
  if (!response.ok) throw new Error(`Open-Meteo respondió HTTP ${response.status}`)
  return response.json()
}

function weatherParams(latitude, longitude, fields) {
  return new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    timezone: 'auto',
    ...fields,
  })
}

async function fetchCurrentWeather(latitude, longitude, signal) {
  const params = weatherParams(latitude, longitude, {
    current: [
      'temperature_2m',
      'relative_humidity_2m',
      'precipitation',
      'wind_speed_10m',
      'apparent_temperature',
      'weather_code',
    ].join(','),
  })
  const result = await fetchJson(`${CURRENT_URL}?${params}`, signal)
  const current = result.current
  if (!current || typeof current !== 'object') {
    throw new Error('Open-Meteo no devolvió condiciones actuales')
  }

  const weatherCode = numberOrNull(current.weather_code)
  return {
    temperature: numberOrNull(current.temperature_2m),
    humidity: numberOrNull(current.relative_humidity_2m),
    precipitation: numberOrNull(current.precipitation),
    wind: numberOrNull(current.wind_speed_10m),
    feelsLike: numberOrNull(current.apparent_temperature),
    weatherCode,
    condition: describeWeatherCode(weatherCode),
    observedAt: typeof current.time === 'string' ? current.time : null,
    timezone: typeof result.timezone === 'string' ? result.timezone : null,
  }
}

async function fetchSeasonalForecast(latitude, longitude, signal) {
  const params = weatherParams(latitude, longitude, {
    forecast_days: '214',
    daily: [
      'temperature_2m_mean',
      'relative_humidity_2m_mean',
      'precipitation_sum',
      'wind_speed_10m_mean',
      'weather_code',
    ].join(','),
  })
  const result = await fetchJson(`${SEASONAL_URL}?${params}`, signal)
  if (!result.daily?.time?.length) {
    throw new Error('Open-Meteo no devolvió el pronóstico estacional')
  }
  return {
    monthly: aggregateDailyData(result.daily),
    periodStart: result.daily.time[0],
    periodEnd: result.daily.time[result.daily.time.length - 1],
  }
}

async function fetchHistoricalWeather(latitude, longitude, signal) {
  const now = new Date()
  const endDate = new Date(Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate() - 5,
  ))
  const startDate = new Date(Date.UTC(endDate.getUTCFullYear() - 5, endDate.getUTCMonth(), endDate.getUTCDate()))
  const formatDate = (date) => date.toISOString().slice(0, 10)
  const params = weatherParams(latitude, longitude, {
    daily: [
      'temperature_2m_mean',
      'relative_humidity_2m_mean',
      'precipitation_sum',
      'wind_speed_10m_mean',
    ].join(','),
    start_date: formatDate(startDate),
    end_date: formatDate(endDate),
  })
  const result = await fetchJson(`${HISTORICAL_URL}?${params}`, signal)
  if (!result.daily?.time?.length) {
    throw new Error('Open-Meteo no devolvió datos históricos')
  }
  const currentMonth = now.toISOString().slice(0, 7)
  const monthly = aggregateDailyData(result.daily)
    .filter((month) => month.period < currentMonth)
    .slice(-12)
  return {
    monthly,
    periodStart: result.daily.time[0],
    periodEnd: result.daily.time[result.daily.time.length - 1],
  }
}

function aggregateDailyData(daily) {
  const groups = new Map()
  const fields = [
    ['temperature_2m_mean', 'temperatures'],
    ['relative_humidity_2m_mean', 'humidities'],
    ['precipitation_sum', 'precipitations'],
    ['wind_speed_10m_mean', 'winds'],
  ]

  daily.time.forEach((date, index) => {
    const period = date.slice(0, 7)
    if (!/^\d{4}-\d{2}$/.test(period)) return
    let group = groups.get(period)
    if (!group) {
      group = {
        period,
        temperatures: [],
        humidities: [],
        precipitations: [],
        winds: [],
        weatherCodes: new Map(),
        days: 0,
      }
      groups.set(period, group)
    }
    group.days += 1
    for (const [key, valuesKey] of fields) {
      const value = daily[key]?.[index]
      if (!Number.isFinite(value)) continue
      group[valuesKey].push(value)
    }
    const weatherCode = daily.weather_code?.[index]
    if (Number.isInteger(weatherCode)) {
      group.weatherCodes.set(weatherCode, (group.weatherCodes.get(weatherCode) ?? 0) + 1)
    }
  })

  return [...groups.values()].map((group) => {
    const dominantWeatherCode = [...group.weatherCodes.entries()]
      .sort((left, right) => right[1] - left[1])[0]?.[0] ?? null
    return {
      period: group.period,
      month: formatMonth(group.period),
      temperature: average(group.temperatures),
      humidity: average(group.humidities),
      precipitation: group.precipitations.length
        ? group.precipitations.reduce((sum, value) => sum + value, 0)
        : null,
      wind: average(group.winds),
      weatherCode: dominantWeatherCode,
      condition: describeWeatherCode(dominantWeatherCode),
      days: group.days,
    }
  })
}

function makeChart(history, seasonal) {
  const historicRows = (history?.monthly ?? []).map((month) => ({
    ...month,
    historico: month.temperature,
    predicción: null,
    humedadHistorica: month.humidity,
    humedadPronostico: null,
  }))
  const forecastRows = (seasonal?.monthly ?? []).map((month) => ({
    ...month,
    historico: null,
    predicción: month.temperature,
    humedadHistorica: null,
    humedadPronostico: month.humidity,
  }))
  return [...historicRows, ...forecastRows]
}

function sourceResult(name, url, result) {
  const connected = result.status === 'fulfilled'
  return {
    name,
    url,
    connected,
    error: connected ? '' : result.reason instanceof Error
      ? result.reason.message
      : String(result.reason),
  }
}

export async function getClimateOutlook({ latitude, longitude }, signal) {
  if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90 ||
      !Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
    throw new TypeError('Se requieren coordenadas válidas para consultar el clima')
  }

  const results = await Promise.allSettled([
    fetchCurrentWeather(latitude, longitude, signal),
    fetchSeasonalForecast(latitude, longitude, signal),
    fetchHistoricalWeather(latitude, longitude, signal),
  ])
  if (signal?.aborted) {
    const error = new Error('Consulta cancelada')
    error.name = 'AbortError'
    throw error
  }

  const [currentResult, seasonalResult, historicalResult] = results
  const current = currentResult.status === 'fulfilled' ? currentResult.value : null
  const seasonal = seasonalResult.status === 'fulfilled' ? seasonalResult.value : null
  const historical = historicalResult.status === 'fulfilled' ? historicalResult.value : null
  const sources = {
    current: sourceResult(
      'Open-Meteo Forecast API',
      'https://open-meteo.com/en/docs',
      currentResult,
    ),
    seasonal: sourceResult(
      'Open-Meteo Seasonal Forecast API · ECMWF',
      'https://open-meteo.com/en/docs/seasonal-forecast-api',
      seasonalResult,
    ),
    historical: sourceResult(
      'Open-Meteo Historical Weather API · reanalysis',
      'https://open-meteo.com/en/docs/historical-weather-api',
      historicalResult,
    ),
  }

  if (!current && !seasonal && !historical) {
    throw new Error(Object.values(sources).map(({ error }) => error).join(' · '))
  }

  const forecastTemperatures = (seasonal?.monthly ?? [])
    .map(({ temperature }) => temperature)
    .filter(Number.isFinite)
  const range = forecastTemperatures.length
    ? `${Math.round(Math.min(...forecastTemperatures))}° — ${Math.round(Math.max(...forecastTemperatures))}°C`
    : null

  return {
    current,
    seasonal,
    historical,
    chart: makeChart(historical, seasonal),
    range,
    sources,
  }
}
