import { createElement, useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import {
  Activity, Cloud, CloudDrizzle, CloudFog, CloudLightning, CloudSnow, CloudSun, CloudRain, Droplets, Leaf, MapPin,
  Search, ThermometerSun, Users, Wind,
  X, Database, RefreshCw, ChevronLeft, ChevronRight, Menu, LocateFixed, MapPinned, Sun,
  Clock3, ExternalLink, Route as RouteIcon,
} from 'lucide-react'
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip as ChartTooltip,
  XAxis, YAxis, Line,
} from 'recharts'
import { crops, regions } from './data/agtechData'
import referenceCatalog from './data/referenceCatalog.json'
import { useMarketPricesAPI } from './hooks/useMarketPricesAPI'
import { useClimateOutlook } from './hooks/useClimateOutlook'
import { useCropRequirements } from './hooks/useCropRequirements'
import { useMappedMarkets } from './hooks/useMappedMarkets'
import { useReferenceExchange } from './hooks/useReferenceExchange'
import { calculateClimateSuitability } from './services/cropRequirements'
import { formatMarketQuote } from './services/marketQuote'
import { getRouteAlternatives } from './services/tollRoutingService'

const cropIcons = {
  Zanahoria: '🥕', Cebolla: '🧅', Zarzamora: '🫐', Maíz: '🌽', Tomate: '🍅',
  Aguacate: '🥑', Limón: '🍋', Fresa: '🍓', 'Chile Jalapeño': '🌶️', Papa: '🥔',
  Pepino: '🥒', Brócoli: '🥦', Mango: '🥭', Plátano: '🍌', Calabacita: '🥒', Uva: '🍇',
  Coco: '🥥', Papaya: '🍈', Sandía: '🍉', Melón: '🍈', 'Chile verde': '🫑',
}

const unavailableMessage = 'Dato no disponible / Pendiente de conexión a API oficial'
const referenceOnlyMessage = 'Referencia orientativa, no oficial; no es una cotización ni una oferta de compra.'

function formatReferencePrice(pricesPerKg) {
  if (!pricesPerKg || !Number.isFinite(pricesPerKg.MXN) || !Number.isFinite(pricesPerKg.USD)) {
    return 'Precio de referencia no definido'
  }
  const formatCurrency = (amount, currency) => new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
    currencyDisplay: 'code',
    minimumFractionDigits: 2,
  }).format(amount)
  return `${formatCurrency(pricesPerKg.MXN, 'MXN')} / kg · ${formatCurrency(pricesPerKg.USD, 'USD')} / kg · ORIENTATIVO`
}

function formatCropPrice(cropName, marketQuote, exchangeRate) {
  if (marketQuote) return formatMarketQuote(marketQuote, exchangeRate)
  return formatReferencePrice(referenceCatalog.crops[cropName]?.pricesPerKg)
}

function formatSourceDate(timestamp) {
  if (!timestamp || Number.isNaN(Date.parse(timestamp))) return unavailableMessage
  return new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(timestamp))
}

const normalizeText = (value) => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLocaleLowerCase('es')

const distanceKm = ([lat1, lng1], [lat2, lng2]) => {
  const radians = (degrees) => (degrees * Math.PI) / 180
  const latitudeDelta = radians(lat2 - lat1)
  const longitudeDelta = radians(lng2 - lng1)
  const haversine = Math.min(1, Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(radians(lat1)) * Math.cos(radians(lat2)) *
    Math.sin(longitudeDelta / 2) ** 2)
  return 6371 * 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine))
}

const formatDuration = (seconds) => {
  const minutes = Math.max(1, Math.round(seconds / 60))
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return hours ? `${hours} h ${remainingMinutes} min` : `${minutes} min`
}

const formatRouteMoney = (price) => {
  if (!price || !Number.isFinite(price.amount) || !price.currency) return 'Tarifa no disponible'
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: price.currency,
    minimumFractionDigits: 2,
  }).format(price.amount)
}

const formatRouteQueryTime = (date) => {
  if (!date || Number.isNaN(new Date(date).getTime())) return 'hora no disponible'
  return new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(date))
}

const googleMapsDirectionsUrl = (origin, destination) => {
  const params = new URLSearchParams({
    api: '1',
    origin: `${origin[0]},${origin[1]}`,
    destination: `${destination[0]},${destination[1]}`,
    travelmode: 'driving',
  })
  return `https://www.google.com/maps/dir/?${params}`
}

const wazeDestinationUrl = (destination) =>
  `https://waze.com/ul?ll=${encodeURIComponent(`${destination[0]},${destination[1]}`)}&navigate=yes`

const buyerIcon = (color = '#1f5f3a') => L.divIcon({
  className: 'buyer-marker',
  html: `<div style="background:${color}"><span>$</span></div>`,
  iconSize: [42, 42],
  iconAnchor: [21, 42],
  popupAnchor: [0, -38],
})

const mappedMarketIcon = () => L.divIcon({
  className: 'market-marker',
  html: '<div><span>M</span></div>',
  iconSize: [38, 38],
  iconAnchor: [19, 38],
  popupAnchor: [0, -34],
})

const referencePointIcon = () => L.divIcon({
  className: 'reference-marker',
  html: '<div><span>R</span></div>',
  iconSize: [38, 38],
  iconAnchor: [19, 38],
  popupAnchor: [0, -34],
})

function MapFitBuyers({ buyers, locations = [], fallbackCenter, fallbackZoom, refreshKey, focusPoint }) {
  const map = useMap()
  useEffect(() => {
    const mapLocations = [...buyers, ...locations]
    let fitFrame
    const resizeFrame = window.requestAnimationFrame(() => {
      map.invalidateSize()
      fitFrame = window.requestAnimationFrame(() => {
        if (mapLocations.length === 1 && !focusPoint) {
          map.flyTo([mapLocations[0].lat, mapLocations[0].lng], Math.min(fallbackZoom + 3, 10), { duration: 0.8 })
          return
        }
        if (mapLocations.length > 1) {
          const points = mapLocations.map(({ lat, lng }) => [lat, lng])
          if (focusPoint) points.push(focusPoint)
          const bounds = L.latLngBounds(points)
          map.flyToBounds(bounds, { padding: [36, 36], maxZoom: 9, duration: 0.8 })
          return
        }
        if (focusPoint && mapLocations.length === 1) {
          const bounds = L.latLngBounds([focusPoint, [mapLocations[0].lat, mapLocations[0].lng]])
          map.flyToBounds(bounds, { padding: [36, 36], maxZoom: 9, duration: 0.8 })
          return
        }
        if (focusPoint) {
          map.flyTo(focusPoint, fallbackZoom, { duration: 0.8 })
          return
        }
        map.flyTo(fallbackCenter, fallbackZoom, { duration: 0.8 })
      })
    })
    return () => {
      window.cancelAnimationFrame(resizeFrame)
      if (fitFrame) window.cancelAnimationFrame(fitFrame)
    }
  }, [map, buyers, locations, fallbackCenter, fallbackZoom, refreshKey, focusPoint])
  return null
}

function FitRouteBounds({ route }) {
  const map = useMap()
  useEffect(() => {
    if (!route?.coordinates?.length) return
    map.fitBounds(L.latLngBounds([route.origin, route.destination, ...route.coordinates]), {
      padding: [48, 48],
      maxZoom: 13,
    })
  }, [map, route])
  return null
}

function MapClickHandler({ enabled, onSelect }) {
  useMapEvents({
    click(event) {
      if (enabled) onSelect(event.latlng.lat, event.latlng.lng)
    },
  })
  return null
}

const parcelIcon = L.divIcon({
  className: 'parcel-marker',
  html: '<div><span>●</span></div>',
  iconSize: [46, 46],
  iconAnchor: [23, 46],
  popupAnchor: [0, -42],
})

const tollIcon = L.divIcon({
  className: 'toll-marker',
  html: '<div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18M5 21V8l7-5 7 5v13M5 8h14M9 11v2m6-2v2M9 21v-4h6v4"/></svg></div>',
  iconSize: [36, 36],
  iconAnchor: [18, 18],
  popupAnchor: [0, -16],
})

