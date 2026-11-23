# PROPUESTA DEL OBSERVATORIO CLIMÁTICO Y AGRÍCOLA
**Documento:** `docs/E0/propuesta.md`  
**Entrega:** E0 Arranque (Proyecto Integrador)

---

## 1. Ficha del Observatorio
* **Sector:** Medio Ambiente y Agricultura (Gestión de Riesgos Climáticos).
* **Región:** Estado de Colima (Municipios de Tecomán, Colima y Manzanillo).
* **Pregunta detonadora:** ¿Cómo han variado los patrones de precipitación acumulada y temperatura en los municipios agrícolas clave de Colima durante los últimos 36 meses, y qué anomalías térmicas e hídricas se pronostican para el próximo semestre?
* **Cliente potencial:** Productores agrícolas locales (ej. zarzamora, limón, maíz), módulos de riego, asociaciones de agricultores y direcciones municipales de desarrollo rural.

---

## 2. Entrevista de Campo
* **Nombre del entrevistado:** Productor Agrícola Local
* **Cargo / Rol:** Productor y Agricultor de la Región
* **Sector / Cultivo:** Horticultura y Fruticultura (ej. Zarzamora y Limón)
* **Ubicación / Municipio:** Estado de Colima (Tecomán / Región agrícola)
* **Fecha y Duración:** Noviembre de 2026 (15 minutos)

### 5 Preguntas Requeridas y Respuestas de la Entrevista:

1. **Impacto de las Variaciones Climáticas:**
   * **Pregunta:** ¿De qué manera influyen las variaciones atípicas de temperatura y precipitación en la planeación de tus siembras, aplicación de insumos y cosechas?
   * **Respuesta:** Mucho. Ya no se puede sembrar en la fecha de antes. Si llueve antes de tiempo se puede descomponer la semilla, si se atrasa la lluvia no nace. El calor hace que el fertilizante se evapore y la fumigada no pegue. Y a la hora de cosecha, si llueve fuera de temporada se mancha o se pudre el producto. En el caso de la zarzamora, esto representaba un retraso crítico con el corte.

2. **Fuentes Actuales y Anticipación:**
   * **Pregunta:** ¿Qué medios o herramientas utilizas actualmente para consultar el pronóstico del tiempo y con cuánta anticipación necesitas la información para tomar decisiones operativas?
   * **Respuesta:** Se utiliza puro celular, noticias y en ocasiones CONAGUA. Se necesita saber mínimo con 3 días de anticipación para programar con precisión si se fumiga, se fertiliza o si se mete a la gente a cortar.

3. **Pérdidas Económicas Previas:**
   * **Pregunta:** ¿Has experimentado pérdidas de producción o afectaciones financieras recientes debido a eventos climáticos no previstos (sequías prolongadas, lluvias fuera de temporada, olas de calor)?
   * **Respuesta:** Sí. Se han registrado episodios de sequía larga seguidos de lluvias que no se esperaban. Como resultado se perdió parte de la siembra, se gastó más en riego y en volver a fumigar, y la cosecha salió de menor calidad, provocando que nos pagaran menos. Además, en ocasiones se tenía a los trabajadores listos para cortar y no se podía laborar por la lluvia, lo que implicaba tener que pagarles solo por presentarse al día.

4. **Variables Críticas:**
   * **Pregunta:** De las variables meteorológicas habituales (temperatura máxima, temperatura mínima, precipitación acumulada, humedad relativa, viento), ¿cuáles consideras más críticas para el manejo de tu cultivo?
   * **Respuesta:** 
     1. Precipitación acumulada — para saber con certeza si va a llover o no.
     2. Temperatura máxima — por las olas de calor que queman la planta.
     3. Temperatura mínima — por si llega a helar en la madrugada.
     4. Humedad y viento — para evaluar las condiciones óptimas y saber si se puede fumigar.

5. **Valor del Servicio y Certificación:**
   * **Pregunta:** ¿Estarías dispuesto a consultar o pagar por una suscripción a un reporte periódico de inteligencia climática que certifique la confiabilidad de sus datos y emita alertas tempranas?
   * **Respuesta:** Sí, si de verdad le atina para la zona y no es caro. Sí se pagaría una suscripción accesible si avisa con tiempo suficiente sobre sequías, heladas o lluvias fuertes, debido a que una pérdida en campo sale mucho más cara que el costo de la suscripción.

### Registro de Aprendizajes Clave:
* **Aprendizaje 1 (Necesidad real y operativa):** Las decisiones críticas del día a día (como la aplicación oportuna de fertilizantes, los esquemas de fumigación según el viento/humedad y la contratación de jornales de corte) dependen de un margen de anticipación de al menos 3 días con datos sumamente localizados para evitar pérdidas por mano de obra o daños al fruto (como en zarzamora).
* **Aprendizaje 2 (Oportunidad del Observatorio):** Existe una clara disposición de los productores locales a adoptar e invertir en servicios de alertas tempranas verificadas, ya que los costos asociados a eventos imprevistos —como la resiembra, el re-trabajo de fumigación y el pago de jornales caídos por lluvia— superan por amplio margen el costo de una suscripción de inteligencia climática.

---

## 3. Las Tres Preguntas Analíticas
| Fase / Metodología | Pregunta Analítica |
| --- | --- |
| **E1 - Pronóstico** *(Series de Tiempo)* | ¿Cuál será la precipitación acumulada mensual y la temperatura máxima estimada para los próximos 6 meses en Tecomán, Colima y Manzanillo? |
| **E2 - Experimento** *(Diseño Factorial)* | ¿De qué manera influye la combinación de tamaño de lote de consulta (1 vs 4 municipios), formato de almacenamiento (CSV vs Parquet) e intervalo de actualización en el tiempo de procesamiento y tasa de error del extractor de Open-Meteo? |
| **E3 - Multivariado** *(PCA y MANOVA)* | ¿Cómo se agrupan y diferencian los tres municipios observados al evaluar de forma simultánea temperatura máxima, mínima, precipitación acumulada, humedad y viento? |

---

## 4. Plan de Recopilación de Datos

### Fuente 1: Open-Meteo API (API REST)
* **Estructura y formato:** Respuestas JSON con series temporales meteorológicas.
* **Frecuencia:** Ingesta diaria automatizada.
* **Análisis ético y legal:** Datos bajo licencia CC BY 4.0 (Uso libre con atribución). No requiere API Key ni procesa datos personales.

### Fuente 2: Servicio Meteorológico Nacional (SMN / CONAGUA)
* **Estructura y formato:** Tablas HTML / Archivos CSV descargables.
* **Análisis ético y legal (robots.txt):** Extracción respetando `robots.txt`, con `User-Agent` académico identificable (`TDL-ObservatorioClimatico/1.0`) y pausa de 1.5 segundos entre peticiones para no saturar servidores.

---

## 5. Sistema de Calidad Inicial (Objetivos PSP)
1. **Disponibilidad del Extractor:** Porcentaje de ejecuciones exitosas $\ge 95\%$ en GitHub Actions.
2. **Completitud de Datos:** Menos de $2\%$ de registros nulos en la capa bronce.
3. **Eficiencia:** Ejecución del pipeline de captura en menos de 3 minutos por corrida.