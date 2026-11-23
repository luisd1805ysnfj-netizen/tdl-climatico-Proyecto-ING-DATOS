# Entrega E1 · Observatorio de Inteligencia Climática y Gestión de Riesgos Agrícolas (Colima, Tecomán y Manzanillo)

Equipo: [COMPLETAR: integrante 1] · [COMPLETAR: integrante 2] · Etiqueta: `e1` · Tablero: [COMPLETAR: URL pública]

> Los enlaces son relativos al repositorio y funcionan en GitHub dentro de la etiqueta `e1`.

## Resumen en tres líneas
1. Un solo comando (`python -m pipeline.run_pipeline`, y el mismo flujo en el CI) lleva los datos de **bronce → plata → oro** sin intervención manual: 3,243 registros diarios de 3 municipios (23-nov-2023 a 7-nov-2026).
2. La **puerta de calidad** (pandera) valida esquema, tipos, rangos físicos, regla `tmax ≥ tmin`, coordenadas y unicidad; lo inválido va a `data/cuarentena/` con motivo. Sobre los datos reales rechazó 0 registros; se probó con 7 registros dañados a propósito (todos a cuarentena, ninguno perdido).
3. La limpieza está **justificada con evidencia**, no por costumbre: experimento de enmascarado para elegir la imputación, atípicos marcados (no borrados) con tres métodos, y reducción 96.6 % (3,243 filas diarias → 111 mensuales).

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Valores faltantes (15) | [`limpieza.ipynb` §4](limpieza.ipynb) · [`pipeline/limpieza.py`](../../pipeline/limpieza.py) (`diagnosticar_faltantes`, `evaluar_imputacion`, `imputar`) | Los datos reales no traen faltantes; el diagnóstico MCAR/MAR queda implementado y probado con un caso MAR sintético. La imputación se justificó con un experimento de enmascarado (10 %, huecos de 1 y 5 días). |
| Atípicos y ruido (15) | [`limpieza.ipynb` §5](limpieza.ipynb) · `marcar_atipicos`, `suavizar_ruido` | z robusto sobre anomalía + IQR (k=3) en lluvia + Isolation Forest. Decisión: marcar y conservar; 196 de 3,243 días (6.0 %) con alguna marca. |
| Normalización, discretización y reducción (15) | [`limpieza.ipynb` §6, §7 y §8](limpieza.ipynb) · `aplicar_escalado`, `discretizar`, `agregar_jerarquias`, `reducir_mensual` | Min-max y z-score con parámetros guardados en `data/oro/params_escalado.json`. Reducción por agregación (96.6 %) y selección de variables (ninguna redundante). |
| Integración de fuentes (20) | [`pipeline/integracion.py`](../../pipeline/integracion.py) · [`limpieza.ipynb` §1-2](limpieza.ipynb) · [`tests/test_pipeline.py`](../../tests/test_pipeline.py) | [COMPLETAR: estado de la segunda fuente (SMN/CONAGUA)]. El adaptador y la consolidación por prioridad están probados con una fuente sintética. |
| Puerta de calidad (25) | [`pipeline/puerta_calidad.py`](../../pipeline/puerta_calidad.py) · [`data/plata/reporte_puerta_calidad.json`](../../data/plata/reporte_puerta_calidad.json) · [`limpieza.ipynb` §3](limpieza.ipynb) · `data/cuarentena/` | Los registros rechazados conservan `motivo_rechazo` y la regla violada. Los duplicados de captura también se registran, no se descartan en silencio. |

Capas pobladas automáticamente: [`data/plata/`](../../data/plata) y [`data/oro/`](../../data/oro). Diccionario de datos: [`diccionario_datos.md`](diccionario_datos.md) y `data/oro/diccionario_datos.csv`.

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Caracterización y descomposición (15) | [COMPLETAR] | |
| Estacionariedad y autocorrelación (15) | [COMPLETAR] | |
| Cuatro modelos (25) | [COMPLETAR] | |
| Selección por error (20) | [COMPLETAR] | |
| Residuos y comunicación (15) | [COMPLETAR] | |

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Fiabilidad y disponibilidad (25) | [COMPLETAR: MTBF, MTTR y disponibilidad con la bitácora de captura] | |
| Seguridad (15) | [COMPLETAR: gitleaks, pip-audit, respaldo] | El workflow ya ejecuta gitleaks en cada push. |
| Requerimientos (10) | [COMPLETAR] | |
| Plan SQA (25) | [COMPLETAR: `docs/plan-SQA.md`] | La puerta de calidad de datos es un control del plan. |
| Integración continua (15) | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) | Linter, pruebas con cobertura mínima de 60 %, pipeline sobre bronce y gitleaks. |

## Relatoría de etapa
Enlace a [`docs/relatoria-E1.md`](../relatoria-E1.md)

## Issues de la entrega anterior
Observaciones del maestro en E0 y cómo se atendieron:

| Observación | Cómo se atendió | Evidencia | Commit que cierra |
|---|---|---|---|
| Configurar el workflow de GitHub Actions para programar la ingesta diaria | Workflow con `schedule` diario (08:00 hora de Colima) y botón manual; captura con reintentos, guarda en `data/bronce/`, refresca plata/oro y registra cada intento en la bitácora | [`.github/workflows/captura.yml`](../../.github/workflows/captura.yml) · [`extractors/captura_diaria.py`](../../extractors/captura_diaria.py) · [`calidad/bitacora_captura.csv`](../../calidad/bitacora_captura.csv) | [COMPLETAR] |
| Formalizar `tests/` con pruebas unitarias offline que validen las respuestas de Open-Meteo | 17 pruebas que usan una respuesta real guardada como fixture y una sesión falsa (éxito, 429, 500, timeout, JSON roto, unidades incorrectas); un bloqueo de red automático hace fallar cualquier prueba que intente conectarse | [`tests/test_open_meteo_offline.py`](../../tests/test_open_meteo_offline.py) · [`tests/conftest.py`](../../tests/conftest.py) · [`tests/fixtures/`](../../tests/fixtures) | [COMPLETAR] |

Cualquier otro issue abierto por los docentes: [COMPLETAR]

## Cómo reproducir
```bash
pip install -r requirements.txt
python -m pipeline.run_pipeline      # bronce -> plata -> oro
pytest --cov=pipeline                # pruebas
```
