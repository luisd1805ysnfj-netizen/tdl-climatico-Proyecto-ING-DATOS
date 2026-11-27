# tdl-climatico-Proyecto-ING-DATOS

Observatorio de Inteligencia Climática y Gestión de Riesgos Agrícolas para Colima, Tecomán y Manzanillo.

El repositorio integra Open-Meteo, limpieza de datos, linaje verificable y una fuente geoespacial experimental de OpenStreetMap.

## Ejecutar

```powershell
pip install -r requirements.txt
python -m pipeline.run_pipeline
pytest tests/test_linaje.py tests/test_osm_offline.py tests/test_pipeline.py tests/test_open_meteo_offline.py -q
streamlit run tablero/app.py
```

## Estado verificable

- 3495 registros de bronce leídos en la última ejecución local.
- 3294 registros aprobados en plata.
- 111 filas mensuales en oro.
- 13,176 valores revisados por linaje y 0 fallos.
- 66 pruebas aprobadas y 4 omitidas.

## Entregas

- E2: [docs/E2/ENTREGA.md](docs/E2/ENTREGA.md)
- Ética y legalidad: [docs/etica-datos.md](docs/etica-datos.md)
- Relatoría E2: [docs/relatoria-E2.md](docs/relatoria-E2.md)
- DataSheet E3: [docs/DATASHEET.md](docs/DATASHEET.md)

## Prototipo web React

La interfaz "Observatorio Climático & Mercado América" está en [frontend/](frontend/) y utiliza React,
Tailwind CSS, Leaflet, Recharts y Lucide React.

```powershell
cd frontend
npm install
npm run dev
```

Los precios y puntos incluidos en el prototipo son referencias ilustrativas, no cotizaciones oficiales ni
ofertas/compradores confirmados. Los precios de las fichas del mapa son estimaciones y conectar la API de
precios por cultivo no verifica compradores ni sus ofertas o condiciones. Para conectar una fuente real,
configura `VITE_MARKET_PRICES_API` en
`frontend/.env.local`; la aplicación consultará `${VITE_MARKET_PRICES_API}/prices`. El endpoint debe
responder con un objeto `prices` cuyas claves sean nombres de cultivo y cuyos valores incluyan `price`,
`currency` (`MXN` o `USD`) y `unit` (`kg`). La tasa dual se configura con
`VITE_MXN_PER_USD_RATE` (por defecto, `20.00`).
