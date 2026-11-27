# Entrega E2 · Observatorio de Inteligencia Climática y Gestión de Riesgos Agrícolas (Colima, Tecomán y Manzanillo)

Equipo registrado en E0: Luis Alfredo Ruiz Fuentes y Ariadna Andrea Muñoz Andrade · Tag `e2` existente · Tablero: no hay URL pública registrada.

> Los enlaces son relativos al repositorio y funcionan en GitHub dentro de la etiqueta `e2`.

## Resumen en tres líneas
1. **Fuente avanzada integrada:** Open-Meteo Archive alimenta Bronce y Open-Meteo Forecast/Seasonal alimentan el frontend. El extractor geoespacial de OSM está implementado y probado offline, pero no hay captura real persistida.
2. **Ética y legalidad:** `docs/etica-datos.md` registra licencias, términos consultados, `robots.txt`, privacidad, sesgos y la limitación de no asumir que una API pública equivale a permiso ilimitado.
3. **Linaje:** cada valor de la capa oro apunta a su archivo de bronce, su huella SHA-256, su posición y su fecha de ingesta; una prueba automática abre los archivos y lo comprueba. Ejecución actual: 13,176 valores revisados, 13,176 trazables y 0 fallos.

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Fuente especializada (45) | [`extractors/clima_extractor.py`](../../extractors/clima_extractor.py) · [`frontend/src/services/openMeteo.js`](../../frontend/src/services/openMeteo.js) · [`extractors/osm_overpass.py`](../../extractors/osm_overpass.py) · [`tests/test_osm_offline.py`](../../tests/test_osm_offline.py) | Open-Meteo está integrado. El extractor y pruebas OSM son experimentales/offline; no hay `osm_agricola_*.json` real y no se reportan superficies agrícolas obtenidas. |
| Declaración de ética y legalidad (30) | [`docs/etica-datos.md`](../etica-datos.md) | Distingue endpoints API de scraping de páginas, documenta fuentes/atribución y deja Overpass condicionado a verificar política y escala antes de automatizar o desplegar públicamente. |
| Linaje de datos (15) | [`pipeline/oro.py`](../../pipeline/oro.py) (`agregar_linaje`, `verificar_linaje`) · [`tests/test_linaje.py`](../../tests/test_linaje.py) · [`data/oro/reporte_linaje.json`](../../data/oro/reporte_linaje.json) · [`diccionario_datos.md`](../E1/diccionario_datos.md) | `origen_<variable>` = `archivo\|huella12\|fila` o `IMPUTADO:<método>`; `id_registro` estable; `fecha_captura` = fecha de ingesta; el oro mensual declara `primer_dia`, `ultimo_dia` y `ultima_ingesta`. La verificación **falla el pipeline** si algo no se puede rastrear. |

### Cómo se rastrea un valor (ejemplo para la defensa)
1. En `data/oro/clima_oro_diario.csv`, tomar una fila y leer `origen_tmax_c`, p. ej. `clima_historico_colima_20261109.json|2444c990bd3a|0`.
2. Abrir ese archivo en `data/bronce/`: su SHA-256 empieza con `2444c990bd3a`.
3. En `daily.time[0]` está la fecha y en `daily.temperature_2m_max[0]` el valor: son los mismos de la fila de oro.
4. Si el valor fue imputado, `origen_tmax_c` dice `IMPUTADO:<método>` y `tmax_c_imputado` es `True`: está declarado, no escondido.

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Diseño y principios (factorial 2³) | No entregado | No hay diseño ejecutado ni hipótesis documentadas en esta versión. |
| Dos factores con interacción | No entregado | No se calculó interacción factorial. |
| Completo vs. fraccionado | No entregado | No se documentó resolución ni comparación de diseños. |
| Análisis y confirmación | No entregado | No hay ANOVA ni modelo equivalente. |

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Evaluación ISO/IEC 25010 | Evidencia parcial: 74 pruebas aprobadas, 4 omitidas; benchmark E3 reproducible | El tiempo de replay se midió; `tracemalloc` representa asignaciones Python, no RAM total. |
| Evaluación ISO/IEC 25012 | Evidencia parcial: linaje 100 % trazable y 0 fallos | Cubre precisión, trazabilidad y consistencia sobre la capa oro. |
| Antecedentes normativos | [`docs/etica-datos.md`](../etica-datos.md) | Documenta licencias, privacidad, sesgos y uso académico. |
| Auditoría cruzada | Pendiente de acta | Periodo objetivo del 19 al 23 de noviembre de 2026. |

## Relatoría de etapa
Enlace a [`docs/relatoria-E2.md`](../relatoria-E2.md)

## Issues de la entrega anterior
No se consultó el tracker de GitHub durante esta auditoría; no se afirma que no existan issues. Workflow, pruebas offline y CI están versionados en el repositorio.

## Cómo reproducir
```bash
pip install -r requirements.txt
python -m pipeline.run_pipeline       # bronce -> plata -> oro, linaje y mapa
pytest tests --cov=pipeline            # pruebas offline; incluye OSM simulado
streamlit run tablero/app.py          # tablero
```

No ejecutar `python -m extractors.osm_overpass` hasta confirmar la política
vigente del servidor elegido y que el volumen de consultas esté permitido. La
integración OSM aún no tiene captura real.