function Metric({ icon: Icon, label, value, unit }) {
  return (
    <div className="metric-card">
      <div className="metric-icon"><Icon size={18} /></div>
      <div>
        <span>{label}</span>
        <strong>
          {Number.isFinite(value) ? value : 'Dato no disponible'}
          {Number.isFinite(value) && <small>{unit}</small>}
        </strong>
      </div>
    </div>
  )
}

function weatherIcon(code, condition) {
  const normalizedCondition = normalizeText(condition ?? '')
  if (/tormenta|electrica|rayo/.test(normalizedCondition)) return CloudLightning
  if (/llovizna/.test(normalizedCondition)) return CloudDrizzle
  if (/lluvia|lluvioso|chubasco/.test(normalizedCondition)) return CloudRain
  if (/niebla|neblina|bruma/.test(normalizedCondition)) return CloudFog
  if (/nieve|nevando/.test(normalizedCondition)) return CloudSnow
  if (/nublado|cubierto/.test(normalizedCondition) &&
      !/parcialmente|algo nublado/.test(normalizedCondition)) return Cloud
  if (/parcialmente|mayormente despejado/.test(normalizedCondition)) return CloudSun
  if (/despejado|soleado/.test(normalizedCondition)) return Sun

  const numericCode = Number(code)
  if (code !== null && code !== undefined && code !== '' && Number.isFinite(numericCode)) {
    if (numericCode === 0) return Sun
    if ([1, 2].includes(numericCode)) return CloudSun
    if (numericCode === 3) return Cloud
    if ([45, 48].includes(numericCode)) return CloudFog
    if ([51, 53, 55, 56, 57].includes(numericCode)) return CloudDrizzle
    if ([61, 63, 65, 66, 67, 80, 81, 82].includes(numericCode)) return CloudRain
    if ([71, 73, 75, 77, 85, 86].includes(numericCode)) return CloudSnow
    if ([95, 96, 99].includes(numericCode)) return CloudLightning
    return null
  }

  return null
}

function WeatherIcon({ code, condition, size = 20, ...props }) {
  const Icon = weatherIcon(code, condition)
  return Icon ? createElement(Icon, { size, ...props }) : null
}

function BuyerDetails({ buyer, crop, exchangeRate }) {
  const quote = buyer.prices?.[crop]
  const cropReference = referenceCatalog.crops[crop]
  const priceText = quote
    ? formatMarketQuote(quote, exchangeRate)
    : formatReferencePrice(cropReference?.pricesPerKg)
  const minimumOrder = buyer.minimumOrder ??
    `Mínimo de referencia: ${cropReference?.minimumOrderKg ?? 'no definido'} kg (orientativo; confirmar)`
  const deliveryTerms = buyer.deliveryTerms ?? referenceCatalog.deliveryTermsReference
  return (
    <>
      <div className="buyer-detail-price">
        <span>{quote ? 'Cotización reportada por la fuente' : 'Precio de referencia orientativo · no es oferta de compra'}</span>
        <strong>{priceText}</strong>
      </div>
      <div className="buyer-detail-row">
        <Activity size={17} />
        <span><b>Tendencia de 30 días</b>{buyer.trend30Days ?? 'No incluida en el catálogo de referencia'}</span>
      </div>
      <div className="buyer-detail-row">
        <CloudSun size={18} />
        <span><b>Clima local</b>{buyer.localClimate ?? 'Consulta el clima de Open-Meteo para la región seleccionada'}</span>
      </div>
      <div className="buyer-detail-row">
        <Users size={17} />
        <span><b>Compra mínima y condiciones</b>
          {minimumOrder}
          <span>{deliveryTerms}</span>
        </span>
      </div>
      <p className="buyer-reference">
        {buyer.isReferencePoint
          ? referenceOnlyMessage
          : buyer.isMappedPlace
          ? <>Ubicación mapeada por <a href={buyer.source.url} target="_blank" rel="noreferrer">OpenStreetMap</a>; no confirma comprador, producto comprado ni condiciones. Licencia ODbL · consulta {formatSourceDate(buyer.updatedAt)}.</>
          : <>Fuente declarada: <a href={buyer.source.url} target="_blank" rel="noreferrer">{buyer.source.name}</a>
            {' · '}licencia {buyer.source.license}
            {' · '}actualización {formatSourceDate(quote?.updatedAt ?? buyer.updatedAt)}</>}
      </p>
    </>
  )
}

