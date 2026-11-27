import { crops } from '../data/agtechData.js'

const cropNames = new Set(crops.map(({ name }) => name))
const unavailableMessage = 'Dato no disponible / Pendiente de fuente agronómica verificada'

function validateSource(source) {
  if (!source || typeof source !== 'object' ||
      typeof source.name !== 'string' || !source.name.trim() ||
      typeof source.url !== 'string' || typeof source.license !== 'string' || !source.license.trim()) {
    throw new Error('La fuente agronómica debe declarar name, url HTTPS y license')
  }
  let url
  try {
    url = new URL(source.url)
  } catch {
    throw new Error('La URL de la fuente agronómica no es válida')
  }
  if (url.protocol !== 'https:') throw new Error('La fuente agronómica debe usar HTTPS')
  return { name: source.name.trim(), url: url.toString(), license: source.license.trim() }
}

function validateRange(range, label, maximum) {
  if (!range || !Number.isFinite(range.min) ||
      !Number.isFinite(range.optimum) || !Number.isFinite(range.max) ||
      range.min > range.optimum || range.optimum > range.max ||
      range.min < 0 && label.includes('humedad') ||
      range.max > maximum) {
    throw new Error(`Rango inválido para ${label}; se requieren min, optimum y max ordenados`)
  }
  return { min: range.min, optimum: range.optimum, max: range.max }
}

function normalizeRequirements(payload) {
  if (!payload || typeof payload !== 'object' || !payload.crops || typeof payload.crops !== 'object') {
    throw new Error('La API agronómica debe devolver source, updatedAt y crops')
  }
  const source = validateSource(payload.source)
  if (typeof payload.updatedAt !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}T/.test(payload.updatedAt) ||
      Number.isNaN(Date.parse(payload.updatedAt))) {
    throw new Error('La API agronómica debe devolver updatedAt como fecha válida')
  }
  const requirements = Object.fromEntries(Object.entries(payload.crops).map(([name, record]) => {
    if (!cropNames.has(name)) throw new Error(`Cultivo no reconocido en requisitos: "${name}"`)
    if (!record || typeof record !== 'object') throw new Error(`Requisitos inválidos para "${name}"`)
    return [name, {
      temperatureC: validateRange(record.temperatureC, `temperatura de "${name}"`, 60),
      humidityPercent: validateRange(record.humidityPercent, `humedad de "${name}"`, 100),
    }]
  }))
  return { source, updatedAt: payload.updatedAt, crops: requirements }
}

function getRequirementsEndpoint(endpoint) {
  const normalized = endpoint.trim().replace(/\/+$/, '')
  if (!normalized) throw new Error('VITE_CROP_REQUIREMENTS_API no puede estar vacía')
  const url = new URL(normalized, window.location.origin)
  const isLocalDevelopment = url.hostname === 'localhost'
  if (url.protocol !== 'https:' && !(isLocalDevelopment && url.protocol === 'http:')) {
    throw new Error('La API agronómica debe usar HTTPS fuera del entorno local')
  }
  return normalized.endsWith('/requirements') ? normalized : `${normalized}/requirements`
}

export async function fetchCropRequirements(endpoint, signal) {
  const response = await fetch(getRequirementsEndpoint(endpoint), { signal })
  if (!response.ok) throw new Error(`La API agronómica respondió HTTP ${response.status}`)
  return normalizeRequirements(await response.json())
}

function rangeScore(value, range) {
  if (!Number.isFinite(value)) return null
  const distance = value <= range.optimum
    ? range.optimum - range.min
    : range.max - range.optimum
  if (distance === 0) return value === range.optimum ? 100 : 0
  return Math.round(Math.max(0, 100 * (1 - Math.abs(value - range.optimum) / distance)))
}

function climateScore(temperature, humidity, requirements) {
  if (!Number.isFinite(temperature) || !Number.isFinite(humidity)) return null
  const temperatureScore = rangeScore(temperature, requirements.temperatureC)
  const humidityScore = rangeScore(humidity, requirements.humidityPercent)
  return Math.round((temperatureScore + humidityScore) / 2)
}

export function calculateClimateSuitability(requirements, current, historical = []) {
  if (!requirements) return null
  const currentScore = climateScore(current?.temperature, current?.humidity, requirements)
  const historicalScores = historical
    .map((month) => climateScore(month.temperature, month.humidity, requirements))
    .filter(Number.isFinite)
  const historicalScore = historicalScores.length
    ? Math.round(historicalScores.reduce((total, score) => total + score, 0) / historicalScores.length)
    : null
  if (currentScore === null) return null
  return {
    currentScore,
    historicalScore,
    classification: currentScore >= 70 ? 'Compatible' : 'Fuera del rango de referencia',
  }
}

export { unavailableMessage as cropRequirementsUnavailableMessage }
