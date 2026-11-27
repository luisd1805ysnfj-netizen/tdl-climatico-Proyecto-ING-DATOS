# Relatoría E3 · Optimización, trazabilidad y dataset curado

## 1. Objetivo de la etapa

La meta fue medir una mejora real del pipeline, comparar el antes y el después
con la misma entrada y entregar una versión curada de la capa Oro con licencia,
diccionario de datos e instrucciones reproducibles. La medición se hizo sobre
los archivos locales de bronce: no se incorporaron resultados sintéticos ni
solicitudes de red.

## 2. Situación inicial

El pipeline local leía 39 JSON de bronce y 3,495 filas. La deduplicación
conservaba 3,294 registros únicos y enviaba 201 capturas repetidas a
cuarentena. La puerta de calidad no rechazaba registros, las cuatro variables
climáticas críticas no tenían faltantes, y las 13,176 referencias de linaje se
verificaban sin fallos.

El perfil indicó que `consolidar_fuentes` era el costo dominante. Para cada una
de las cuatro variables, el código llamaba una función Python por grupo para
calcular máximos, mínimos y comprobar cuántos valores existían. En el conjunto
actual hay miles de grupos diarios, aunque casi todos contienen una sola fuente.

## 3. Decisiones e implementación

Se sustituyeron esas funciones por las agregaciones nativas de pandas
`min`, `max` y `count` sobre el `DataFrameGroupBy`. La resta se publica solo
cuando el conteo de valores de esa variable es mayor que uno; así se conserva el
comportamiento previo para los días con una sola fuente. Se añadió una
regresión para cubrir tanto la diferencia entre dos fuentes como el caso de un
solo valor disponible.

El benchmark [`scripts/benchmark_e3.py`](../scripts/benchmark_e3.py) extrae el
código anterior del commit `b96c6f878ec8b4ae2e460045b0fedcc8385277b4`, usa los
mismos archivos de bronce, separa los directorios de salida y repite tres veces
cada variante en orden intercalado. Además de tiempos y pico de `tracemalloc`,
compara conteos de calidad y hashes de Plata, Oro diario y Oro mensual; no crea
el reporte si encuentra diferencias de datos.

La captura ya implementaba reintentos exponenciales, timeout, comprobación de
unidades/esquema y escritura atómica, por lo que esas defensas se conservaron.
La tasa de errores HTTP se consultó en la bitácora existente y se reporta aparte:
el replay del pipeline no reproduce una conexión de red.

## 4. Resultado medido

| Métrica | Baseline | Optimizado |
|---|---:|---:|
| Mediana de tiempo | 7.041 s | 4.378 s |
| Mediana de pico `tracemalloc` | 12.36 MiB | 12.32 MiB |
| Diferencia de tiempo | — | −37.81% |
| Diferencia de pico trazado | — | −0.34% |
| Duplicados en cuarentena | 201 | 201 |
| Rechazos de calidad / valores críticos faltantes | 0 / 0 | 0 / 0 |
| Reducción de errores de calidad | — | No observada: ambas variantes tuvieron 0 rechazos |
| Fallos de linaje | 0 | 0 |
| Paridad por hash de las tres salidas | — | Sí |

La conclusión respaldada por la medición es una reducción de tiempo. No hubo
reducción medible de errores porque la variante base ya tenía cero rechazos; el
resultado de calidad se mantuvo. El cambio
de memoria es pequeño y está dentro de lo que puede variar entre ejecuciones;
`tracemalloc` no mide toda la memoria nativa de las bibliotecas científicas. No
se presenta como una mejora sustancial de RAM.

La bitácora de captura contiene 45 intentos: 42 exitosos y 3 fallos HTTP 429,
sin timeout registrado. Esto es un conteo de adquisición y no una diferencia
entre las dos ejecuciones offline del pipeline.

## 5. Dataset publicado

Se ejecutó el pipeline optimizado y después
[`scripts/curate_e3.py`](../scripts/curate_e3.py). La validación generó:

- 3,294 filas × 29 columnas, sin nulos en los campos publicados.
- Fechas de observación del 2023-11-23 al 2026-11-24 y tres municipios de
  Colima.
- CSV y Parquet. Parquet conserva `float32`, categorías e enteros compactos;
  CSV facilita inspección manual y guarda decimales con seis posiciones.
- Linaje por variable, referencia al archivo y SHA-256 del bronce.
- Licencia CC BY 4.0 y atribución a Open-Meteo en
  [`data/curated/LICENSE-DATA.md`](../data/curated/LICENSE-DATA.md).

Los 197 registros marcados como atípicos se conservan para análisis y revisión;
no se interpretan automáticamente como errores. Esta extracción no tiene
imputaciones ni filas creadas para completar calendario. El
[`datasheet`](E3/datasheet.md) documenta cada columna, rangos, procedencia y
limitaciones.

## 6. Lecciones aprendidas y limitaciones

- El perfilado localizó un costo evitable en callbacks Python; usar primitivas
  vectorizadas mejoró el tiempo sin cambiar el resultado.
- La paridad de hashes complementa las pruebas unitarias: garantiza que una
  mejora de rendimiento no alteró las tablas completas en esta entrada.
- Reprocesar el mismo bronce no mide latencia, disponibilidad ni errores de la
  API. Esos datos requieren una medición de adquisición separada.
- La reducción de RAM no fue significativa; una próxima optimización necesita
  medir RSS del proceso completo, además de `tracemalloc`.
- El dataset cubre únicamente Colima y Open-Meteo Archive. No hay captura real
  OSM en el bronce y no debe presentarse como una red de estaciones ni como una
  predicción meteorológica.

## 7. Próximos pasos

1. Revisar la ficha y los cambios, crear el commit de entrega y etiquetar ese
   commit como `e3`.
2. Ampliar la validación con nuevas fuentes solo cuando exista una captura real,
   licencia compatible y linaje verificable.
3. Medir RSS y rendimiento en el runner de CI para contrastar con el equipo
   local; conservar el replay reproducible como referencia.
4. Someter los atípicos y la cobertura espacial a revisión de dominio antes de
   usarlos en recomendaciones agrícolas.
