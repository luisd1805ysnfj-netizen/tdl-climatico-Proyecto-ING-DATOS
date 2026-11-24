# Entrega E2 · Observatorio de Inteligencia Climática y Gestión de Riesgos Agrícolas (Colima, Tecomán y Manzanillo)

Equipo: [COMPLETAR: integrante 1] · [COMPLETAR: integrante 2] · Etiqueta: `e2` · Tablero: [COMPLETAR: URL pública de Streamlit]

> Los enlaces son relativos al repositorio y funcionan en GitHub dentro de la etiqueta `e2`.

## Resumen en tres líneas
1. **Fuente especializada geoespacial:** uso de suelo agrícola de OpenStreetMap (Overpass), consultado alrededor de las coordenadas reales de la malla de Open-Meteo, con unión espacial en GeoPandas, área en hectáreas y mapa en el tablero.
2. **Ética y legalidad:** `docs/etica-datos.md` con términos, licencias, `robots.txt`, privacidad (lista blanca de etiquetas: cero datos personales en bronce) y sesgos por fuente.
3. **Linaje:** cada valor de la capa oro apunta a su archivo de bronce, su huella SHA-256, su posición y su fecha de ingesta; una prueba automática abre los archivos y lo comprueba (con los datos de E1: [COMPLETAR tras correr el pipeline] valores revisados, 0 fallos).

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Fuente especializada (45) | [`extractors/osm_overpass.py`](../../extractors/osm_overpass.py) · [`pipeline/geoespacial.py`](../../pipeline/geoespacial.py) · [`pipeline/mapa.py`](../../pipeline/mapa.py) · [`tablero/app.py`](../../tablero/app.py) · [`tests/test_osm_offline.py`](../../tests/test_osm_offline.py) · bitácora [`calidad/bitacora_osm.csv`](../../calidad/bitacora_osm.csv) · salida [`data/oro/oro_contexto_agricola.csv`](../../data/oro/oro_contexto_agricola.csv) | Integrada al pipeline (`python -m pipeline.run_pipeline`): bronce `osm_agricola_*.json` → puerta de calidad geoespacial con cuarentena → unión espacial → oro. Sin datos personales: la lista blanca de etiquetas actúa **antes** de guardar en bronce. [COMPLETAR: cifras reales, p. ej. "Tecomán: X ha, Y % del círculo"] |
| Declaración de ética y legalidad (30) | [`docs/etica-datos.md`](../etica-datos.md) | Base legal, licencias (CC BY 4.0 y ODbL), análisis de `robots.txt`, riesgos de privacidad y sesgos por fuente, cada uno con su mitigación y su evidencia en el código. |
| Linaje de datos (15) | [`pipeline/oro.py`](../../pipeline/oro.py) (`agregar_linaje`, `verificar_linaje`) · [`tests/test_linaje.py`](../../tests/test_linaje.py) · [`data/oro/reporte_linaje.json`](../../data/oro/reporte_linaje.json) · [`diccionario_datos.md`](../E1/diccionario_datos.md) | `origen_<variable>` = `archivo\|huella12\|fila` o `IMPUTADO:<método>`; `id_registro` estable; `fecha_captura` = fecha de ingesta; el oro mensual declara `primer_dia`, `ultimo_dia` y `ultima_ingesta`. La verificación **falla el pipeline** si algo no se puede rastrear. |

### Cómo se rastrea un valor (ejemplo para la defensa)
1. En `data/oro/clima_oro_diario.csv`, tomar una fila y leer `origen_tmax_c`, p. ej. `clima_historico_colima_20261109.json|2444c990bd3a|0`.
2. Abrir ese archivo en `data/bronce/`: su SHA-256 empieza con `2444c990bd3a`.
3. En `daily.time[0]` está la fecha y en `daily.temperature_2m_max[0]` el valor: son los mismos de la fila de oro.
4. Si el valor fue imputado, `origen_tmax_c` dice `IMPUTADO:<método>` y `tmax_c_imputado` es `True`: está declarado, no escondido.

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Diseño y principios (factorial 2³) | [COMPLETAR] | |
| Dos factores con interacción | [COMPLETAR] | |
| Completo vs. fraccionado | [COMPLETAR] | |
| Análisis y confirmación | [COMPLETAR] | |

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Evaluación ISO/IEC 25010 | [COMPLETAR] | La ruta ingeniería puede usar el experimento como evidencia de eficiencia de desempeño |
| Evaluación ISO/IEC 25012 | [COMPLETAR] | Medida sobre la capa oro |
| Antecedentes normativos | [COMPLETAR] | |
| Auditoría cruzada | [COMPLETAR] | Del 19 al 23 de noviembre |

## Relatoría de etapa
Enlace a [`docs/relatoria-E2.md`](../relatoria-E2.md)

## Issues de la entrega anterior
[COMPLETAR: issues de E1 atendidos, con el commit que cierra cada uno]

## Cómo reproducir
```bash
pip install -r requirements.txt
python -m extractors.osm_overpass     # captura OSM (3 consultas; manual o mensual)
python -m pipeline.run_pipeline       # bronce -> plata -> oro, linaje y mapa
pytest --cov=pipeline                 # pruebas
streamlit run tablero/app.py          # tablero
```
