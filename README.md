# tdl-climatico-Proyecto-ING-DATOS

Observatorio de Inteligencia Climática y Gestión de Riesgos Agrícolas para Colima, Tecomán y Manzanillo.

El repositorio integra Open-Meteo, limpieza de datos, linaje verificable y una fuente geoespacial experimental de OpenStreetMap.

## Ejecutar

```powershell
pip install -r requirements.txt
python -m pipeline.run_pipeline
pytest tests -q
streamlit run tablero/app.py
```

## Estado verificable

- 3495 registros de bronce leídos en la última ejecución local.
- 3294 registros aprobados en plata.
- 111 filas mensuales en oro.
- 13,176 valores revisados por linaje y 0 fallos.
- Dataset curado E3: 3294 filas × 29 columnas; sin nulos en los campos publicados.
- Suite raíz: 74 pruebas aprobadas y 4 omitidas.

## Entregas

- E2: [docs/E2/ENTREGA.md](docs/E2/ENTREGA.md)
- E3: [docs/E3/ENTREGA.md](docs/E3/ENTREGA.md)
- E0: [docs/E0/ENTREGA.md](docs/E0/ENTREGA.md)
- E1: [docs/E1/ENTREGA.md](docs/E1/ENTREGA.md)
- Datasheet E3: [docs/E3/datasheet.md](docs/E3/datasheet.md)
- Relatoría E3: [docs/relatoria-E3.md](docs/relatoria-E3.md)
- Dataset curado: [data/curated/](data/curated/)
- Ética y legalidad: [docs/etica-datos.md](docs/etica-datos.md)
- Relatoría E2: [docs/relatoria-E2.md](docs/relatoria-E2.md)
- Plan SQA: [docs/plan-SQA.md](docs/plan-SQA.md)
- Datasheet general: [docs/DATASHEET.md](docs/DATASHEET.md)

## Benchmark y dataset curado E3

```powershell
python scripts\benchmark_e3.py --runs 3
python -m pipeline.run_pipeline
python scripts\curate_e3.py
```

El benchmark compara el código base fijado en el reporte con el pipeline actual,
sin peticiones de red, y verifica que las capas generadas sean idénticas.
Consulta [`docs/E3/benchmark.json`](docs/E3/benchmark.json) para métricas y
[`data/curated/LICENSE-DATA.md`](data/curated/LICENSE-DATA.md) para atribución y licencia.

## Prototipo web React

La interfaz "Observatorio Climático & Mercado América" está en [frontend/](frontend/) y utiliza React,
Tailwind CSS, Leaflet, Recharts y Lucide React.

```powershell
cd frontend
npm install
npm run dev
```

El catálogo local contiene referencias ilustrativas de precios, mínimos y rangos
climáticos; no son cotizaciones, compradores confirmados ni recomendaciones
agronómicas. Los puntos de OSM son ubicaciones mapeadas y no prueban que compren
un cultivo. La app puede conectar cotizaciones mediante `VITE_MARKET_PRICES_API`
en `frontend/.env.local`; requiere metadatos de fuente, URL HTTPS, licencia y
fecha, pero esos metadatos no certifican por sí mismos la legalidad del origen.
Consulta [frontend/README.md](frontend/README.md) y [docs/etica-datos.md](docs/etica-datos.md).
No se implementa scraping de páginas web.

La ficha de compradores también permite comparar hasta dos rutas desde la parcela y
ver casetas con tarifas reportadas por TollGuru. Configura `TOLLGURU_API_KEY` como
secreto del proxy del servidor (nunca como variable `VITE_*`); sin proxy o si el
proveedor falla, se muestran rutas OSRM de referencia sin tráfico ni precios de casetas.
El clima usa Open-Meteo Forecast, Seasonal Forecast y Historical Weather APIs;
el plan gratuito solo permite uso no comercial y requiere atribución CC BY 4.0.
La app consulta Overpass para ubicaciones mapeadas y OSRM para rutas de
referencia; ninguno proporciona compradores, tráfico en tiempo real ni tarifas
oficiales. El mapa atribuye OpenStreetMap y sus tiles. La geolocalización del
navegador requiere acción y permiso del usuario; las coordenadas se envían a los
servicios seleccionados para consultar clima, lugares o rutas. Revisa las
condiciones de cada proveedor antes de un despliegue público o comercial.
