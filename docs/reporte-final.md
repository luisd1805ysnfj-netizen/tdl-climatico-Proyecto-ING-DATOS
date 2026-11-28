# Reporte técnico final · Observatorio Climático y Agrícola

## Resumen ejecutivo

El proyecto integra datos climáticos de Open-Meteo, una arquitectura
Bronce-Plata-Oro, linaje verificable, controles de calidad y una interfaz React.
El alcance presentado cubre Colima, Tecomán y Manzanillo y distingue datos
observados de referencias orientativas. No declara precios oficiales,
compradores confirmados ni recomendación agronómica.

## Flujo completo

1. Captura diaria en Bronce con reintentos, timeout y bitácora.
2. Integración y normalización.
3. Puerta Pandera y cuarentena con motivos.
4. Limpieza, imputación declarada y marcaje de atípicos.
5. Construcción de Oro diario/mensual y verificación de linaje.
6. Curación CSV/Parquet.
7. Consumo del resultado procesado por React.

## Inteligencia para el cliente

### Hallazgo 1
El sistema permite rastrear cada dato publicado hasta el archivo de bronce
correspondiente. Esta trazabilidad reduce el riesgo de presentar una cifra
climática sin procedencia.

**Incertidumbre:** los valores provienen de una celda o modelo de la API, no de
una estación automática en cada parcela.

### Hallazgo 2
Los datos permiten comparar temperaturas y precipitación entre municipios,
pero no se dispone todavía de una serie suficiente para validar pronósticos
agrícolas locales en producción.

**Incertidumbre:** ADF, ACF/PACF y intervalos requieren actualización continua
y partición temporal fuera de la muestra.

### Hallazgo 3
El contexto geoespacial de OpenStreetMap puede aportar un mínimo de cobertura
agrícola, no un inventario oficial.

**Incertidumbre:** el mapeo voluntario es incompleto y puede incluir sesgo de
representación.

## Recomendación

Usar el observatorio como apoyo de planeación y no como recomendación de
aplicación agronómica. Antes de cobro comercial: validar fuentes oficiales,
licencias, consentimiento de datos personales, cobertura geográfica y capacidad
operativa.

## Modelo de negocio preliminar

**Cliente inicial:** asociaciones, módulos de riego y dirección municipal que
necesiten reportes climáticos agregados.

**Oferta propuesta:** suscripción mensual por organización con actualizaciones,
calidad, linaje y reporte PDF.

**Costo pendiente de medir:** infraestructura React/API, almacenamiento,
capturas, soporte, licencias comerciales, revisión agronómica y monitoreo.

**Precio:** no definido hasta contar con costo operativo, volumen de usuarios
y permisos comerciales de proveedores.

**Defensa de mercado:** cobrar por automatización verificable, calidad,
linaje, alertas y soporte, no por afirmar pronósticos superiores a su
incertidumbre real.