export default function App() {
  const [crop, setCrop] = useState('Zanahoria')
  const [region, setRegion] = useState('AMERICA')
  const [cropSearch, setCropSearch] = useState('')
  const [cropFilter, setCropFilter] = useState('todos')
  const [markParcel, setMarkParcel] = useState(false)
  const [parcelPoint, setParcelPoint] = useState(null)
  const [originType, setOriginType] = useState(null)
  const [locationOverride, setLocationOverride] = useState(null)
  const [locationStatus, setLocationStatus] = useState('')
  const [activeTab, setActiveTab] = useState('observatorio')
  const [selectedBuyer, setSelectedBuyer] = useState(null)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mobileSection, setMobileSection] = useState('clima')
  const [showAllCrops, setShowAllCrops] = useState(false)
  const [cropsCollapsed, setCropsCollapsed] = useState(false)
  const [routeResult, setRouteResult] = useState(null)
  const [selectedRouteId, setSelectedRouteId] = useState('')
  const [routeLoading, setRouteLoading] = useState(false)
  const [routeError, setRouteError] = useState('')
  const [routePanelOpen, setRoutePanelOpen] = useState(false)
  const [vehicleType, setVehicleType] = useState('2AxlesAuto')
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia('(max-width: 767px)').matches,
  )
  const routeAbortController = useRef(null)
  const routeRequestId = useRef(0)
  const market = useMarketPricesAPI()
  const exchange = useReferenceExchange()
  const cropRequirements = useCropRequirements()

  useEffect(() => {
    const query = window.matchMedia('(max-width: 767px)')
    const update = () => setIsMobile(query.matches)
    update()
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (!mobileOpen && !selectedBuyer) return undefined
    const handleKeyDown = (event) => {
      if (event.key !== 'Escape') return
      setMobileOpen(false)
      setSelectedBuyer(null)
      routeRequestId.current += 1
      routeAbortController.current?.abort()
      routeAbortController.current = null
      setRouteResult(null)
      setSelectedRouteId('')
      setRouteLoading(false)
      setRouteError('')
      setRoutePanelOpen(false)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mobileOpen, selectedBuyer])

  useEffect(() => () => routeAbortController.current?.abort(), [])

  const regionData = locationOverride ?? regions[region]
  const selectedLocation = {
    latitude: locationOverride?.latitude ?? regionData.latitude,
    longitude: locationOverride?.longitude ?? regionData.longitude,
  }
  const climateRequest = useClimateOutlook(selectedLocation)
  const mappedMarketsRequest = useMappedMarkets(selectedLocation)
  const forecast = climateRequest.outlook
  const currentWeather = forecast?.current ?? null
  const cropSuitability = (name) => {
    const apiRequirements = cropRequirements.data?.crops[name]
    const result = calculateClimateSuitability(
      apiRequirements ?? referenceCatalog.crops[name]?.requirements,
      currentWeather,
      forecast?.historical?.monthly,
    )
    return result
      ? {
          ...result,
          source: apiRequirements ? cropRequirements.data.source.name : 'Catálogo local orientativo',
        }
      : null
  }
  const currentWeatherError = forecast?.sources?.current?.error || climateRequest.error
  const hasTemperatureSeries = forecast?.chart?.some((month) =>
    Number.isFinite(month.historico) || Number.isFinite(month['predicción']),
  )
  const localReferencePoints = useMemo(() => referenceCatalog.referencePoints
    .filter((point) => region === 'AMERICA' || point.regionKeys.includes(region))
    .map((point) => ({
      ...point,
      name: `Punto regional de referencia · ${point.city}`,
      category: 'Referencia geográfica orientativa; centro de compra no verificado',
      crops: [crop],
      prices: {},
      isReferencePoint: true,
    })), [crop, region])
  const visibleBuyers = useMemo(() => {
    const cropBuyers = market.buyers.filter((buyer) => buyer.crops.includes(crop))
    if (!parcelPoint) {
      const country = regionData.marketCountry ?? region
      const countries = Array.isArray(country) ? country : [country]
      const state = regionData.marketState ?? (region === 'Colima' ? 'Colima' : '')
      const regionBuyers = cropBuyers.filter((buyer) => region === 'AMERICA'
        ? buyer.lng >= -180 && buyer.lng <= -30 && buyer.lat >= -60 && buyer.lat <= 84
        : state ? buyer.state === state : countries.includes(buyer.country))
      return [...regionBuyers, ...localReferencePoints]
    }

    const nearestBuyers = [...cropBuyers, ...localReferencePoints]
      .map((buyer) => ({ buyer, distance: distanceKm(parcelPoint, [buyer.lat, buyer.lng]) }))
      .sort((a, b) => a.distance - b.distance)
    const selected = new Set(nearestBuyers
      .filter(({ distance }) => distance <= 120)
      .slice(0, 8)
      .map(({ buyer }) => buyer))
    for (const { buyer } of nearestBuyers) {
      if (selected.size >= 4) break
      selected.add(buyer)
    }
    return nearestBuyers
      .filter(({ buyer }) => selected.has(buyer))
      .map(({ buyer }) => buyer)
  }, [crop, localReferencePoints, market.buyers, parcelPoint, region, regionData])

  const normalizedSearch = normalizeText(cropSearch.trim())
  const matchingCrops = crops.filter((item) =>
    (cropFilter === 'todos' || item.type === cropFilter) &&
    normalizeText(item.name).includes(normalizedSearch),
  )
  const filteredCrops = showAllCrops ? matchingCrops : matchingCrops.slice(0, 6)
  const routeOptions = routeResult?.routes ?? []
  const activeRoute = routeOptions.find((item) => item.id === selectedRouteId) ?? routeOptions[0] ?? null

  const invalidateRoute = (closePanel = true) => {
    routeRequestId.current += 1
    routeAbortController.current?.abort()
    routeAbortController.current = null
    setRouteResult(null)
    setSelectedRouteId('')
    setRouteLoading(false)
    setRouteError('')
    if (closePanel) setRoutePanelOpen(false)
  }

  const calculateRoutes = async (origin = parcelPoint, buyer = selectedBuyer, selectedVehicle = vehicleType) => {
    if (!origin || !buyer) return
    routeAbortController.current?.abort()
    const requestId = ++routeRequestId.current
    const controller = new AbortController()
    routeAbortController.current = controller
    setRouteResult(null)
    setSelectedRouteId('')
    setRouteError('')
    setRouteLoading(true)
    setRoutePanelOpen(true)
    try {
      const result = await getRouteAlternatives(origin, [buyer.lat, buyer.lng], {
        vehicleType: selectedVehicle,
        signal: controller.signal,
      })
      if (requestId === routeRequestId.current) {
        setRouteResult(result)
        setSelectedRouteId(result.routes[0]?.id ?? '')
      }
    } catch (error) {
      if (error.name !== 'AbortError' && requestId === routeRequestId.current) {
        setRouteError(`No se pudo calcular la ruta: ${error.message}`)
      }
    } finally {
      if (requestId === routeRequestId.current) {
        routeAbortController.current = null
        setRouteLoading(false)
      }
    }
  }

  const openRoutePanel = () => {
    setRouteError('')
    setRoutePanelOpen(true)
    if (parcelPoint) calculateRoutes()
  }

  const changeVehicleType = (nextVehicleType) => {
    setVehicleType(nextVehicleType)
    if (parcelPoint && selectedBuyer && routePanelOpen) {
      calculateRoutes(parcelPoint, selectedBuyer, nextVehicleType)
    }
  }

  const selectBuyer = (buyer) => {
    invalidateRoute()
    setSelectedBuyer(buyer)
  }

  const selectCrop = (name) => {
    invalidateRoute()
    setCrop(name)
    setSelectedBuyer(null)
    setMobileOpen(false)
    if (isMobile) setMobileSection('map')
  }

  const selectTab = (tab) => {
    invalidateRoute()
    setActiveTab(tab)
    setMobileOpen(false)
    setSelectedBuyer(null)
  }

  const clearCropFilters = () => {
    setCropSearch('')
    setCropFilter('todos')
    setShowAllCrops(false)
  }

  const setPointAndWeather = (lat, lng, source = 'parcel') => {
    invalidateRoute(false)
    setParcelPoint([lat, lng])
    setOriginType(source)
    setLocationOverride({
      city: `Parcela ${lat.toFixed(4)}, ${lng.toFixed(4)}`,
      latitude: lat,
      longitude: lng,
      mapCenter: [lat, lng],
      zoom: 12,
    })
    setRegion('AMERICA')
    setLocationStatus(source === 'gps' ? 'Ubicación actual detectada' : 'Parcela marcada')
    setMarkParcel(false)
    setRoutePanelOpen(Boolean(selectedBuyer))
    if (selectedBuyer) calculateRoutes([lat, lng], selectedBuyer)
  }

  const markRouteOrigin = () => {
    setRouteError('')
    setRoutePanelOpen(false)
    setMarkParcel(true)
    setMobileSection('map')
  }

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      const message = 'Geolocalización no disponible en este navegador.'
      setLocationStatus(message)
      if (selectedBuyer) {
        setRouteError(message)
        setRoutePanelOpen(true)
      }
      return
    }
    setLocationStatus('Detectando ubicación...')
    navigator.geolocation.getCurrentPosition(
      (position) => setPointAndWeather(position.coords.latitude, position.coords.longitude, 'gps'),
      () => {
        const message = 'No se pudo obtener tu ubicación. Revisa el permiso de ubicación del navegador.'
        setLocationStatus(message)
        if (selectedBuyer) {
          setRouteError(message)
          setRoutePanelOpen(true)
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
    )
  }

  return (
    <div className="app-shell grid min-h-screen lg:grid-cols-2">
      <aside className={`sidebar ${mobileOpen ? 'open' : ''} ${mobileSection === 'clima' ? 'mobile-shown' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><Leaf size={21} /></div>
          <div>
            <strong>Observatorio</strong>
            <span>Climático & Mercado</span>
          </div>
          <button className="close-sidebar" aria-label="Cerrar menú" onClick={() => setMobileOpen(false)}><X size={20} /></button>
        </div>

        <nav className="main-nav">
          <button className={activeTab === 'observatorio' ? 'active' : ''} onClick={() => selectTab('observatorio')}>
            <MapPin size={18} /> Observatorio
          </button>
          <button className={activeTab === 'fuentes' ? 'active' : ''} onClick={() => selectTab('fuentes')}>
            <Database size={18} /> Fuentes y API
          </button>
        </nav>

        {activeTab === 'observatorio' && (
          <div className="sidebar-content">
            <label className="field-label">Visualizar producto</label>
            <div className="crop-search">
              <Search size={14} />
              <input
                value={cropSearch}
                onChange={(event) => setCropSearch(event.target.value)}
                placeholder="Buscar cultivo..."
                aria-label="Buscar cultivo"
              />
            </div>
            <div className="crop-tabs">
              {[
                { label: 'Todos', value: 'todos' },
                { label: 'Verduras', value: 'verdura' },
                { label: 'Frutas', value: 'fruta' },
              ].map((tab) => (
                <button key={tab.value} className={cropFilter === tab.value ? 'active' : ''} onClick={() => setCropFilter(tab.value)}>
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="crop-result-count" aria-live="polite">
              {matchingCrops.length} {matchingCrops.length === 1 ? 'cultivo coincide' : 'cultivos coinciden'}
            </div>
            <div className="crop-select grid grid-cols-2 gap-2 overflow-x-hidden">
              {filteredCrops.map((item) => (
                <button
                  key={item.name}
                  className={crop === item.name ? 'selected' : ''}
                  onClick={() => selectCrop(item.name)}
                  aria-pressed={crop === item.name}
                >
                  <span>{cropIcons[item.name]}</span>
                  <span className="crop-option-label">
                    <strong>{item.name}</strong>
                    <small>{formatCropPrice(item.name, market.prices[item.name], exchange.rate)}</small>
                  </span>
                </button>
              ))}
            </div>
            {matchingCrops.length === 0 && (
              <div className="crop-empty">
                <span>No hay cultivos que coincidan con esos filtros.</span>
                <button onClick={clearCropFilters}>Limpiar filtros</button>
              </div>
            )}
            {matchingCrops.length > 6 && (
              <button className="crop-more" onClick={() => setShowAllCrops((value) => !value)}>
                {showAllCrops ? 'Mostrar menos' : `Ver ${matchingCrops.length - 6} cultivos más`}
              </button>
            )}

            <label className="field-label">País / Región</label>
            <div className="select-wrap">
              <Search size={16} />
              <select value={region} onChange={(event) => {
                invalidateRoute()
                setRegion(event.target.value)
                setLocationOverride(null)
                setParcelPoint(null)
                setOriginType(null)
                setSelectedBuyer(null)
                setLocationStatus('')
                setMarkParcel(false)
              }}>
                {Object.entries(regions).map(([key, item]) => (
                  <option key={key} value={key}>{item.label}</option>
                ))}
              </select>
            </div>

            <div className="weather-heading">
              <div>
                <span>Clima ahora</span>
                <strong>{regionData.city}</strong>
              </div>
              <span className={`live-badge ${currentWeather ? '' : 'demo'}`}>
                <i /> {currentWeather ? 'API conectada' : climateRequest.loading ? 'Consultando' : 'No disponible'}
              </span>
            </div>

            <div className="location-actions">
              <button className="min-h-[44px]" onClick={useCurrentLocation}><LocateFixed size={15} /> Usar mi ubicación</button>
              <button className={`min-h-[44px] ${markParcel ? 'active' : ''}`} onClick={() => setMarkParcel((value) => !value)}>
                <MapPinned size={15} /> {markParcel ? 'Clic en el mapa' : 'Marcar parcela'}
              </button>
            </div>
            {locationStatus && <small className="location-status">{locationStatus}</small>}

            {currentWeather ? (
              <div className="weather-primary">
                <WeatherIcon
                  code={currentWeather.weatherCode}
                  condition={currentWeather.condition}
                  size={48}
                  strokeWidth={1.5}
                />
                <div>
                  <strong>{Number.isFinite(currentWeather.temperature)
                    ? `${currentWeather.temperature}°`
                    : 'Dato no disponible'}</strong>
                  <span>{currentWeather.condition ?? 'Condición no disponible'}</span>
                </div>
              </div>
            ) : (
              <p className="weather-unavailable" role="status">
                {climateRequest.loading ? 'Consultando Open-Meteo…' : unavailableMessage}
                {currentWeatherError && <span>{currentWeatherError}</span>}
              </p>
            )}

            <div className="metrics-grid">
              <Metric icon={Droplets} label="Humedad" value={currentWeather?.humidity} unit="%" />
              <Metric icon={CloudRain} label="Precipitación" value={currentWeather?.precipitation} unit=" mm" />
              <Metric icon={Wind} label="Viento" value={currentWeather?.wind} unit=" km/h" />
              <Metric icon={ThermometerSun} label="Sensación" value={currentWeather?.feelsLike} unit="°C" />
            </div>
            <p className="climate-attribution">
              Fuente: <a href="https://open-meteo.com/en/docs" target="_blank" rel="noreferrer">Open-Meteo Forecast API</a>
              {' · '}dato de modelo, no observación de estación
              {currentWeather?.observedAt && <> · actualización del modelo {currentWeather.observedAt}</>}
            </p>

            <div className="forecast-card">
              <div className="forecast-top">
                <div>
                  <span>Histórico y pronóstico estacional</span>
                  <strong>{forecast?.range ?? (climateRequest.loading ? 'Consultando APIs…' : unavailableMessage)}</strong>
                </div>
              </div>
              <div className="forecast-chart">
                {hasTemperatureSeries && (!isMobile || mobileSection === 'clima') ? (
                  <ResponsiveContainer width="100%" height="100%" initialDimension={{ width: 280, height: 78 }}>
                  <AreaChart data={forecast.chart}>
                    <defs>
                      <linearGradient id="history" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#87a887" stopOpacity={0.28} />
                        <stop offset="95%" stopColor="#87a887" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="prediction" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#df9a32" stopOpacity={0.32} />
                        <stop offset="95%" stopColor="#df9a32" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e7ede7" />
                    <XAxis dataKey="month" interval="preserveStartEnd" minTickGap={5} tick={{ fontSize: 9, fill: '#758076' }} axisLine={false} tickLine={false} />
                    <YAxis hide domain={['dataMin - 2', 'dataMax + 2']} />
                    <YAxis yAxisId="humidity" hide orientation="right" domain={[30, 100]} />
                    <ChartTooltip />
                    <Area type="monotone" dataKey="historico" stroke="#728b74" fill="url(#history)" strokeWidth={2} />
                    <Area type="monotone" dataKey="predicción" stroke="#d89332" fill="url(#prediction)" strokeWidth={2} />
                    <Line yAxisId="humidity" type="monotone" dataKey="humedadHistorica" stroke="#347b83" strokeWidth={1.5} dot={false} />
                    <Line yAxisId="humidity" type="monotone" dataKey="humedadPronostico" stroke="#639ba1" strokeWidth={1.5} strokeDasharray="4 3" dot={false} />
                  </AreaChart>
                  </ResponsiveContainer>
                ) : <p className="forecast-empty">{unavailableMessage}</p>}
              </div>
              <p>
                Histórico de <a href="https://open-meteo.com/en/docs/historical-weather-api" target="_blank" rel="noreferrer">Open-Meteo Historical Weather API</a>
                {' · '}pronóstico de <a href="https://open-meteo.com/en/docs/seasonal-forecast-api" target="_blank" rel="noreferrer">Seasonal Forecast API / ECMWF</a>.
                {' '}Histórico de reanálisis, no observación de estación. Pronóstico de área (~36 km), sin corrección de sesgo.
                {' '}Open-Meteo gratuito: solo uso no comercial; datos <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a>.
              </p>
              {forecast?.sources?.seasonal?.error && (
                <p className="climate-source-error" role="status">
                  Pronóstico estacional no disponible: {forecast.sources.seasonal.error}
                </p>
              )}
              {forecast?.sources?.historical?.error && (
                <p className="climate-source-error" role="status">
                  Histórico no disponible: {forecast.sources.historical.error}
                </p>
              )}
            </div>
          </div>
        )}
      </aside>

      {mobileOpen && <button className="sidebar-backdrop" aria-label="Cerrar menú" onClick={() => setMobileOpen(false)} />}

      <main className="main-content">
        <header className="topbar">
          <button className="menu-button" onClick={() => {
            setMobileSection('clima')
            setMobileOpen(true)
          }}><Menu size={21} /></button>
          <div className="breadcrumb">
            <span>Observatorio</span>
            <ChevronRight size={14} />
            <strong>{activeTab === 'observatorio' ? 'Inteligencia agrícola' : 'Fuentes de datos'}</strong>
          </div>
          <div className="api-status">
            <span aria-live="polite">
              <i className="status-dot" />
              {market.error
                ? 'Error API · referencias disponibles'
                : market.connected
                  ? 'API de precios conectada'
                  : 'Referencias orientativas · API pendiente'}
            </span>
            <button onClick={() => {
              market.refresh()
              climateRequest.refresh()
              cropRequirements.refresh()
              exchange.refresh()
              mappedMarketsRequest.refresh()
            }} disabled={market.loading || climateRequest.loading || cropRequirements.loading || exchange.loading || mappedMarketsRequest.loading}>
              <RefreshCw size={15} /> {market.loading || climateRequest.loading || cropRequirements.loading || exchange.loading || mappedMarketsRequest.loading ? 'Consultando' : 'Actualizar'}
            </button>
          </div>
        </header>

        {activeTab === 'observatorio' ? (
          <div className={`dashboard grid md:grid-cols-2 ${!isMobile && cropsCollapsed ? 'crops-collapsed' : ''}`}>
            <section className={`recommendations ${mobileSection !== 'crops' ? 'mobile-hidden' : ''}`}>
              <div className="section-heading">
                <div>
                  <span>CATÁLOGO DE PRODUCTOS</span>
                  <h1>Cultivos</h1>
                </div>
                <p>Estimación climática basada en rangos de referencia y datos Open-Meteo; no sustituye evaluación agronómica local.</p>
                {!isMobile && (
                  <button
                    className="collapse-crops-button"
                    aria-label="Minimizar catálogo de cultivos"
                    aria-controls="crop-catalog"
                    aria-expanded={!cropsCollapsed}
                    onClick={() => setCropsCollapsed(true)}
                  >
                    <ChevronLeft size={17} /> Minimizar
                  </button>
                )}
              </div>
              <div className="recommendation-count" aria-live="polite">
                {matchingCrops.length} {matchingCrops.length === 1 ? 'cultivo' : 'cultivos'} en catálogo · precios orientativos locales; API opcional
              </div>

              <div className="crop-list" id="crop-catalog">
                {filteredCrops.map((item, index) => {
                  const suitability = cropSuitability(item.name)
                  const marketQuote = market.prices[item.name]
                  return (
                  <article className={`crop-card ${crop === item.name ? 'highlight' : ''}`} key={item.name}>
                    <div className="crop-rank">{String(index + 1).padStart(2, '0')}</div>
                    <div className="crop-emoji">{cropIcons[item.name]}</div>
                    <div className="crop-info">
                      <h3><button className="crop-name-button" onClick={() => selectCrop(item.name)}>{item.name}</button></h3>
                      <p>
                        {suitability
                          ? `Clima Open-Meteo: ${suitability.currentScore}% · ${suitability.classification}${
                            suitability.historicalScore === null
                              ? ''
                              : ` · histórico disponible: ${suitability.historicalScore}%`
                          } · rango ${suitability.source}`
                          : climateRequest.loading
                            ? 'Calculando compatibilidad con Open-Meteo…'
                            : 'Compatibilidad pendiente de datos climáticos de Open-Meteo.'}
                      </p>
                    </div>
                    <div className="crop-price">
                      <span>{marketQuote ? 'Cotización de API' : 'Precio de referencia · no oficial'}</span>
                      <strong>{formatCropPrice(item.name, marketQuote, exchange.rate)}</strong>
                    </div>
                    <button onClick={() => selectCrop(item.name)}>
                      Ver puntos <ChevronRight size={16} />
                    </button>
                  </article>
                  )
                })}
                {matchingCrops.length === 0 && (
                  <div className="crop-empty crop-empty-main">
                    <span>No hay cultivos que coincidan con esos filtros.</span>
                    <button onClick={clearCropFilters}>Limpiar filtros</button>
                  </div>
                )}
              </div>
            </section>

            <section className={`map-section ${mobileSection !== 'map' ? 'mobile-hidden' : ''}`}>
              <div className="map-heading">
                <div>
                  <span>COMPRADORES API · REFERENCIAS REGIONALES</span>
                  <h2>{crop}</h2>
                </div>
                <div className="map-heading-actions">
                  <div className="map-count">
                    <Users size={16} />
                    <span aria-label={`${visibleBuyers.filter((buyer) => !buyer.isReferencePoint).length} registros API, ${visibleBuyers.filter((buyer) => buyer.isReferencePoint).length} puntos regionales de referencia y ${mappedMarketsRequest.locations.length} ubicaciones OSM`}>
                      {`${visibleBuyers.filter((buyer) => !buyer.isReferencePoint).length} API · ${
                        visibleBuyers.filter((buyer) => buyer.isReferencePoint).length
                      } ref · ${
                        mappedMarketsRequest.error ? 'OSM error' : mappedMarketsRequest.loading
                          ? 'OSM…'
                          : `${mappedMarketsRequest.locations.length} OSM`
                      }`}
                    </span>
                  </div>
                  {!isMobile && cropsCollapsed && (
                    <button
                      className="expand-crops-button"
                      aria-label="Mostrar catálogo de cultivos"
                      aria-controls="crop-catalog"
                      aria-expanded={false}
                      onClick={() => setCropsCollapsed(false)}
                    >
                      <ChevronRight size={17} /> Cultivos
                    </button>
                  )}
                </div>
              </div>
              <div className="map-frame min-h-[420px]">
                {(!isMobile || mobileSection === 'map') ? (
                  <MapContainer
                    center={locationOverride?.mapCenter ?? regionData.mapCenter}
                    zoom={locationOverride?.zoom ?? regionData.zoom}
                    scrollWheelZoom
                    className="leaflet-map"
                  >
                  <MapFitBuyers
                  buyers={visibleBuyers}
                  locations={mappedMarketsRequest.locations}
                  fallbackCenter={locationOverride?.mapCenter ?? regionData.mapCenter}
                  fallbackZoom={locationOverride?.zoom ?? regionData.zoom}
                  refreshKey={`${mobileSection}-${activeTab}-${cropsCollapsed && !isMobile ? 'collapsed' : 'expanded'}`}
                  focusPoint={parcelPoint}
                  />
                  {activeRoute && selectedBuyer && (
                    <>
                      <FitRouteBounds route={activeRoute} />
                      {routeOptions.map((item, index) => (
                        <Polyline
                          key={item.id}
                          positions={item.coordinates}
                          pathOptions={{
                            color: index === 0 ? '#205e78' : '#c1812d',
                            weight: item.id === activeRoute.id ? 7 : 4,
                            opacity: item.id === activeRoute.id ? 0.95 : 0.58,
                            dashArray: index === 0 ? undefined : '10 9',
                          }}
                          eventHandlers={{ click: () => setSelectedRouteId(item.id) }}
                        />
                      ))}
                      {activeRoute.tolls.map((toll, index) => (
                        <Marker
                          key={`${activeRoute.id}-${toll.id}-${index}`}
                          position={[toll.latitude, toll.longitude]}
                          icon={tollIcon}
                        >
                          <Popup>
                            <div className="toll-popup">
                              <strong>{toll.name}</strong>
                              <span>{toll.road}</span>
                              <b>{toll.isCongestionZone ? 'Cargo vial' : 'Tarifa del vehículo'}</b>
                              <small>Vehículo: {vehicleType === '2AxlesAuto'
                                ? 'Pickup / Camioneta (2 ejes)'
                                : 'Camión de carga (perfil de 3 ejes)'}</small>
                              <span className="toll-popup-price">
                                {formatRouteMoney(toll.price === null
                                  ? null
                                  : { amount: toll.price, currency: toll.currency })}
                              </span>
                              {toll.paymentMethod && <small>Método: {toll.paymentMethod}</small>}
                              <small>Fuente: <a href="https://tollguru.com/" target="_blank" rel="noreferrer">TollGuru</a> · consulta {formatRouteQueryTime(routeResult.queriedAt)}</small>
                              <small>La hora de consulta no confirma la fecha de vigencia de la tarifa.</small>
                            </div>
                          </Popup>
                        </Marker>
                      ))}
                    </>
                  )}
                  <MapClickHandler enabled={markParcel} onSelect={(lat, lng) => {
                    setPointAndWeather(lat, lng)
                  }} />
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
                    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {parcelPoint && (
                    <Marker position={parcelPoint} icon={parcelIcon}>
                      <Popup>
                        <div className="buyer-popup">
                          <strong>Mi parcela</strong>
                          <span>{parcelPoint[0].toFixed(4)}, {parcelPoint[1].toFixed(4)}</span>
                        </div>
                      </Popup>
                    </Marker>
                  )}
                  {visibleBuyers.map((buyer) => (
                    <Marker
                      key={buyer.id}
                      position={[buyer.lat, buyer.lng]}
                      icon={buyer.isReferencePoint ? referencePointIcon() : buyerIcon()}
                      eventHandlers={{ click: () => selectBuyer(buyer) }}
                    >
                      <Popup>
                        <div className="buyer-popup">
                          <strong>{buyer.name}</strong>
                          <span>{buyer.city}, {buyer.country}</span>
                          <span>{buyer.isReferencePoint
                            ? referenceOnlyMessage
                            : 'Consulta la ficha lateral para cotizaciones, condiciones y rutas.'}</span>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                  {mappedMarketsRequest.locations.map((location) => (
                    <Marker
                      key={location.id}
                      position={[location.lat, location.lng]}
                      icon={mappedMarketIcon()}
                      eventHandlers={{ click: () => selectBuyer(location) }}
                    >
                      <Popup>
                        <div className="buyer-popup">
                          <strong>{location.name}</strong>
                          <span>{location.city || 'Ciudad no especificada'}{location.country ? `, ${location.country}` : ''}</span>
                          <span>{location.category}</span>
                          <span>Consulta la ficha lateral para referencias y rutas.</span>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                  </MapContainer>
                ) : <div className="map-placeholder">Abre la pestaña Mapa para explorar compradores.</div>}
              </div>

              {selectedBuyer && (
                <aside className="buyer-drawer">
                  <button className="drawer-close" aria-label="Cerrar ficha del punto" onClick={() => {
                    invalidateRoute()
                    setSelectedBuyer(null)
                  }}><X size={18} /></button>
                  <span className="drawer-label">
                    {selectedBuyer.isReferencePoint
                      ? 'PUNTO REGIONAL · COMPRADOR NO VERIFICADO'
                      : selectedBuyer.isMappedPlace
                        ? 'UBICACIÓN OSM · COMPRADOR NO CONFIRMADO'
                        : 'COMPRADOR REPORTADO POR API'}
                  </span>
                  <h3>{selectedBuyer.name}</h3>
                  <p><MapPin size={15} /> {[selectedBuyer.city, selectedBuyer.state, selectedBuyer.country].filter(Boolean).join(', ') || 'Dirección no especificada en la fuente'}</p>
                  {(selectedBuyer.isMappedPlace || selectedBuyer.isReferencePoint) && <p>{selectedBuyer.category}</p>}
                  <div className="buyer-drawer-details">
                    <BuyerDetails buyer={selectedBuyer} crop={crop} exchangeRate={exchange.rate} />
                  </div>
                  <button
                    className="route-trigger min-h-[44px]"
                    aria-expanded={routePanelOpen}
                    onClick={() => routePanelOpen ? setRoutePanelOpen(false) : openRoutePanel()}
                  >
                    <RouteIcon size={17} /> ¿Cómo llegar?
                  </button>
                  {routePanelOpen && (
                    <div className="route-panel">
                      {selectedBuyer.isReferencePoint && (
                        <p className="route-disclosure">
                          El destino es una coordenada regional orientativa, no un centro de compra confirmado. Verifica la dirección real antes de iniciar el viaje.
                        </p>
                      )}
                      {routeError && <p className="route-error" role="alert">{routeError}</p>}
                      <label className="route-vehicle-select">
                        <span>Tipo de vehículo</span>
                        <select
                          className="min-h-[44px]"
                          value={vehicleType}
                          onChange={(event) => changeVehicleType(event.target.value)}
                        >
                          <option value="2AxlesAuto">Pickup / Camioneta (2 ejes)</option>
                          <option value="3AxlesTruck">Camión de carga (3+ ejes)</option>
                        </select>
                      </label>
                      {vehicleType === '3AxlesTruck' && (
                        <small className="route-disclosure">
                          TollGuru usa el perfil de 3 ejes; para vehículos de 4 o más ejes, verifica la tarifa con el operador.
                        </small>
                      )}
                      {!parcelPoint ? (
                        <>
                          <p className="route-prompt">Para calcular las rutas, primero indica el punto de partida:</p>
                          <div className="route-origin-actions">
                            <button className="min-h-[44px]" onClick={useCurrentLocation}>
                              <LocateFixed size={16} /> Usar mi ubicación
                            </button>
                            <button className="min-h-[44px]" onClick={markRouteOrigin}>
                              <MapPinned size={16} /> Marcar parcela
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="route-origin-row">
                            <p className="route-origin-status">
                              <MapPin size={15} /> Origen: {originType === 'gps' ? 'tu ubicación' : 'parcela'} · {parcelPoint[0].toFixed(4)}, {parcelPoint[1].toFixed(4)}
                            </p>
                            <button className="route-change-origin min-h-[44px]" onClick={markRouteOrigin}>Cambiar</button>
                          </div>
                          <button
                            className="route-calculate min-h-[44px]"
                            onClick={() => calculateRoutes()}
                            disabled={routeLoading}
                          >
                            <RouteIcon size={16} /> {routeLoading ? 'Calculando rutas…' : routeResult ? 'Actualizar rutas' : 'Calcular rutas'}
                          </button>
                          {routeLoading && <p className="route-loading" role="status">Consultando servicios de rutas…</p>}
                          {routeResult && (
                            <>
                              <p className={`route-mode ${routeResult.mode}`} role="status">
                                {routeResult.mode === 'api'
                                  ? routeResult.trafficAvailable
                                    ? 'Tarifas y tráfico en tiempo real vía API'
                                    : 'Tarifas vía TollGuru · tráfico actual no disponible'
                                  : routeResult.fallbackNotice}
                              </p>
                              {routeResult.mode === 'api' && (
                                <small className="route-provider">
                                  TollGuru · consultado {formatRouteQueryTime(routeResult.queriedAt)}. La hora indica consulta al servicio, no fecha oficial de publicación de la tarifa.
                                </small>
                              )}
                              {routeOptions.length === 1 && (
                                <p className="route-disclosure">
                                  {routeResult.mode === 'simulation'
                                    ? 'OSRM solo encontró una ruta viable para este trayecto.'
                                    : 'TollGuru devolvió una ruta; no hay una segunda alternativa disponible para este trayecto.'}
                                </p>
                              )}
                              <div className="route-options" aria-label="Rutas disponibles">
                                {routeOptions.map((option) => (
                                  <button
                                    key={option.id}
                                    type="button"
                                    className={`route-option min-h-[44px] ${option.id === activeRoute?.id ? 'active' : ''}`}
                                    aria-pressed={option.id === activeRoute?.id}
                                    onClick={() => setSelectedRouteId(option.id)}
                                  >
                                    <span className="route-option-heading">
                                      <strong>{option.selectionLabel}</strong>
                                      <small>{option.name}</small>
                                    </span>
                                    <span className="route-option-metrics">
                                      <span><b>Distancia</b>{option.distanceKm.toFixed(1)} km</span>
                                      <span>
                                        <b>{option.trafficSeconds === null ? 'Tiempo estimado' : 'Tiempo con tráfico'}</b>
                                        <span><Clock3 size={14} /> {formatDuration(option.trafficSeconds ?? option.durationSeconds)}</span>
                                      </span>
                                      <span>
                                        <b>Casetas</b>
                                        {option.tollTotal
                                          ? formatRouteMoney(option.tollTotal)
                                          : 'Sin datos oficiales'}
                                      </span>
                                    </span>
                                  </button>
                                ))}
                              </div>
                              <p className="route-disclosure">
                                {routeResult.mode === 'simulation'
                                  ? 'OSRM aporta geometría, distancia y tiempo estimado; no informa tráfico real ni casetas. No se muestran tarifas simuladas.'
                                  : 'Tarifas reportadas por TollGuru para el vehículo seleccionado en la moneda nativa de la respuesta. Confirma cargos y vigencia con el operador.'}
                              </p>
                              <div className="route-app-links">
                                <a
                                  className="min-h-[44px]"
                                  href={googleMapsDirectionsUrl(parcelPoint, [selectedBuyer.lat, selectedBuyer.lng])}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  Google Maps <ExternalLink size={14} />
                                </a>
                                <a
                                  className="min-h-[44px]"
                                  href={wazeDestinationUrl([selectedBuyer.lat, selectedBuyer.lng])}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  Waze <ExternalLink size={14} />
                                </a>
                              </div>
                              <p className="route-waze-note">Google Maps abre con origen y destino; Waze usa el GPS actual como origen.</p>
                              <button className="route-clear min-h-[44px]" onClick={() => invalidateRoute(false)}>
                                Limpiar rutas
                              </button>
                            </>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </aside>
              )}
            </section>
          </div>
        ) : (
          <SourcesView
            market={market}
            climate={climateRequest}
            requirements={cropRequirements}
            mappedMarkets={mappedMarketsRequest}
            exchange={exchange}
            crop={crop}
            routeResult={routeResult}
            onRefresh={() => {
              market.refresh()
              climateRequest.refresh()
              cropRequirements.refresh()
              exchange.refresh()
              mappedMarketsRequest.refresh()
            }}
            onBack={() => selectTab('observatorio')}
          />
        )}
      </main>
      {activeTab === 'observatorio' && (
        <nav className="mobile-bottom-nav" aria-label="Navegación principal">
          <button className={mobileSection === 'clima' ? 'active' : ''} onClick={() => setMobileSection('clima')}>
            <CloudSun size={19} /><span>Clima & Filtros</span>
          </button>
          <button className={mobileSection === 'crops' ? 'active' : ''} onClick={() => setMobileSection('crops')}>
            <Leaf size={19} /><span>Cultivos</span>
          </button>
          <button className={mobileSection === 'map' ? 'active' : ''} onClick={() => setMobileSection('map')}>
            <MapPin size={19} /><span>Mapa</span>
          </button>
        </nav>
      )}
    </div>
  )
}

function SourcesView({ market, climate, requirements, mappedMarkets, exchange, crop, routeResult, onRefresh, onBack }) {
  const climateSources = climate.outlook?.sources ?? {}
  const apiCrops = new Set(market.priceRecords.map((record) => record.crop))
  const displayPriceRecords = [
    ...market.priceRecords.map((record) => ({ ...record, isReferenceOnly: false })),
    ...crops
      .filter(({ name }) => !apiCrops.has(name))
      .map(({ name }) => ({
        crop: name,
        region: 'América · referencia local',
        isReferenceOnly: true,
      })),
  ]
  const sourceState = (source, loading) => {
    if (loading) return 'Consultando API'
    if (source?.connected) return 'API conectada'
    return 'Dato no disponible'
  }
  const routeSourceLabel = routeResult?.mode === 'api'
    ? 'TollGuru · datos de la consulta'
    : routeResult?.mode === 'simulation'
      ? 'OSRM · ruta de referencia, sin tráfico ni tarifas'
      : 'Pendiente de consulta'

  return (
    <div className="sources-page">
      <div className="section-heading sources-heading">
        <div>
          <span>CENTRO DE INTEGRACIÓN</span>
          <h1>Fuentes y API</h1>
        </div>
        <div className="sources-actions">
          <button className="sources-back" onClick={onBack} aria-label="Cerrar fuentes y volver al observatorio">
            <X size={16} /> Volver al observatorio
          </button>
          <button onClick={onRefresh} disabled={market.loading || climate.loading || requirements.loading || exchange.loading || mappedMarkets.loading}>
            <RefreshCw size={16} /> {market.loading || climate.loading || requirements.loading || exchange.loading || mappedMarkets.loading ? 'Consultando' : 'Actualizar fuentes'}
          </button>
        </div>
      </div>

      <div className="source-cards">
        <article>
          <div className="source-icon weather"><CloudSun size={22} /></div>
          <div>
            <span>CONDICIONES ACTUALES</span>
            <h3>Open-Meteo Forecast API</h3>
            <a href="https://open-meteo.com/en/docs" target="_blank" rel="noreferrer">Documentación</a>
          </div>
          <div className={`source-state ${climateSources.current?.connected ? '' : 'demo'}`}>
            <i /> {sourceState(climateSources.current, climate.loading)}
          </div>
          {climateSources.current?.error && <small className="source-card-error">{climateSources.current.error}</small>}
        </article>
        <article>
          <div className="source-icon weather"><Activity size={22} /></div>
          <div>
            <span>PRONÓSTICO ESTACIONAL</span>
            <h3>Open-Meteo · ECMWF</h3>
            <a href="https://open-meteo.com/en/docs/seasonal-forecast-api" target="_blank" rel="noreferrer">Documentación</a>
          </div>
          <div className={`source-state ${climateSources.seasonal?.connected ? '' : 'demo'}`}>
            <i /> {sourceState(climateSources.seasonal, climate.loading)}
          </div>
          {climateSources.seasonal?.error && <small className="source-card-error">{climateSources.seasonal.error}</small>}
        </article>
        <article>
          <div className="source-icon weather"><Activity size={22} /></div>
          <div>
            <span>HISTÓRICO / REANÁLISIS</span>
            <h3>Open-Meteo Historical Weather</h3>
            <a href="https://open-meteo.com/en/docs/historical-weather-api" target="_blank" rel="noreferrer">Documentación</a>
          </div>
          <div className={`source-state ${climateSources.historical?.connected ? '' : 'demo'}`}>
            <i /> {sourceState(climateSources.historical, climate.loading)}
          </div>
          {climateSources.historical?.error && <small className="source-card-error">{climateSources.historical.error}</small>}
        </article>
        <article>
          <div className="source-icon weather"><Leaf size={22} /></div>
          <div>
            <span>RANGOS AGRONÓMICOS</span>
            <h3>{requirements.data?.source.name ?? 'FAO ECOCROP / guías técnicas'}</h3>
            <a href={requirements.data?.source.url ?? 'https://ecocrop.review.fao.org/ecocrop/srv/en/home'} target="_blank" rel="noreferrer">Fuente de referencia</a>
          </div>
          <div className={`source-state ${requirements.data ? '' : 'demo'}`}>
            <i /> {requirements.loading
              ? 'Consultando API'
              : requirements.data
                ? `Rangos conectados · ${formatSourceDate(requirements.data.updatedAt)}`
                : requirements.isConfigured ? 'Rangos orientativos locales visibles · API sin datos válidos' : 'Rangos orientativos locales visibles · API pendiente'}
          </div>
          {requirements.error && <small className="source-card-error">{requirements.error}</small>}
          <small className="source-card-note">Sin API conectada se usan rangos ilustrativos locales, no oficiales ni verificados. La puntuación compara temperatura y humedad de Open-Meteo y no certifica aptitud productiva ni rendimiento.</small>
        </article>
        <article>
          <div className="source-icon market"><MapPin size={22} /></div>
          <div>
            <span>UBICACIONES DE MERCADOS</span>
            <h3>OpenStreetMap / Overpass API</h3>
            <a href="https://wiki.openstreetmap.org/wiki/Overpass_API" target="_blank" rel="noreferrer">API · licencia ODbL</a>
          </div>
          <div className={`source-state ${mappedMarkets.error ? 'demo' : ''}`}>
            <i /> {mappedMarkets.loading
              ? 'Consultando Overpass'
              : mappedMarkets.error
                ? 'Error al consultar'
                : `${mappedMarkets.locations.length} ubicaciones mapeadas en el área`}
          </div>
          {mappedMarkets.error && <small className="source-card-error">{mappedMarkets.error}</small>}
          <small className="source-card-note">Un punto mapeado no confirma un comprador, la compra del cultivo ni sus condiciones. Overpass es una API pública de bajo volumen; su robots.txt indica Disallow: /api/. Antes de un despliegue público, confirma la política y el volumen permitido.</small>
        </article>
        <article>
          <div className="source-icon market"><Activity size={22} /></div>
          <div>
            <span>CONVERSIÓN DE REFERENCIA</span>
            <h3>Frankfurter · MXN/USD</h3>
            <a href="https://frankfurter.dev/" target="_blank" rel="noreferrer">Documentación y proveedores</a>
          </div>
          <div className={`source-state ${exchange.rate ? '' : 'demo'}`}>
            <i /> {exchange.loading
              ? 'Consultando tipo de cambio'
              : exchange.rate
                ? `Referencia ${exchange.rate.date}`
                : 'Conversión no disponible'}
          </div>
          {exchange.error && <small className="source-card-error">{exchange.error}</small>}
        </article>
        <article>
          <div className="source-icon market"><Activity size={22} /></div>
          <div>
            <span>REFERENCIAS MAYORISTAS OFICIALES</span>
            <h3>SNIIM · USDA AMS Market News</h3>
            <a href="https://www.economia-sniim.gob.mx/" target="_blank" rel="noreferrer">SNIIM México</a>
            {' · '}
            <a href="https://mymarketnews.ams.usda.gov/mymarketnews-api/api-docs" target="_blank" rel="noreferrer">USDA AMS API</a>
          </div>
          <div className={`source-state ${market.connected ? '' : 'demo'}`}>
            <i /> {market.connected
              ? 'Datos entregados por API de mercado'
              : 'Precios orientativos locales visibles · API pendiente'}
          </div>
          <small className="source-card-note">El catálogo local es ilustrativo y no procede de SNIIM ni USDA. Cotizaciones de API se distinguen de las referencias y no equivalen a ofertas directas al agricultor.</small>
        </article>
        <article>
          <div className="source-icon market"><Activity size={22} /></div>
          <div>
            <span>PRECIOS Y COMPRADORES</span>
            <h3>{market.source?.name ?? 'API de mercado no configurada'}</h3>
            {market.source && <a href={market.source.url} target="_blank" rel="noreferrer">Fuente declarada</a>}
          </div>
          <div className={`source-state ${market.connected ? '' : 'demo'}`}>
            <i /> {market.connected
              ? 'API conectada · fuente declarada'
              : market.isConfigured ? 'Referencias locales visibles · API sin datos válidos' : 'Referencias locales visibles · API pendiente'}
          </div>
        </article>
        <article>
          <div className="source-icon market"><RouteIcon size={22} /></div>
          <div>
            <span>RUTAS, TRÁFICO Y CASETAS</span>
            <h3>{routeResult?.provider ?? 'TollGuru / OSRM'}</h3>
            <a href={routeResult?.mode === 'simulation'
              ? 'https://project-osrm.org/'
              : 'https://tollguru.com/'} target="_blank" rel="noreferrer">Proveedor</a>
          </div>
          <div className={`source-state ${routeResult?.mode === 'api' ? '' : 'demo'}`}>
            <i /> {routeSourceLabel}
          </div>
          {routeResult?.mode === 'simulation' && (
            <small className="source-card-error">{routeResult.fallbackNotice}</small>
          )}
        </article>
      </div>
      {market.error && <p className="source-error" role="alert">{market.error}</p>}
      {climate.error && <p className="source-error" role="alert">{climate.error}</p>}
      {exchange.error && <p className="source-error" role="alert">{exchange.error}</p>}

      <div className="data-panel">
        <div className="data-panel-heading">
          <div>
            <span>COTIZACIONES Y CATÁLOGO LOCAL</span>
            <h2>Precios de referencia y cotizaciones</h2>
          </div>
          <div className="last-update">Actualización de la API <strong>{market.connected
            ? market.lastUpdateLabel
            : 'Pendiente · catálogo local visible'}</strong></div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Cultivo</th>
                <th>Región</th>
                <th>Precio de referencia (MXN/USD por kg cuando la fuente lo permite)</th>
                <th>Fuente y licencia declaradas</th>
                <th>Actualización</th>
                <th>Estado de conexión</th>
              </tr>
            </thead>
            <tbody>
              {displayPriceRecords.map((record) => (
                <tr key={record.crop} className={`${crop === record.crop ? 'row-active' : ''} ${record.isReferenceOnly ? 'row-reference' : ''}`}>
                  <td><span className="table-crop">{cropIcons[record.crop]}</span><strong>{record.crop}</strong></td>
                  <td>{record.region ?? 'No especificada por la API'}</td>
                  <td className="table-price">{record.isReferenceOnly
                    ? formatReferencePrice(referenceCatalog.crops[record.crop]?.pricesPerKg)
                    : formatMarketQuote(record, exchange.rate)}</td>
                  <td>
                    {record.isReferenceOnly
                      ? 'Catálogo local ilustrativo · no oficial'
                      : market.source
                        ? <><a href={market.source.url} target="_blank" rel="noreferrer">{market.source.name}</a>{' · '}{market.source.license}</>
                        : 'Fuente de API no declarada'}
                  </td>
                  <td>{record.isReferenceOnly ? 'No aplica · valor ilustrativo' : formatSourceDate(record.updatedAt)}</td>
                  <td><span className={`table-status ${record.isReferenceOnly ? 'reference-status' : ''}`}>
                    {record.isReferenceOnly ? 'Orientativo · no oficial' : 'API conectada'}
                  </span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="sources-disclaimer">
        Las cifras del catálogo local son orientativas e ilustrativas, no son precios oficiales, ofertas directas ni datos tomados de SNIIM/USDA; los rangos y mínimos tampoco están verificados. Las cotizaciones conectadas se identifican con su API declarada. Los puntos regionales del mapa son coordenadas de referencia, no compradores ni centros de acopio confirmados. La conversión a la otra moneda solo se muestra para kg/tonelada y usa el tipo
        de cambio de referencia fechado de Frankfurter{exchange.rate ? ` (${exchange.rate.date})` : ''}; no es un precio de venta.
        La fuente y licencia de mercado son declaraciones del endpoint: la aplicación no certifica por sí sola su legalidad,
        autorización ni exactitud. Configura <code>VITE_MARKET_PRICES_API</code>
        y sirve <code>/prices</code> desde un origen HTTPS con <code>source</code> (name, URL HTTPS y licencia),
        <code>updatedAt</code>, <code>prices</code> y, opcionalmente, <code>buyers</code>. No uses scraping ni fuentes que
        no autoricen la reutilización. Los datos de mercado mayorista SNIIM/USDA no deben etiquetarse como ofertas de compra
        al agricultor; comprador, mínimo y condiciones solo se confirman cuando los entrega una fuente verificable.
      </p>

      <div className="sources-disclaimer">
        Atribución: datos meteorológicos de <a href="https://open-meteo.com/" target="_blank" rel="noreferrer">Open-Meteo</a>
        {' '}bajo <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a>;
        {' '}la API gratuita es solo para uso no comercial. Las condiciones actuales son del modelo, no de una estación.
        {' '}El pronóstico estacional se basa en ECMWF
        (~36 km, sin corrección de sesgo). Mapa: © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a>.
        {' '}Los puntos de mercados consultados en Overpass son datos ODbL y no verifican compradores. Las tasas de Frankfurter son de referencia, no tasas de operación intradía.
        {' '}Las rutas provienen de TollGuru cuando la API está conectada; OSRM solo aporta geometría/tiempo estimado,
        sin tarifas ni tráfico en el modo de respaldo.
        {' '}Privacidad: al usar GPS o marcar una parcela, las coordenadas se envían a los proveedores necesarios para consultar clima, ubicaciones o rutas; no se guardan como perfil en esta aplicación.
      </div>

      <details className="json-panel">
        <summary><Database size={16} /> Contrato del endpoint de mercado</summary>
        <p>
          Cada cotización debe declarar un valor numérico devuelto por la fuente, moneda MXN/USD, unidad y fecha.
          Cada comprador debe incluir identificador, nombre, ciudad, país, coordenadas, cultivos y cotizaciones; puede declarar
          <code> minimumOrder </code> y <code>deliveryTerms</code> si la fuente los confirma. Las tendencias y clima local
          solo se muestran si el endpoint aporta esos valores y fechas.
          Las claves de cultivo deben pertenecer al catálogo; no se completan campos con estimaciones locales.
          Verifica la licencia, uso permitido y atribución del proveedor antes de publicar o usar los rangos comercialmente.
        </p>
      </details>
      <details className="json-panel">
        <summary><Leaf size={16} /> Contrato de rangos agronómicos</summary>
        <p>
          Configura <code>VITE_CROP_REQUIREMENTS_API</code> para consultar <code>/requirements</code> con
          <code> source</code> (name, URL HTTPS y licencia), <code>updatedAt</code> y <code>crops</code>.
          Cada cultivo requiere <code>temperatureC</code> y <code>humidityPercent</code>, con <code>min</code>,
          <code>optimum</code> y <code>max</code> respaldados por la fuente. La app calcula el porcentaje como una
          puntuación lineal respecto al óptimo; “Compatible” significa al menos 70% y es solo una estimación climática.
        </p>
      </details>
    </div>
  )
}
