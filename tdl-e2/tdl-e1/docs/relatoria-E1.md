# Relatoría E1 · Observatorio de Inteligencia Climática (Colima, Tecomán y Manzanillo)

Equipo: [COMPLETAR: integrantes] · Periodo: 2 al 13 de noviembre de 2026

> **Borrador.** Todo lo que sale de los datos y del código ya está verificado. Los campos `[COMPLETAR]` (quién hizo qué, horas, números de defecto) deben salir de su registro de tiempo y de defectos. La rúbrica califica que sea específica, honesta y verificable: no dejen ningún corchete en la versión final.

## 1. Qué nos propusimos
Automatizar el paso de bronce a plata y oro, de modo que 3 municipios × 1,081 días (3,243 registros) se limpien, integren y validen sin revisión manual, y que ningún registro inválido se borre en silencio. Meta medible: pipeline de un solo comando, puerta de calidad con cuarentena y 100 % de los registros contabilizados (aprobados + cuarentena = recibidos).

## 2. Qué hicimos
| Fecha | Qué | Quién | Horas |
|---|---|---|---|
| 9-nov | Descarga del histórico (23-nov-2023 a 7-nov-2026) de Open-Meteo para los 3 municipios, guardado tal cual en bronce | [COMPLETAR] | [COMPLETAR] |
| 10-nov | Revisión de los JSON: 0 faltantes, coordenadas distintas a las pedidas (celda de malla) y elevaciones de 37 m (Tecomán, Manzanillo) y 495 m (Colima) | [COMPLETAR] | [COMPLETAR] |
| 10-nov | Módulos de integración, puerta de calidad (pandera), limpieza y capa oro; 25 pruebas automáticas | [COMPLETAR] | [COMPLETAR] |
| 10-nov | Notebook `docs/E1/limpieza.ipynb` con experimento de imputación y análisis de atípicos | [COMPLETAR] | [COMPLETAR] |
| [COMPLETAR] | CI en GitHub Actions, revisión cruzada (Quality Lead) y etiqueta `e1` | [COMPLETAR] | [COMPLETAR] |

## 3. Qué decidimos y por qué
- **Imputar con evidencia, no por costumbre.** Como los datos reales no traen faltantes, enmascaramos el 10 % de valores reales y medimos qué método los recupera mejor. Para temperatura y viento ganó la interpolación temporal (RMSE de tmax 1.07 °C contra 1.96 °C de la media); para lluvia ganó KNN (RMSE 5.30 mm contra 6.69 mm de la mediana). Descartamos eliminar filas porque rompe la continuidad de la serie que Estadística necesita para pronosticar.
- **Atípicos: marcar y conservar.** Usamos z robusto sobre la anomalía mensual, IQR (k=3) sobre días con lluvia e Isolation Forest. Descartamos el IQR sobre el valor crudo porque marca como atípicas las noches frías normales de la temporada de secas. Resultado: 196 de 3,243 días marcados (6.0 %).
- **Prioridad entre fuentes.** Si el SMN y Open-Meteo reportan el mismo día, gana el SMN variable por variable (observación sobre reanálisis) y se guarda la discrepancia en `dif_<variable>`. [COMPLETAR si ya hay segunda fuente real; si no, decir que el adaptador está probado con datos sintéticos.]

## 4. Qué salió mal y cómo lo corregimos
- Defecto #[COMPLETAR] (función, código → revisión): el IQR sobre `log1p` de la lluvia no marcaba ningún atípico, ni siquiera los 168.9 mm de Manzanillo del 11-oct-2026, porque el logaritmo comprime justo la cola que interesa. Se cambió a escala lineal sobre días con lluvia (60 días marcados).
- Defecto #[COMPLETAR] (función, código → revisión): la imputación de lluvia usaba la mediana climatológica, que no era el método ganador del experimento (6.69 mm de RMSE contra 5.30 mm de KNN). Se cambió a KNN.
- Defecto #[COMPLETAR] (verificación, pruebas): una prueba de conversión de unidades usaba un rango fijo y fallaba por azar. Se reemplazó por una comparación contra la media esperada.
- [COMPLETAR: otros defectos reales del equipo, con tiempo de corrección]

## 5. Qué aprendimos
**Ingeniería de Datos.** Una API puede responder con otras coordenadas que las pedidas: Open-Meteo movió cada punto a su celda de malla. Guardar `lat_grid`/`lon_grid` en cada registro evita afirmar que el dato es "de Colima" cuando es de una celda con otra elevación. [COMPLETAR: algo propio del equipo.]

**Análisis Estadístico.** Con el 58 % de los días sin lluvia, ningún método de atípicos para una distribución normal sirve sobre la lluvia completa; hay que tratar aparte los días con lluvia. Lo mismo vale para los supuestos de los modelos de pronóstico. [COMPLETAR: conectar con descomposición y ARIMA.]

**Calidad en los Sistemas de Información.** La puerta de calidad es un control, no un adorno: la probamos con 7 registros dañados a propósito (lluvia negativa, tmax < tmin, municipio fuera de catálogo, viento de 900 km/h, fecha futura y 2 duplicados) y todos terminaron en cuarentena con su motivo. [COMPLETAR: conectar con el plan SQA y la fiabilidad medida.]

## 6. Evidencias
- Commits: [COMPLETAR enlaces]
- Notebook: [`docs/E1/limpieza.ipynb`](E1/limpieza.ipynb)
- Pruebas: [`tests/test_pipeline.py`](../tests/test_pipeline.py) · CI: [COMPLETAR enlace a la ejecución verde]
- Reporte de la puerta: [`data/plata/reporte_puerta_calidad.json`](../data/plata/reporte_puerta_calidad.json)

## Uso de IA generativa
Usamos Claude (Anthropic) para generar el borrador del pipeline (`pipeline/`), las pruebas, el notebook y esta plantilla de relatoría, a partir de nuestros archivos de bronce y la rúbrica del proyecto. [COMPLETAR: qué revisamos, ejecutamos y modificamos nosotros.] Cada integrante puede explicar cualquier parte del código en la defensa.
