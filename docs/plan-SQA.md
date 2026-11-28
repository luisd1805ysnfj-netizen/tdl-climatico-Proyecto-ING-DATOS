# Plan SQA · Observatorio Climático y Agrícola

## Alcance y responsables

Este plan cubre la captura meteorológica, la transformación Bronce → Plata →
Oro, la curación E3 y la aplicación web. Los responsables operativos son los
roles del equipo (captura, revisión de datos y publicación); la bitácora del
repositorio no permite asignar cada actividad ni sus horas a una persona.

## Objetivos medibles y controles

| Objetivo | Umbral | Medición y control | Evidencia actual |
|---|---:|---|---|
| Integridad del linaje | 100 % de valores climáticos trazables o con origen imputado declarado | Verificación automática en el pipeline; falla ante una referencia rota | 13,176/13,176 valores, 0 fallos |
| Contabilización de datos | 100 % de filas de entrada explicadas como aceptadas o en cuarentena | Reportes de calidad y cuarentena por ejecución | En la ejecución E3: 3,495 leídas; 3,294 aceptadas y 201 duplicados en cuarentena |
| Disponibilidad de captura | ≥95 % de intentos por periodo de reporte | Calcular éxitos/intentos desde `calidad/bitacora_captura.csv`; investigar 429 y reintentar conforme a la política del proveedor | 42/45 = 93.3 % en la bitácora revisada; objetivo no alcanzado |
| Cobertura de pruebas | ≥60 % | Medición pytest sobre `pipeline/` | 86.75 % en la ejecución local actual |
| MTBF aproximado | Registrar y justificar | Intervalos entre intentos fallidos desde la bitácora | 22.70 h aproximadas; no equivale a SLA continuo |
| MTTR aproximado | Registrar y justificar | Duración media de registros fallidos | 6.40 s aproximados; no equivale a restauración de servicio |
| Ventana de disponibilidad | ≥95 % durante 14 días | Evaluación continua mediante Actions | Pendiente: la bitácora cubre aproximadamente 14 días, pero no demuestra uptime continuo |
| Tiempo de reprocesamiento local | <180 s por ejecución | Medir el pipeline offline con entradas idénticas | Benchmark E3: mediana optimizada de 4.378 s; no equivale a latencia de captura ni a un SLA |
| Secretos publicados | 0 hallazgos | Gitleaks en CI y revisión antes de publicar | Gitleaks está configurado en `.github/workflows/ci.yml`; su ejecución local no sustituye el resultado de CI |

## Flujo de verificación

1. Ejecutar `ruff check pipeline tests scripts`.
2. Ejecutar `pytest --cov=pipeline --cov-report=term-missing --cov-fail-under=60`.
3. Ejecutar `python -m pipeline.run_pipeline` y revisar los reportes de puerta,
   cuarentena y linaje.
4. Para E3, ejecutar el benchmark offline y la validación del dataset.
5. Revisar los fallos de captura por separado; no contabilizar el replay local
   como disponibilidad de una API.
6. Antes de publicar, revisar fuentes, licencias, atribuciones y secretos.

## Defectos, incidentes y límites

Registrar cada defecto con fecha, tipo, descripción, tiempo de corrección y
evidencia en `calidad/defectos-luis.csv`. La bitácora existente solo contiene
un defecto (5 minutos); no hay base suficiente para calcular MTBF o MTTR.
Los objetivos incumplidos y los fallos HTTP deben conservarse en los reportes,
no reinterpretarse como éxito.

Los valores de tiempo de calidad actualmente registrados suman 75 minutos en
dos actividades de 2026-11-09. No representan el tiempo total de desarrollo ni
permiten distribuir horas entre las actividades técnicas.
