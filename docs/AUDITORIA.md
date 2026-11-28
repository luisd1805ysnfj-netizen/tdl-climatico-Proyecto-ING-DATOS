# Diagnóstico de auditoría integral

**Proyecto:** Observatorio de Inteligencia Climática y Gestión de Riesgos Agrícolas
**Región:** Colima, Tecomán y Manzanillo
**Fecha de revisión:** 27 de noviembre de 2026
**Alcance:** calidad, documentación E0-E4, datos, extractores, pipeline, laboratorio y React

> Esta auditoría no modifica código ni datos. Separa evidencia respaldada por archivos reales de afirmaciones pendientes, sintéticas o desactualizadas.

## Estado posterior a la corrección

- Se añadieron registros PSP individuales y cálculo automático de disponibilidad/MTBF/MTTR.
- Se ejecutaron análisis E1, E2 exploratorio y E3 en `laboratorio/`.
- Los resultados se exportaron a `frontend/public/data/`.
- React muestra tarjetas de pronóstico, factorial, PCA/MANOVA y calidad.
- Las cifras reales actuales son 74 pruebas aprobadas, 3 omitidas y 86.75 % de cobertura.
- Los pendientes que requieren terceros siguen siendo fuente oficial adicional, OSM real, consentimiento de entrevista, experimento aleatorizado controlado y validación móvil/agrónomica.

---

## Resumen ejecutivo

El repositorio tiene una base sólida de ingeniería de datos:

- Arquitectura Bronce → Plata → Oro.
- 3,495 registros leídos de Bronce.
- 3,294 registros diarios aceptados.
- 111 registros mensuales.
- 201 duplicados enviados a cuarentena.
- Linaje verificable con 13,176 valores revisados y cero fallos.
- Dataset curado de 3,294 filas × 29 columnas.
- Benchmark reproducible antes/después.
- Interfaz React principal.
- 74 pruebas aprobadas y 3 omitidas.
- Cobertura real de pipeline del 86.75 %.

Las brechas principales son:

- Falta completar E1 estadístico con pronóstico y intervalos.
- Falta ejecutar el experimento factorial y ANOVA de dos vías de E2.
- Falta PCA completo con Mardia/Henze-Zirkler, Mahalanobis y MANOVA en E3.
- Falta Sello TDL, auditoría cruzada, MoProSoft, CMMI y datos individuales PSP completos.
- Falta completar E4 con entrega final, PDF, demo y modelo de negocio real.
- La única fuente meteorológica persistida es Open-Meteo.
- No hay captura real persistida de OSM, SMN/CONAGUA u otra fuente oficial.
- Las bitácoras PSP son insuficientes para asignar horas, defectos y responsables.

---

# 1. Auditoría de `calidad/`

## `calidad/bitacora_captura.csv`

**Estado:** parcial.

Cumple:

- Registra ejecuciones de los tres municipios.
- Contiene timestamp UTC, municipio, éxito, HTTP, filas, intentos, duración y error.
- Contiene tres fallos HTTP 429.
- Permite calcular una disponibilidad observada de 42 éxitos sobre 45 intentos.

Falta:

- 14 días o más continuos posteriores a la última captura si se busca demostrar el sello.
- Relación con commit, ejecución de GitHub Actions y fecha de observación.
- Códigos separados por reintento y no solamente por municipio.
- Evidencia de respaldo o recuperación.
- MTBF y MTTR calculados con incidentes definidos.

## `calidad/tiempo-luis.csv`

**Estado:** muy incompleto.

Cumple:

- Contiene dos actividades E0 con 75 minutos totales.

Falta:

- Actividades individuales de E1 a E4.
- Archivo separado para Ariadna.
- Fechas, fase, actividad, responsable y resultado.
- Horas por fase de desarrollo, prueba, revisión y corrección.
- Tiempo útil para retrospección PSP.

## `calidad/defectos-luis.csv`

**Estado:** muy incompleto.

Cumple:

