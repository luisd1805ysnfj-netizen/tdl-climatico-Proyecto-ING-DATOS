# Entrega E1 · Observatorio de Inteligencia Climática y Gestión de Riesgos Agrícolas (Colima, Tecomán y Manzanillo)

Equipo registrado en E0: Luis Alfredo Ruiz Fuentes y Ariadna Andrea Muñoz Andrade · Etiqueta: `e1` (pendiente) · Tablero: no hay URL pública registrada.

> Estado: la capa de Ingeniería de Datos está implementada y reproducible. El análisis estadístico de pronóstico que aparece en la rúbrica anterior no está evidenciado; por ello esta entrega no se declara completa en esa dimensión.

## Resumen en tres líneas
1. Un solo comando (`python -m pipeline.run_pipeline`, y el mismo flujo en el CI) lleva los datos de **bronce → plata → oro**: 3,294 registros diarios de 3 municipios (23-nov-2023 a 24-nov-2026).
2. La **puerta de calidad** (pandera) valida esquema, tipos, rangos físicos, regla `tmax ≥ tmin`, coordenadas y unicidad; lo inválido va a `data/cuarentena/` con motivo. Sobre los datos reales rechazó 0 registros; se probó con 7 registros dañados a propósito (todos a cuarentena, ninguno perdido).
3. La limpieza está **justificada con evidencia**, no por costumbre: experimento de enmascarado para elegir la imputación, 197 filas marcadas como atípicas (no borradas) y reducción 96.6 % (3,294 filas diarias → 111 mensuales).

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Valores faltantes (15) | [`limpieza.ipynb` §4](limpieza.ipynb) · [`pipeline/limpieza.py`](../../pipeline/limpieza.py) (`diagnosticar_faltantes`, `evaluar_imputacion`, `imputar`) | Los datos reales no traen faltantes; el diagnóstico MCAR/MAR queda implementado y probado con un caso MAR sintético. La imputación se justificó con un experimento de enmascarado (10 %, huecos de 1 y 5 días). |
| Atípicos y ruido (15) | [`limpieza.ipynb` §5](limpieza.ipynb) · `marcar_atipicos`, `suavizar_ruido` | z robusto sobre anomalía + IQR (k=3) en lluvia + Isolation Forest. Decisión: marcar y conservar; 197 de 3,294 días (6.0 %) con alguna marca. |
| Normalización, discretización y reducción (15) | [`limpieza.ipynb` §6, §7 y §8](limpieza.ipynb) · `aplicar_escalado`, `discretizar`, `agregar_jerarquias`, `reducir_mensual` | Min-max y z-score con parámetros guardados en `data/oro/params_escalado.json`. Reducción por agregación (96.6 %) y selección de variables (ninguna redundante). |
| Integración de fuentes (20) | [`pipeline/integracion.py`](../../pipeline/integracion.py) · [`limpieza.ipynb` §1-2](limpieza.ipynb) · [`tests/test_pipeline.py`](../../tests/test_pipeline.py) | No hay segunda fuente real: SMN/CONAGUA no está capturado en Bronce. El adaptador y la consolidación por prioridad están probados con datos sintéticos; no se atribuyen discrepancias a fuentes reales. |
| Puerta de calidad (25) | [`pipeline/puerta_calidad.py`](../../pipeline/puerta_calidad.py) · [`data/plata/reporte_puerta_calidad.json`](../../data/plata/reporte_puerta_calidad.json) · [`limpieza.ipynb` §3](limpieza.ipynb) · `data/cuarentena/` | Los registros rechazados conservan `motivo_rechazo` y la regla violada. Los duplicados de captura también se registran, no se descartan en silencio. |

Capas pobladas automáticamente: [`data/plata/`](../../data/plata) y [`data/oro/`](../../data/oro). Diccionario de datos: [`diccionario_datos.md`](diccionario_datos.md) y `data/oro/diccionario_datos.csv`.

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Caracterización y descomposición (15) | No evidenciado en esta entrega | El notebook de limpieza describe preprocesamiento; no se reporta una descomposición temporal ejecutada. |
| Estacionariedad y autocorrelación (15) | No evidenciado en esta entrega | No se encontró una prueba reproducible ni resultados guardados. |
| Cuatro modelos (25) | No evidenciado en esta entrega | No se encontraron cuatro modelos de pronóstico ajustados. |
| Selección por error (20) | No evidenciado en esta entrega | No hay partición temporal ni métricas comparativas de pronóstico. |
| Residuos y comunicación (15) | No evidenciado en esta entrega | No se encontraron diagnósticos de residuos ni reporte de pronóstico. |

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Fiabilidad y disponibilidad (25) | [`calidad/bitacora_captura.csv`](../../calidad/bitacora_captura.csv) · [`docs/plan-SQA.md`](../plan-SQA.md) | 42/45 éxitos (93.3 %); no cumple la meta ≥95 %. No hay evidencia suficiente para calcular MTBF/MTTR. |
| Seguridad (15) | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) | Gitleaks está configurado. No se encontró evidencia de `pip-audit` ni de una política de respaldo automatizado. |
| Requerimientos (10) | [`docs/E0/propuesta.md`](../E0/propuesta.md) | Pregunta detonadora y requisitos de captura están documentados; falta evidencia de aceptación del cliente. |
| Plan SQA (25) | [`docs/plan-SQA.md`](../plan-SQA.md) | Objetivos, controles y resultados actuales; incluye umbrales incumplidos sin presentarlos como éxitos. |
| Integración continua (15) | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) | Linter, pruebas con cobertura mínima de 60 %, pipeline sobre Bronce y Gitleaks. |

## Relatoría de etapa
Enlace a [`docs/relatoria-E1.md`](../relatoria-E1.md)

## Issues de la entrega anterior
Observaciones del maestro en E0 y cómo se atendieron:

| Observación | Cómo se atendió | Evidencia | Commit que cierra |
|---|---|---|---|
| Configurar el workflow de GitHub Actions para programar la ingesta diaria | Workflow con `schedule` diario (08:00 hora de Colima) y botón manual; captura con reintentos, guarda en `data/bronce/`, refresca plata/oro y registra cada intento en la bitácora | [`.github/workflows/captura.yml`](../../.github/workflows/captura.yml) · [`extractors/captura_diaria.py`](../../extractors/captura_diaria.py) · [`calidad/bitacora_captura.csv`](../../calidad/bitacora_captura.csv) | Implementación presente; no hay enlace de una corrida verde de Actions en este documento. |
| Formalizar `tests/` con pruebas unitarias offline que validen las respuestas de Open-Meteo | Suite raíz con fixtures y pruebas offline para respuestas válidas, 429, 500, timeout, JSON inválido y unidades | [`tests/test_open_meteo_offline.py`](../../tests/test_open_meteo_offline.py) · [`tests/conftest.py`](../../tests/conftest.py) · [`tests/fixtures/`](../../tests/fixtures) | Verificación local actual: 74 aprobadas, 4 omitidas, 83.53 % de cobertura. |

No se consultó el tracker de issues del proyecto; no se afirma que no existan otros issues docentes.

## Cómo reproducir
```bash
pip install -r requirements.txt
python -m pipeline.run_pipeline      # bronce -> plata -> oro
pytest tests --cov=pipeline --cov-report=term-missing --cov-fail-under=60
```
