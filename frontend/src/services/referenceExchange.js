const EXCHANGE_RATE_URL = 'https://api.frankfurter.dev/v2/rate/mxn/usd'

export async function getReferenceExchangeRate(signal) {
  const response = await fetch(EXCHANGE_RATE_URL, { signal })
  if (!response.ok) throw new Error(`Frankfurter respondió HTTP ${response.status}`)
  const result = await response.json()
  if (!Number.isFinite(result.rate) || result.rate <= 0 ||
      typeof result.date !== 'string' || Number.isNaN(Date.parse(result.date))) {
    throw new Error('Frankfurter devolvió un tipo de cambio de referencia inválido')
  }
  return {
    mxnToUsd: result.rate,
    date: result.date,
    source: 'Frankfurter',
    url: 'https://frankfurter.dev/',
  }
}
