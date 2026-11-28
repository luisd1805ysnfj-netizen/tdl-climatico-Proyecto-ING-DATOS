# Entrega E3 · Observatorio Climático y Agrícola

**Estado:** implementación técnica existente; el tag Git `e3` existe en el repositorio y debe corresponder al contenido aprobado final.

## Resumen ejecutivo

Se optimizó el paso de consolidación de fuentes del pipeline, se midió el cambio
contra el código previo sobre los mismos 39 archivos de bronce y se generó un
dataset curado en CSV y Parquet con 3,294 filas, 29 columnas y linaje por
variable. El benchmark verifica que las capas Plata y Oro antes/después sean
idénticas mediante hashes SHA-256.

## Comparación cuantitativa

Resultados de tres repeticiones intercaladas por variante; los tiempos y la
memoria son medianas. Datos completos y huellas: [`benchmark.json`](benchmark.json).

| Métrica | Antes | Después | Cambio |
|---|---:|---:|---:|
| Tiempo total del replay | 7.041 s | 4.378 s | **−37.81%** |
| Pico de asignaciones Python (`tracemalloc`) | 12.36 MiB | 12.32 MiB | −0.34% |
| Filas de bronce leídas | 3,495 | 3,495 | 0 |
| Capturas duplicadas enviadas a cuarentena | 201 | 201 | 0 |
| Rechazos por esquema/calidad | 0 | 0 | 0 |
| Reducción de errores de calidad | — | — | No observada: ambas variantes tuvieron 0 rechazos |
| Valores climáticos críticos faltantes antes/después de imputar | 0 / 0 | 0 / 0 | 0 |
| Imputaciones climáticas | 0 | 0 | 0 |
| Filas de oro diario / mensual | 3,294 / 111 | 3,294 / 111 | 0 |
| Valores revisados por linaje / fallos | 13,176 / 0 | 13,176 / 0 | 0 |
| Hashes de Plata, Oro diario y Oro mensual | iguales | iguales | paridad confirmada |

Las 201 filas son duplicados de capturas históricas que se preservan en
cuarentena; no son rechazos por esquema. La bitácora de captura, medida aparte
del replay offline, registra 42 éxitos y 3 respuestas HTTP 429 en 45 intentos
(93.3 % de éxito), y 0 timeouts. El objetivo PSP de disponibilidad ≥95 % no se
alcanza en esta muestra. No se ejecutaron peticiones HTTP durante el benchmark.

`tracemalloc` contabiliza asignaciones de memoria Python; no equivale al uso
total de RAM del proceso ni mide directamente todas las asignaciones nativas de
NumPy, SciPy o scikit-learn. Por eso el resultado se reporta como MiB de pico
trazado y no se afirma una reducción material de memoria.

## Cambios técnicos y artefactos

- La agregación de diferencias por variable ahora calcula `min`, `max` y
  `count` en operaciones nativas de `groupby`, en lugar de invocar una función
  Python por variable y grupo. La diferencia se deja nula si hay menos de dos
  valores, preservando la semántica anterior.
- Se conservaron la cuarentena, validación de calidad y verificación estricta de
  linaje. El extractor ya contaba con reintentos exponenciales, timeout,
  validación de unidades y escritura atómica; no se duplicó esa lógica.
- Benchmark reproducible: [`scripts/benchmark_e3.py`](../../scripts/benchmark_e3.py).
- Curación y validación: [`scripts/curate_e3.py`](../../scripts/curate_e3.py).
- Dataset CSV: [`data/curated/observatorio_climatico_agricola_curado.csv`](../../data/curated/observatorio_climatico_agricola_curado.csv).
- Dataset Parquet: [`data/curated/observatorio_climatico_agricola_curado.parquet`](../../data/curated/observatorio_climatico_agricola_curado.parquet).
- Licencia: [`data/curated/LICENSE-DATA.md`](../../data/curated/LICENSE-DATA.md).
- CC BY 4.0 cubre las aportaciones del proyecto; los datos de Open-Meteo siguen
  sujetos a los términos no comerciales de la API gratuita. La licencia del
  proyecto no amplía los derechos sobre la fuente.
- Ficha técnica: [`datasheet.md`](datasheet.md).
- Relatoría: [`docs/relatoria-E3.md`](../relatoria-E3.md).

## Reproducibilidad

Desde la raíz del repositorio, con dependencias de `requirements.txt`:

```powershell
python scripts\benchmark_e3.py --runs 3
python -m pipeline.run_pipeline
python scripts\curate_e3.py
pytest tests\test_pipeline.py tests\test_curate_e3.py -q
```

La medición reproducida el 27 de noviembre de 2026 usa por defecto como baseline el commit
`b96c6f878ec8b4ae2e460045b0fedcc8385277b4`, ejecuta ambas variantes en
directorios temporales aislados y guarda las nuevas métricas en
`docs/E3/benchmark.json`. El replay es offline: necesita Git y los archivos
actuales de `data/bronce`, pero no una API disponible.

## Alcance y asuntos pendientes

Esta versión cubre clima de tres municipios de Colima y una sola fuente
meteorológica; no incluye capturas reales de OSM ni la capa de mercado. Los
valores extremos se conservan marcados.

El laboratorio actual incluye PCA con cinco variables, aproximación Mardia,
distancias Mahalanobis y MANOVA por municipio. Falta una prueba formal
Henze-Zirkler, replicación independiente y publicación final del Mapa de
componentes si se requiere un cierre más amplio.

El tag `e3` ya existe en el repositorio. No se movió ni se recreó durante
esta revisión.
