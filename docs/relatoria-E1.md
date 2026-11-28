# Relatoría E1 · Integración, limpieza y puerta de calidad

## Estado de evidencia

La parte de preparación de datos tiene implementación, artefactos y pruebas
reproducibles. La serie cubre Colima, Manzanillo y Tecomán, con datos de
Open-Meteo Archive del 2023-11-23 al 2026-11-24. El análisis estadístico de
pronóstico de seis meses planteado en E0 no está implementado ni documentado en
esta entrega; no se reportan modelos ni métricas de pronóstico.

El equipo indicado en E0 es Luis Alfredo Ruiz Fuentes y Ariadna Andrea Muñoz
Andrade. Los registros de tiempo no permiten asignar cada actividad ni sus
horas a una persona. La bitácora registra dos actividades por un total de 75
minutos el 2026-11-09, sin desglosar el trabajo técnico.

## 1. Qué se implementó

- Flujo reproducible Bronce → Plata → Oro mediante `python -m
  pipeline.run_pipeline`.
- Diagnóstico de faltantes MCAR/MAR/MNAR, evaluación de imputación por
  enmascarado y métodos de tratamiento; las pruebas sintéticas no se presentan
  como faltantes reales.
- Detección de anomalías mediante z-score robusto, IQR y Isolation Forest. Se
  marcan y conservan; el dataset curado registra 197 filas marcadas.
- Escalado Min-Max y Z-score, discretización, jerarquías y reducción diaria a
  mensual.
- Puerta Pandera y cuarentena con motivo. Los duplicados se conservan en
  cuarentena, no se confunden con rechazos de esquema.
- Linaje verificable: 13,176 valores, 13,176 rastreables y 0 fallos en la
  ejecución reportada.

## 2. Integración y limitaciones

Open-Meteo Archive es la única fuente meteorológica presente en los datos de
Bronce. El adaptador de SMN/CONAGUA y la resolución de conflictos se probaron
con datos sintéticos; no hay captura SMN real. Por tanto, la regla de prioridad
entre fuentes no se valida contra observaciones de dos proveedores.

La última ejecución E3 leyó 3,495 filas; 3,294 quedaron en Plata y 201
duplicados se enviaron a cuarentena. No hubo rechazos de calidad por esquema ni
imputaciones climáticas en el dataset curado.

## 3. Defectos y correcciones reportados

La bitácora `calidad/defectos-luis.csv` contiene un defecto de sintaxis de cinco
minutos. Un borrador previo de esta relatoría describe tres ajustes adicionales
(detección de lluvia extrema, selección de método de imputación y prueba de
conversión de unidades), pero no los registra en la bitácora con fecha,
responsable o tiempo; se conservan como antecedentes no corroborados, no como
métricas PSP.

La puerta se probó con siete filas dañadas a propósito y las pruebas verifican
que se cuarenten con motivos. Resultado local de la suite raíz: 74 aprobadas,
3 omitidas y 86.75 % de cobertura. La disponibilidad de captura en la bitácora
es 42/45 (93.3 %), inferior al objetivo PSP de 95 %. No hay evidencia suficiente
para calcular MTBF o MTTR.

## 4. Análisis estadístico ejecutable

El proyecto incluye [`laboratorio/e1_series.py`](../laboratorio/e1_series.py):
descomposición aditiva, ADF, diferenciación, ACF/PACF, correlación cruzada,
Simple, Holt, Holt-Winters y ARIMA sobre 37 meses reales por municipio. Exporta
MAE, RMSE, MAPE, Ljung-Box y intervalos aproximados de seis meses. Estas
métricas no sustituyen validación con estaciones locales.

## 5. Evidencias

- Notebook de limpieza: [`docs/E1/limpieza.ipynb`](E1/limpieza.ipynb).
- Pipeline: [`pipeline/`](../pipeline/).
- Pruebas: [`tests/`](../tests/); ejecución local actual: 74 aprobadas y 3
  omitidas.
- Reporte de calidad: [`data/plata/reporte_puerta_calidad.json`](../data/plata/reporte_puerta_calidad.json).
- Reporte de linaje: [`data/oro/reporte_linaje.json`](../data/oro/reporte_linaje.json).
- Plan SQA: [`docs/plan-SQA.md`](plan-SQA.md).
- Tiempo y defectos: [`calidad/tiempo-luis.csv`](../calidad/tiempo-luis.csv) y
  [`calidad/defectos-luis.csv`](../calidad/defectos-luis.csv).

## 6. Uso de herramientas generativas

La versión anterior de este documento atribuye el borrador del pipeline y del
notebook a Claude. El repositorio no contiene un registro que permita verificar
esa atribución ni los cambios individuales; el equipo debe confirmar o corregir
esa declaración antes de presentar la entrega. La existencia de código y
pruebas no sustituye la revisión y comprensión por parte del equipo.