- Contiene un defecto de sintaxis y cinco minutos de reparación.

Falta:

- Los diez tipos PSP completos.
- Registro para Ariadna.
- Fecha y responsable de cada defecto.
- Fase de inyección y fase de descubrimiento.
- Tipo, severidad, descripción y evidencia.
- Tiempos de corrección repetibles.
- Relación con commits o pruebas.

## Objetivos PSP faltantes

- Disponibilidad real y sostenida.
- Completitud de Oro.
- Cobertura de pruebas.
- Cero secretos.
- Cero hallazgos críticos.
- Tiempo medio de resolución.
- MTBF.
- MTTR.
- Reproducibilidad.

---

# 2. Auditoría por entrega

## E0

### `docs/E0/ENTREGA.md`

Estado: parcial.

Cumple:

- Identifica equipo y etiqueta.
- Resume sector, región y pregunta.
- Presenta los grupos de Ingeniería de Datos, Estadística y Calidad.
- Reconoce que la entrevista y la disponibilidad requieren evidencia adicional.

Falta:

- Confirmar una serie histórica real de 36 periodos.
- Incorporar una captura o referencia oficial adicional.
- Adjuntar evidencia verificable de objetivos PSP.
- Adjuntar constancia de entrevista y aceptación del cliente.

### `docs/E0/propuesta.md`

Estado: suficiente como borrador, pero no cerrada.

Cumple:

- Ficha del observatorio.
- Región y sector.
- Cliente potencial.
- Pregunta central.
- Cinco preguntas de entrevista.
- Respuestas y aprendizajes.
- Tres preguntas analíticas.
- Plan de Open-Meteo, SMN/CONAGUA y OSM.
- Nota ética y de privacidad.

Falta:

- Consentimiento verificable.
- Fecha exacta y duración confirmada.
- Identificación anonimizada o anonimización formal.
- Constancia independiente de la entrevista.
- Captura real SMN/CONAGUA.
- Cálculo real de costo operativo.
- Modelo de precio basado en datos reales.
- Evidencia de disposición efectiva de pago.

---

## E1

### `docs/E1/ENTREGA.md`

Estado: ingeniería de datos parcial; análisis estadístico incompleto.

Cumple:

- Documenta la arquitectura Bronce → Plata → Oro.
- Reporta 3,294 registros de Plata y Oro diario.
- Reporta 111 meses agregados.
- Explica duplicados y cuarentena.
- Reconoce que el pronóstico no está implementado.

Falta:

- Pronóstico con los cuatro modelos requeridos.
- Descomposición.
- ADF y diferenciación.
- ACF/PACF.
- Correlación cruzada.
- Métricas comparables.
- Residuos y Ljung-Box.
- Intervalos de confianza.
- Resultados visibles en React.
- Integración real con segunda fuente.
- MTBF y MTTR reales.

### `docs/relatoria-E1.md`

Estado: parcial y honestamente consciente de sus pendientes.

Cumple:

- Las seis secciones están presentes.
- Distingue datos sintéticos de reales.
- Declara que el pronóstico está abierto.
- Reporta 93.3 % de disponibilidad como incumplimiento.

Falta:

- Completar la actualización histórica restante en documentos que todavía dependan de versiones anteriores.
- Mantener visible la medición real actual: 74 aprobadas, 3 omitidas y 86.75 % de cobertura.
- Vincular evidencias individuales.
- Completar responsables y horas.
- Añadir commit o ejecución CI verificable.

### `docs/E1/diccionario_datos.md`

Estado: útil, incompleto como metadato final.

Cumple:

- Describe variables originales y derivadas.
- Describe linaje y jerarquías.

Falta:

- Versión formal del diccionario.
- Clasificación de nivel de sensibilidad.
- Procedencia por columna.
- Reglas de actualización.
- Relación exacta con el dataset curado.

### `docs/E1/limpieza.ipynb`

Estado: parcial.

Cumple:

