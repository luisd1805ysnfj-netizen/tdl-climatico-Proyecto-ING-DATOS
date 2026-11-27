const unavailableQuoteMessage = 'Dato no disponible / Pendiente de conexión a API oficial'

function formatCurrency(amount, currency) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
    currencyDisplay: 'code',
    minimumFractionDigits: 2,
  }).format(amount)
}

export function formatMarketQuote(quote, referenceRate = null) {
  if (!quote || !Number.isFinite(quote.price) || !quote.currency || !quote.unit) {
    return unavailableQuoteMessage
  }
  const unit = quote.unit.trim().toLocaleLowerCase('es')
  const kilogramsPerUnit = /^(?:(?:mxn|usd)\s*\/\s*)?(kg|kilogramo|kilogramos|kilogram|kilograms)$/.test(unit)
    ? 1
    : /^(?:(?:mxn|usd)\s*\/\s*)?(t|ton|tonelada|toneladas|metric ton|metric tons)$/.test(unit)
      ? 1000
      : null
  if (referenceRate && kilogramsPerUnit &&
      Number.isFinite(referenceRate.mxnToUsd) && referenceRate.mxnToUsd > 0) {
    const pricePerKg = quote.price / kilogramsPerUnit
    const mxn = quote.currency === 'MXN' ? pricePerKg : pricePerKg / referenceRate.mxnToUsd
    const usd = quote.currency === 'USD' ? pricePerKg : pricePerKg * referenceRate.mxnToUsd
    return `${formatCurrency(mxn, 'MXN')} / kg · ${formatCurrency(usd, 'USD')} / kg · FX ${referenceRate.date}`
  }
  return `${formatCurrency(quote.price, quote.currency)} / ${quote.unit}`
}
