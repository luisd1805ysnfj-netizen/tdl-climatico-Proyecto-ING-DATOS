import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import {
  Activity, CloudSun, CloudRain, Droplets, Leaf, MapPin,
  Search, ThermometerSun, TrendingDown, TrendingUp, Users, Wind,
  X, Database, RefreshCw, ChevronRight, Menu, LocateFixed, MapPinned,
} from 'lucide-react'
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip as ChartTooltip,
  XAxis, YAxis, Line,
} from 'recharts'
import { crops, regions, buyers, REFERENCE_MXN_PER_USD } from './data/agtechData'
import { useMarketPricesAPI } from './hooks/useMarketPricesAPI'
import { useClimateOutlook } from './hooks/useClimateOutlook'
import { createFallbackClimateOutlook } from './services/openMeteo'

const cropIcons = {
  Zanahoria: '🥕', Cebolla: '🧅', Zarzamora: '🫐', Maíz: '🌽', Tomate: '🍅',
  Aguacate: '🥑', Limón: '🍋', Fresa: '🍓', 'Chile Jalapeño': '🌶️', Papa: '🥔',
  Pepino: '🥒', Brócoli: '🥦', Mango: '🥭', Plátano: '🍌', Calabacita: '🥒', Uva: '🍇',
  Coco: '🥥', Papaya: '🍈', Sandía: '🍉', Melón: '🍈', 'Chile verde': '🫑',
}

const continentMapBuyerIds = new Set([5, 19, 20, 27, 28, 29, 30, 31])

const priceInMxn = (amount, currency) => currency === 'USD'
  ? amount * REFERENCE_MXN_PER_USD
  : amount

const formatDualPrice = (amountMxn, priority = 'Ambos', unit = 'kg') => {
  const mxn = `$${amountMxn.toFixed(2)} MXN / ${unit}`
  const usd = `$${(amountMxn / REFERENCE_MXN_PER_USD).toFixed(2)} USD / ${unit}`
  if (priority === 'USD') return `${usd} (≈ ${mxn})`
  return `${mxn} (≈ ${usd})`
}

const formatBuyerPrice = (buyer, crop, priority) =>
  formatDualPrice(priceInMxn(buyer.prices[crop], buyer.currency), priority, buyer.unit ?? 'kg')

const buyerPriceDisclosure = (buyer) => buyer.isReference
  ? 'Estimación de mercado; no es una cotización confirmada.'
  : 'Precio de una fuente conectada; comprador y oferta no verificados.'

const buyerTrendLabel = (trend) => trend === 'up'
  ? 'al alza'
  : trend === 'down' ? 'a la baja' : 'estable'

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

const buyerIcon = (color = '#1f5f3a') => L.divIcon({
  className: 'buyer-marker',
  html: `<div style="background:${color}"><span>$</span></div>`,
  iconSize: [42, 42],
  iconAnchor: [21, 42],
  popupAnchor: [0, -38],
})