- Limpieza.
- Diagnóstico de faltantes.
- Ejemplos sintéticos.
- Atípicos.
- Normalización.
- Discretización.

Falta:

- Ejecución completa de serie temporal.
- Descomposición real.
- Cuatro modelos estadísticos.
- Métricas en conjunto de prueba.
- Intervalos de confianza.
- Residuales.

---

## E2

### `docs/E2/ENTREGA.md`

Estado: incompleto.

Cumple:

- Linaje completo.
- Código experimental OSM.
- Pruebas offline OSM.
- Declaración ética.

Falta:

- Experimento factorial ejecutado.
- ANOVA de dos vías e interacción.
- Diseño completo y fraccionado.
- Alias y ahorro de corridas.
- Supuestos de residuos.
- Confirmación del tratamiento óptimo.
- Auditoría ISO/25010/25012 completa.
- Captura real OSM persistida.
- ISO 9126, ISO 25000 y ISO 9001 comparadas.
- Acta de auditoría cruzada.

### `docs/relatoria-E2.md`

Estado: parcial.

Cumple:

- Seis secciones.
- Declara captura real OSM pendiente.
- Explica sesgos, linaje y límites.

Falta:

- Horas individuales reales.
- Diseño estadístico.
- Evidencia del ANOVA.
- URL pública real si existe despliegue.
- Vínculos Git verificables a commits finales.
- Cierre formal de defectos.

### `docs/etica-datos.md`

Estado: buen borrador técnico-ético.

Cumple:

- Licencias.
- Robots, Open-Meteo y OSM.
- Privacidad.
- Minimización.
- Sesgos.
- Secretos de servidor.

Falta:

- Revisión jurídica formal si se va a comercializar.
- Evidencia de confirmación vigente de Overpass.
- Fecha y resultado de una revisión legal real.
- Política formal de borrado y retención.
- Consentimiento para capturar coordenadas de parcelas privadas.

---

## E3

### `docs/E3/ENTREGA.md`

Estado: parcial en análisis multivariado y calidad, buena en optimización.

Cumple:

- Benchmark antes/después.
- 3 repeticiones.
- Hashes equivalentes.
- Dataset curado.
- Licencia.
- Optimización reproducible.

Falta:

- Normalidad multivariada.
- Mahalanobis.
- PCA completo.
- MANOVA.
- Wilks y Pillai.
- Comparación con ANOVAs separadas.
- MoProSoft y CMMI.
- Cierre de auditoría.
- Sello TDL.
- Evidencia 14 días.
- Medición RSS.

También es inconsistente afirmar que el tag `e3` está pendiente, pues el HEAD actual ya está etiquetado como `e3`.

### `docs/E3/datasheet.md`

Estado: bueno.

Cumple:

- Identifica dataset.
- Documenta composición.
- Documenta procedencia.
- Documenta limpieza.
- Declara usos y limitaciones.

Falta:

- Archivo no debe declarar que el tag e3 está pendiente si ya existe.
- Agregar fecha de generación y versión reproducible al nombre del recurso.
- Agregar hashes individuales CSV y Parquet.
- Agregar tamaño, conteo de columnas y esquema formal.
- Separar licencia climática de contenido derivado potencialmente OSM.

### `docs/E3/benchmark.json`

Estado: bueno y respaldado.

Cumple:

- Métricas antes y después.
- Baseline.
- Conteos.
- Hashes.
- Metodología offline.
- Rutas de salida.

Falta:

- RSS real.
- Variabilidad estadística y intervalos.
- Benchmark en varios equipos o runner.
- Resultados de CI.

---

## E4

### `docs/reporte-final.md`

Estado: esquema técnico.

Cumple:

- Resumen.
- Flujo completo.
- Tres hallazgos.
- Incertidumbres.
- Recomendación.

Falta:

- Evidencia final de E1-E3.
- Precio y costo.
- Márgenes.
- Plan operativo.
- Riesgos residuales.
- PDF final.

