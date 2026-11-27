# ENTREGA E0: OBSERVATORIO CLIMÁTICO Y AGRÍCOLA
**Equipo:** LUIS ALFREDO RUIZ FUENTES - ARIADNA ANDREA MUÑOZ ANDRADE 
**Etiqueta:** `e0`  

---

## Resumen en Tres Líneas
Observatorio enfocado en el monitoreo histórico y pronóstico de temperatura y precipitación acumulada en municipios agrícolas de Colima. Permite a los productores evaluar riesgos de sequía/heladas y optimizar sus siembras. Implementa ingesta automatizada diaria con Open-Meteo guardando datos crudos en la capa bronce.

---

## Ingeniería de Datos
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| --- | --- | --- |
| Captura funcionando y serie histórica | [extractors/clima_extractor.py](../../extractors/clima_extractor.py) | Serie de 36 meses descargada y guardada en `data/bronce/` |
| Plan de recopilación y ética | [docs/E0/propuesta.md](../../docs/E0/propuesta.md) | Open-Meteo integrado; SMN propuesto pero no integrado ni verificado. Se documenta el `robots.txt` de Open-Meteo sin tratarlo como autorización. |

---

## Análisis Estadístico
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| --- | --- | --- |
| Preguntas analíticas planteadas | [docs/E0/propuesta.md](../../docs/E0/propuesta.md) | Definidas las 3 preguntas (Pronóstico E1, Experimento E2 y Multivariado E3) |

---

## Calidad en los Sistemas de Información
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| --- | --- | --- |
| Registros PSP y Objetivos | [calidad/](../../calidad/) | Archivos CSV de tiempo y defectos integrados + 3 objetivos medibles |

**Evidencia pendiente:** la entrevista está anonimizada y el repositorio no
incluye constancia de consentimiento ni registro independiente. La disponibilidad
de la captura se evalúa con la bitácora; no se presume que el objetivo PSP se
haya alcanzado.