function MapFitBuyers({ buyers, fallbackCenter, fallbackZoom, refreshKey, focusPoint }) {
  const map = useMap()
  useEffect(() => {
    let fitFrame
    const resizeFrame = window.requestAnimationFrame(() => {
      map.invalidateSize()
      fitFrame = window.requestAnimationFrame(() => {
        if (buyers.length === 1 && !focusPoint) {
          map.flyTo([buyers[0].lat, buyers[0].lng], Math.min(fallbackZoom + 3, 10), { duration: 0.8 })
          return
        }
        if (buyers.length > 1) {
          const points = buyers.map(({ lat, lng }) => [lat, lng])
          if (focusPoint) points.push(focusPoint)
          const bounds = L.latLngBounds(points)
          map.flyToBounds(bounds, { padding: [36, 36], maxZoom: 9, duration: 0.8 })
          return
        }
        if (focusPoint && buyers.length === 1) {
          const bounds = L.latLngBounds([focusPoint, [buyers[0].lat, buyers[0].lng]])
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
  }, [map, buyers, fallbackCenter, fallbackZoom, refreshKey, focusPoint])
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

function climateFromPoint(lat, lng) {
  const latitude = Math.abs(lat)
  const temperature = Math.round(30 - latitude * 0.27 + (lng > -70 ? 1 : 0))
  const humidity = Math.max(48, Math.min(82, Math.round(74 - Math.abs(lat) * 0.18)))
  const rain = Math.max(2, Math.round(18 - Math.abs(lat - 20) * 0.18))
  return {
    city: `Parcela ${lat.toFixed(3)}, ${lng.toFixed(3)}`,
    condition: temperature >= 26 ? 'Cálido y parcialmente soleado' : 'Templado y parcialmente nublado',
    temperature,
    humidity,
    rain,
    wind: Math.max(5, Math.round(8 + (Math.abs(lng) % 9))),
    feels: temperature + (humidity > 70 ? 1 : 0),
  }
}

function Metric({ icon: Icon, label, value, unit }) {
  return (
    <div className="metric-card">
      <div className="metric-icon"><Icon size={18} /></div>
      <div>
        <span>{label}</span>
        <strong>{value}<small>{unit}</small></strong>
      </div>
    </div>
  )
}

export default function App() {
  const [crop, setCrop] = useState('Zanahoria')
  const [region, setRegion] = useState('AMERICA')
  const [cropSearch, setCropSearch] = useState('')
  const [cropFilter, setCropFilter] = useState('todos')
  const [markParcel, setMarkParcel] = useState(false)
  const [parcelPoint, setParcelPoint] = useState(null)
  const [weatherOverride, setWeatherOverride] = useState(null)
  const [locationStatus, setLocationStatus] = useState('')
  const [activeTab, setActiveTab] = useState('observatorio')
  const [selectedBuyer, setSelectedBuyer] = useState(null)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mobileSection, setMobileSection] = useState('clima')
  const [priceMode, setPriceMode] = useState('Ambos')
  const [showAllCrops, setShowAllCrops] = useState(false)
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia('(max-width: 767px)').matches,
  )
  const market = useMarketPricesAPI()

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
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mobileOpen, selectedBuyer])

  const regionData = weatherOverride ?? regions[region]
  const getReferencePriceMXN = (name, fallbackPrice) => {
    const quote = market.prices[name]
    if (!quote) return fallbackPrice
    return quote.currency === 'USD' ? quote.price * REFERENCE_MXN_PER_USD : quote.price
  }
  const formatReferencePrice = (price) => formatDualPrice(price, priceMode)
  const selectedLocation = {
    latitude: weatherOverride?.latitude ?? regionData.latitude,
    longitude: weatherOverride?.longitude ?? regionData.longitude,
  }
  const climateRequest = useClimateOutlook(selectedLocation, regionData)
  const forecast = climateRequest.outlook ??
    createFallbackClimateOutlook(selectedLocation.latitude, regionData)
  const currentWeather = forecast.current ?? regionData
  const visibleBuyers = useMemo(() => {
    const cropBuyers = buyers.filter((buyer) => buyer.crops.includes(crop))
    if (!parcelPoint) {
      return cropBuyers.filter((buyer) => region === 'AMERICA'
        ? continentMapBuyerIds.has(buyer.id)
        : buyer.country === region || (region === 'Colima' && buyer.state === 'Colima'))
    }

    const nearestBuyers = cropBuyers
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
  }, [crop, parcelPoint, region])
  const forecastTemperature = useMemo(() => {
    const values = forecast.chart.map((month) => month.predicción)
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : regionData.temperature
  }, [forecast.chart, regionData.temperature])
  const rankedCrops = crops
    .map((item) => {
      const idealTemperature = (item.climate.temp[0] + item.climate.temp[1]) / 2
      const idealHumidity = (item.climate.humidity[0] + item.climate.humidity[1]) / 2
      const temperatureOutsideRange = Math.max(
        item.climate.temp[0] - forecastTemperature,
        0,
        forecastTemperature - item.climate.temp[1],
      )
      const humidityOutsideRange = Math.max(
        item.climate.humidity[0] - forecast.humidity,
        0,
        forecast.humidity - item.climate.humidity[1],
      )
      const climateScore = 96 - temperatureOutsideRange * 4 -
        humidityOutsideRange * 0.55 -
        (Math.abs(forecastTemperature - idealTemperature) +
          Math.abs(forecast.humidity - idealHumidity) / 8) * 0.2
      return {
        ...item,
        compatibility: Math.round(Math.max(35, Math.min(99, climateScore))),
        livePrice: getReferencePriceMXN(item.name, item.price),
      }
    })
    .sort((a, b) => b.compatibility - a.compatibility)

  const normalizedSearch = normalizeText(cropSearch.trim())
  const matchingCrops = crops.filter((item) =>
    (cropFilter === 'todos' || item.type === cropFilter) &&
    normalizeText(item.name).includes(normalizedSearch),
  )
  const matchingCropNames = new Set(matchingCrops.map(({ name }) => name))
  const filteredCrops = showAllCrops ? matchingCrops : matchingCrops.slice(0, 6)
  const visibleRankedCrops = rankedCrops.filter((item) => matchingCropNames.has(item.name))

  const selectCrop = (name) => {
    setCrop(name)
    setSelectedBuyer(null)
    setMobileOpen(false)
    if (isMobile) setMobileSection('map')
  }

  const selectTab = (tab) => {
    setActiveTab(tab)
    setMobileOpen(false)
    setSelectedBuyer(null)
  }

  const clearCropFilters = () => {
    setCropSearch('')
    setCropFilter('todos')
    setShowAllCrops(false)
  }

  const setPointAndWeather = (lat, lng) => {
    const climate = climateFromPoint(lat, lng)
    setParcelPoint([lat, lng])
    setWeatherOverride({ ...climate, latitude: lat, longitude: lng, mapCenter: [lat, lng], zoom: 12 })
    setRegion('AMERICA')
    setLocationStatus('Parcela marcada')
    setMarkParcel(false)
  }

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Geolocalización no disponible')
      return
    }
    setLocationStatus('Detectando ubicación...')
    navigator.geolocation.getCurrentPosition(
      (position) => setPointAndWeather(position.coords.latitude, position.coords.longitude),
      () => setLocationStatus('No se pudo obtener tu ubicación'),
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
                    <small>{formatReferencePrice(getReferencePriceMXN(item.name, item.price))}</small>
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
                setRegion(event.target.value)
                setWeatherOverride(null)
                setParcelPoint(null)
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
              <span className="live-badge"><i /> EN VIVO</span>
            </div>

            <div className="location-actions">
              <button className="min-h-[44px]" onClick={useCurrentLocation}><LocateFixed size={15} /> Usar mi ubicación</button>
              <button className={`min-h-[44px] ${markParcel ? 'active' : ''}`} onClick={() => setMarkParcel((value) => !value)}>
                <MapPinned size={15} /> {markParcel ? 'Clic en el mapa' : 'Marcar parcela'}
              </button>
            </div>
            {locationStatus && <small className="location-status">{locationStatus}</small>}

            <div className="weather-primary">
              <CloudSun size={48} strokeWidth={1.5} />
              <div>
                <strong>{currentWeather.temperature}°</strong>
                <span>{currentWeather.condition ?? regionData.condition}</span>
              </div>
            </div>

            <div className="metrics-grid">
              <Metric icon={Droplets} label="Humedad" value={currentWeather.humidity} unit="%" />
              <Metric icon={CloudRain} label="Precipitación" value={currentWeather.rain} unit=" mm" />
              <Metric icon={Wind} label="Viento" value={currentWeather.wind} unit=" km/h" />
              <Metric icon={ThermometerSun} label="Sensación" value={currentWeather.feels} unit="°C" />
            </div>

            <div className="forecast-card">
              <div className="forecast-top">
                <div>
                  <span>Tendencia mensual</span>
                  <strong>{forecast.summary}{climateRequest.loading ? ' · actualizando' : ''}</strong>
                </div>
                <div className="forecast-range">{forecast.range}</div>
              </div>
              <div className="forecast-chart">
                {(!isMobile || mobileSection === 'clima') && (
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
                    <XAxis dataKey="month" interval={0} minTickGap={0} tick={{ fontSize: 9, fill: '#758076' }} axisLine={false} tickLine={false} />
                    <YAxis hide domain={['dataMin - 2', 'dataMax + 2']} />
                    <YAxis yAxisId="humidity" hide orientation="right" domain={[30, 100]} />
                    <ChartTooltip />
                    <Area type="monotone" dataKey="historico" stroke="#728b74" fill="url(#history)" strokeWidth={2} />
                    <Area type="monotone" dataKey="predicción" stroke="#d89332" fill="url(#prediction)" strokeWidth={2} />
                    <Line yAxisId="humidity" type="monotone" dataKey="humedad" stroke="#347b83" strokeWidth={1.5} dot={false} />
                  </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
              <p>{forecast.source}; próximos 5 meses. Hemisferio {selectedLocation.latitude < 0 ? 'sur' : 'norte'}; humedad mensual en el gráfico.</p>
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
              {market.error ? 'Error en precios' : market.isLive ? 'API de precios configurada' : 'Precios de referencia'}
            </span>
            <button onClick={market.refresh} disabled={market.loading}>
              <RefreshCw size={15} /> {market.loading ? 'Consultando' : 'Actualizar'}
            </button>
          </div>
          <label className="currency-control">
            <span>Precios</span>
            <select aria-label="Priorizar moneda de precios" value={priceMode} onChange={(event) => setPriceMode(event.target.value)}>
              <option>Ambos</option>
              <option>MXN</option>
              <option>USD</option>
            </select>
          </label>
        </header>

        {activeTab === 'observatorio' ? (
          <div className="dashboard grid md:grid-cols-2">
            <section className={`recommendations ${mobileSection !== 'crops' ? 'mobile-hidden' : ''}`}>
              <div className="section-heading">
                <div>
                  <span>INTELIGENCIA CLIMÁTICA</span>
                  <h1>Cultivos compatibles</h1>
                </div>
                <p>Para <strong>{regionData.city}</strong> · próximos 90 días</p>
              </div>
              <div className="recommendation-count" aria-live="polite">
                {matchingCrops.length} {matchingCrops.length === 1 ? 'cultivo' : 'cultivos'} · precios de referencia en MXN y USD/kg
              </div>

              <div className="crop-list">
                {visibleRankedCrops.map((item, index) => (
                  <article className={`crop-card ${crop === item.name ? 'highlight' : ''}`} key={item.name}>
                    <div className="crop-rank">{String(index + 1).padStart(2, '0')}</div>
                    <div className="crop-emoji">{cropIcons[item.name]}</div>
                    <div className="crop-info">
                      <h3><button className="crop-name-button" onClick={() => selectCrop(item.name)}>{item.name}</button></h3>
                      <div className="compatibility">
                        <span style={{ width: `${item.compatibility}%` }} />
                      </div>
                      <strong>{item.compatibility}% <em>{item.compatibility >= 90 ? 'Óptimo' : 'Compatible'}</em></strong>
                    </div>
                    <div className="crop-price">
                      <span>Precio de referencia</span>
                      <strong>{formatReferencePrice(item.livePrice)}</strong>
                    </div>
                    <button onClick={() => selectCrop(item.name)}>
                      Ver compradores <ChevronRight size={16} />
                    </button>
                  </article>
                ))}
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
                  <span>RED DE COMPRADORES</span>
                  <h2>{crop}</h2>
                </div>
                <div className="map-count"><Users size={16} /> {visibleBuyers.length} puntos activos</div>
              </div>
              <div className="map-frame min-h-[420px]">
                {(!isMobile || mobileSection === 'map') ? (
                  <MapContainer
                    center={weatherOverride?.mapCenter ?? regionData.mapCenter}
                    zoom={weatherOverride?.zoom ?? regionData.zoom}
                    scrollWheelZoom
                    className="leaflet-map"
                  >
                  <MapFitBuyers
                  buyers={visibleBuyers}
                  fallbackCenter={weatherOverride?.mapCenter ?? regionData.mapCenter}
                  fallbackZoom={weatherOverride?.zoom ?? regionData.zoom}
                  refreshKey={`${mobileSection}-${activeTab}`}
                  focusPoint={parcelPoint}
                  />
                  <MapClickHandler enabled={markParcel} onSelect={(lat, lng) => {
                    setPointAndWeather(lat, lng)
                  }} />
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {parcelPoint && (
                    <Marker position={parcelPoint} icon={parcelIcon}>
                      <Popup>
                        <div className="buyer-popup">
                          <strong>Mi parcela</strong>
                          <span>{parcelPoint[0].toFixed(4)}, {parcelPoint[1].toFixed(4)}</span>
                          <b>{regionData.temperature}°C</b>
                        </div>
                      </Popup>
                    </Marker>
                  )}
                  {visibleBuyers.map((buyer) => (
                    <Marker
                      key={buyer.id}
                      position={[buyer.lat, buyer.lng]}
                      icon={buyerIcon(buyer.trend === 'up' ? '#d89332' : '#215f3a')}
                      eventHandlers={{ click: () => setSelectedBuyer(buyer) }}
                    >
                      <Popup>
                        <div className="buyer-popup">
                          <strong>{buyer.name}</strong>
                          <span>{buyer.city}, {buyer.country}</span>
                          <small>Precio de compra al productor · {buyer.unit}</small>
                          <b>{formatBuyerPrice(buyer, crop, priceMode)}</b>
                          <small className="buyer-reference">{buyerPriceDisclosure(buyer)}</small>
                          <small>Fuente: {buyer.source}</small>
                          <small>Unidad: {buyer.unit}</small>
                          <small>Volumen mínimo: {buyer.minimumVolume}</small>
                          <small>{buyer.conditions}</small>
                          <small><Activity size={13} /> Tendencia {buyerTrendLabel(buyer.trend)} · {buyer.trendValue}</small>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                  </MapContainer>
                ) : <div className="map-placeholder">Abre la pestaña Mapa para explorar compradores.</div>}
              </div>

              {selectedBuyer && (
                <aside className="buyer-drawer">
                  <button className="drawer-close" aria-label="Cerrar detalle del comprador" onClick={() => setSelectedBuyer(null)}><X size={18} /></button>
                  <span className="drawer-label">COMPRADOR SELECCIONADO</span>
                  <h3>{selectedBuyer.name}</h3>
                  <p><MapPin size={15} /> {selectedBuyer.city}, {selectedBuyer.country}</p>
                  <div className="drawer-price">
                    <span>Precio de compra al productor</span>
                    <strong>{formatBuyerPrice(selectedBuyer, crop, priceMode)}</strong>
                    <small className="buyer-reference">{buyerPriceDisclosure(selectedBuyer)}</small>
                    <small>Fuente: {selectedBuyer.source}</small>
                    <span>Unidad: {selectedBuyer.unit}</span>
                    <span>Volumen mínimo: {selectedBuyer.minimumVolume}</span>
                    <small>{selectedBuyer.conditions}</small>
                  </div>
                  <div className="drawer-trend">
                    {selectedBuyer.trend === 'up'
                      ? <TrendingUp size={18} />
                      : selectedBuyer.trend === 'down' ? <TrendingDown size={18} /> : <Activity size={18} />}
                    <div>
                      <span>Tendencia de 30 días</span>
                      <strong>{buyerTrendLabel(selectedBuyer.trend)} · {selectedBuyer.trendValue}</strong>
                    </div>
                  </div>
                  <div className="drawer-weather">
                    <CloudSun size={20} />
                    <span>{selectedBuyer.localWeather}</span>
                  </div>
                  <div className="drawer-note">No hay contacto verificado para este punto de referencia.</div>
                </aside>
              )}
            </section>
          </div>
        ) : (
          <SourcesView
            market={market}
            crop={crop}
            region={region}
            formatReferencePrice={formatReferencePrice}
            getReferencePriceMXN={getReferencePriceMXN}
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

function SourcesView({ market, crop, region, formatReferencePrice, getReferencePriceMXN, onBack }) {
  return (
    <div className="sources-page">
      <div className="section-heading sources-heading">
        <div>
          <span>CENTRO DE INTEGRACIÓN</span>
          <h1>Fuente de Datos y API de Precios</h1>
        </div>
        <div className="sources-actions">
          <button className="sources-back" onClick={onBack} aria-label="Cerrar fuentes y volver al observatorio">
            <X size={16} /> Volver al observatorio
          </button>
          <button onClick={market.refresh} disabled={market.loading}>
            <RefreshCw size={16} /> {market.loading ? 'Consultando' : 'Reconectar fuentes'}
          </button>
        </div>
      </div>

      <div className="source-cards">
        <article>
          <div className="source-icon weather"><CloudSun size={22} /></div>
          <div>
            <span>API METEOROLÓGICA</span>
            <h3>Tiempo real + histórico</h3>
          </div>
          <div className="source-state"><i /> Conectada</div>
        </article>
        <article>
          <div className="source-icon market"><Activity size={22} /></div>
          <div>
            <span>API DE PRECIOS AGRÍCOLAS</span>
            <h3>Compra a productor</h3>
          </div>
          <div className={`source-state ${market.connected ? '' : 'demo'}`}>
            <i /> {market.connected ? 'API conectada' : market.isLive ? 'Endpoint configurado' : 'Precios de referencia'}
          </div>
        </article>
      </div>
      {market.error && <p className="source-error" role="alert">{market.error}</p>}

      <div className="data-panel">
        <div className="data-panel-heading">
          <div>
            <span>TABLA DE REFERENCIA</span>
            <h2>Precios por cultivo · {regions[region].label}</h2>
          </div>
          <div className="last-update">Última actualización <strong>{market.lastUpdate}</strong></div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Cultivo</th>
                <th>Región</th>
                <th>Precio de referencia (MXN y USD/kg)</th>
                <th>Tendencia</th>
                <th>Actualización</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {crops.map((item) => (
                <tr key={item.name} className={crop === item.name ? 'row-active' : ''}>
                  <td><span className="table-crop">{cropIcons[item.name]}</span><strong>{item.name}</strong></td>
                  <td>{regions[region].label}</td>
                  <td className="table-price">{formatReferencePrice(getReferencePriceMXN(item.name, item.price))}</td>
                  <td className={item.trend === 'up' ? 'trend-up' : 'trend-flat'}>
                    {item.trend === 'up' ? <TrendingUp size={15} /> : <Activity size={15} />}
                    {item.trendValue}
                  </td>
                  <td>{market.lastUpdate}</td>
                  <td><span className="table-status">{market.connected ? 'API' : 'Referencia'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="sources-disclaimer">
        Los precios de la tabla y de las fichas de compradores son estimaciones de referencia, no cotizaciones oficiales
        ni ofertas confirmadas. Los compradores y sus condiciones no están verificados. La base está expresada en MXN y
        se convierte con una tasa referencial configurable de {` ${REFERENCE_MXN_PER_USD.toFixed(2)} MXN/USD`}.
        Conectar una API de precios por cultivo no verifica compradores ni ofertas puntuales. Para conectar precios reales,
        configura <code>VITE_MARKET_PRICES_API</code> y publica
        <code> /prices</code> con un objeto JSON <code>{'{ prices: { [cultivo]: { price, currency, unit } } }'}</code>.
      </p>

      <details className="json-panel">
        <summary><Database size={16} /> Ver estructura JSON modular</summary>
        <pre>{`{
  "market": "market_prices_api",
  "crop": "Zanahoria",
  "region": "México",
  "price": 10.8,
  "currency": "MXN",
  "unit": "kg",
  "updatedAt": "2026-11-26T20:00:00Z",
  "source": "referencia",
  "isReference": true
}`}</pre>
      </details>
    </div>
  )
}