### `docs/relatoria-final.md`

Estado: parcial.

Cumple:

- Las seis secciones están representadas.
- Uso de IA generativa.

Falta:

- Horas individuales.
- Decisiones individuales.
- Commit final.
- Evidencia de demo.
- Cierre de pendientes.

### `docs/demo-day.md`

Estado: guion básico.

Cumple:

- Pitch de 7 minutos.
- Cinco minutos de preguntas.
- Secuencia de demo.
- Video de dos minutos.

Falta:

- Transcripción ensayada.
- Evidencia de ensayo.
- Métricas finales.
- Capturas o grabación de demo.

---

# 3. Métricas respaldadas

Las siguientes cifras sí están respaldadas por datos o reportes reales:

- 3,495 registros leídos de Bronce.
- 3,294 registros aceptados en Plata.
- 3,294 registros diarios de Oro.
- 111 filas mensuales.
- 201 filas duplicadas en cuarentena.
- 13,176 valores climáticos revisados por linaje.
- 13,176 valores trazables.
- 0 fallos de linaje.
- 197 filas marcadas como atípicas.
- 3,097 filas no marcadas.
- 45 intentos de captura.
- 42 éxitos.
- 3 fallos HTTP 429.
- 0 timeouts registrados.
- 93.33 % de disponibilidad capturada.
- 74 pruebas aprobadas.
- 3 pruebas omitidas.
- Cobertura real de 86.75 % sobre `pipeline/`.
- 39 archivos JSON de Bronce.
- 15 archivos CSV de cuarentena.
- 1,098 registros por municipio.
- Sin huecos de fechas por municipio en Oro diario.
- PCA real sobre cuatro variables con resultados guardados.
- ADF real sobre 37 meses por municipio.

---

# 4. Métricas desactualizadas o no respaldadas

## Conteos de pruebas

La ejecución real actual y consistente con el bloque posterior muestra:

- 74 aprobadas.
- 3 omitidas.
- Cobertura de 86.75 %.

Los documentos con cifras antiguas deben actualizarse.

## Estado del tag `e3`

El datasheet y la entrega E3 dicen que el tag está pendiente.

La auditoría verificó que:

- `e3` existe.
- `e1` existe.
- `e2` existe.
- `e0` existe.
- El HEAD actual está contenido en `e3`.

## Referencias Git

Se encontraron referencias citadas que no existen como etiquetas o revisiones disponibles:


Sí existen:

- `e2`.
- `b96c6f878ec8b4ae2e460045b0fedcc8385277b4`.

La relatoría debe evitar enlaces no verificables.

## PSP

No está respaldado:

- Tiempo por integrante.
- 10 tipos PSP completos.
- MTBF.
- MTTR.
- Disponibilidad sostenida de 14 días.
- Responsables por actividad.

La bitácora indica solo 75 minutos en dos actividades E0.

## Entrevista

La entrevista está registrada como texto declarado.

No está respaldada por:

- Audio.
- Firma.
- Fecha exacta.
- Consentimiento.
- Evidencia independiente.

No debe presentarse como una investigación de campo verificable hasta agregar esas evidencias.

---

# 5. Estado real de datos

## Bronce

Estado:

- 39 JSON reales de Open-Meteo.
- 13 archivos por municipio.
- Cuatro variables climatológicas.
- Fechas históricas de 2023-11-23 a 2026-11-24.

Brechas:

- No hay humedad relativa.
- No hay presión.
- No hay radiación.
- No hay datos oficiales adicionales.
- No hay datos reales de OSM.
- No hay observaciones agrícolas de campo.

## Plata

Estado:

- 3,294 registros.
- Sin nulos en las variables críticas.
- Sin rechazos físicos reales.

Brechas:

- Las columnas `dif_*` son nulas porque no existe segunda fuente.
- No hay evidencia de resolución real de conflictos entre fuentes.
- No representa integración multifuente completa.

## Oro

Estado:

- Diario completo por municipio y fecha.
- Mensual completo.
- 67 columnas en el CSV diario.
- 13,176 valores revisados por linaje.

Brechas:

- Sin variables geoespaciales persistidas reales.
- Sin análisis PCA publicado en React.
- Sin MANOVA.
- Sin pronóstico propio.

## Cuarentena

Estado:

- 15 archivos registrados.
- Principalmente duplicados de captura.

Brechas:

- Separar claramente tipos de rechazo.
- Agregar conteos por regla.
- Agregar motivo y fecha en todas las ejecuciones.

## Dataset curado

Estado:

- CSV presente.
- Parquet presente.
- Licencia presente.
- 29 columnas.
- Sin nulos publicados.

Brechas:

- Sin humedad ni variables adicionales.
- Sin datos geoespaciales reales.
- Sin hashes de distribución.
- Sin versión formal de datasheet.

---

# 6. Estado de análisis estadístico

## Implementado

- Caracterización mensual de precipitación.
- ADF por municipio.
- Shapiro-Wilk.
- PCA sobre cuatro variables.
- Varianza explicada y cargas.
- Exportación JSON parcial.

## No implementado

- Descomposición aditiva/multiplicativa.
- ACF/PACF.
- Correlación cruzada.
- Diferenciación.
- Simple/Naive.
- Holt.
- Holt-Winters.
- ARIMA/SARIMA.
- MAE, RMSE y MAPE comparables.
- Ljung-Box.
- Intervalos de confianza.
- Diseño experimental factorial.
- ANOVA de dos vías.
- Supuestos de residuos.
- Diseño completo/fraccionado.
- Mardia o Henze-Zirkler.
- Distancias de Mahalanobis.
- Q-Q multivariado.
- MANOVA Wilks/Pillai.
- Comparación con ANOVAs.
- Biplot.
- Mapa de componentes React.

---

# 7. Estado de React

Cumple:

- Interfaz React.
- Open-Meteo actual.
- Histórico.
- Pronóstico externo estacional.
- Mapa.
- Rutas.
- Fuentes y API.
- Filtros de fuentes.
- Avisos de datos orientativos.
- JSON del pipeline.
- Linaje expuesto en Fuentes y API.

Falta:

- Pronóstico estadístico propio.
- Intervalos de confianza.
- Comparación de modelos.
- Resultados factoriales.
- PCA y cargas.
- Mapa de componentes.
- MANOVA.
- Estados 25010/25012.
- MTBF/MTTR visuales.
- Indicador de última ejecución de CI.
- Indicador de completitud de Oro.
- Histórico real de PSP.

---

# 8. Plan de cierre

## Bloque E0

1. Registrar consentimiento y entrevista verificable.
2. Completar un modelo de negocio real.
3. Completar horas PSP individuales.
4. Agregar fuente oficial autorizada o mantenerla como pendiente explícita.

## Bloque E1

1. Ampliar series a varios años continuos.
2. Agregar humedad y variables oficiales autorizadas.
3. Ejecutar los cuatro modelos de pronóstico.
4. Guardar métricas y residuos.
5. Mostrar intervalos de confianza en React.

## Bloque E2

1. Ejecutar el diseño factorial.
2. Capturar OSM real con autorización comprobada.
3. Ejecutar ANOVA de dos vías.
4. Completar diseño completo/fraccionado.
5. Registrar auditoría cruzada.

## Bloque E3

1. Crear matriz de al menos cinco variables.
2. Ejecutar normalidad multivariada y Mahalanobis.
3. Completar PCA y biplot.
4. Ejecutar MANOVA.
5. Publicar resultados en React.
6. Completar SQA y sellos.

## Bloque E4

1. Cerrar el reporte técnico.
2. Crear PDF final.
3. Registrar modelo de negocio.
4. Preparar la demo.
5. Crear el video de dos minutos.
6. Entregar relatorías individuales.
7. Vincular los commits y etiquetas finales.
