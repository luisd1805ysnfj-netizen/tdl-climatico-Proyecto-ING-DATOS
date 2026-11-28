# Relatoría final · E0–E4

## 1. Qué nos propusimos

Integrar ingeniería de datos, estadística y calidad en un observatorio
climático agrícola reproducible para Colima, Tecomán y Manzanillo.

## 2. Qué hicimos

| Periodo | Evidencia | Responsable |
|---|---|---|
| Noviembre de 2026 | Entrevista declarada y propuesta E0 | Luis Alfredo Ruiz Fuentes y Ariadna Andrea Muñoz Andrade |
| Noviembre de 2026 | Pipeline Bronce-Plata-Oro, puertas de calidad y linaje | Equipo |
| Noviembre de 2026 | Optimización E3 y dataset curado | Equipo |
| Esta revisión | React como interfaz oficial y laboratorio reproducible | Revisión técnica automatizada |

Las horas individuales y enlaces de implementación final deben registrarse en
la bitácora PSP antes de publicar.

## 3. Qué decidimos y por qué

Elegimos React como interfaz pública porque ya contenía el mapa, gráficas,
precios, rutas y fuentes. Conservamos una única interfaz para evitar sistemas
presentando datos distintos. Usamos JSON estático exportado desde la capa Oro
cuando no corresponde consultar una API.

## 4. Qué salió mal y cómo lo corregimos

- E1 e E2 contenían partes incompletas; se conservaron como pendientes
  explícitas y no se declararon completas.
- Existían copias históricas de proyecto; se compararon y eliminaron sin
  migrar archivos únicos adicionales.
- La documentación nombraba una segunda interfaz histórica; se actualizó para
  referirse únicamente a React.
- Se completaron scripts E1, E2 observacional y E3 reproducibles.
- Se añadieron registros PSP individuales y cálculo de disponibilidad/MTBF/MTTR.

## 5. Qué aprendimos

La trazabilidad y el manejo explícito de incertidumbre son parte del producto,
no anexos. Los datos no sustituyen mediciones locales ni juicio profesional.

## 6. Evidencias

- [Reporte final](reporte-final.md)
- [Dataset curado](../data/curated/)
- [Laboratorio](../laboratorio/)
- [Fuentes y interfaz React](../frontend/src/App.jsx)

## Uso de IA generativa

Se utilizó IA para comparación, consolidación documental y automatización.
Las cifras se generaron desde archivos locales o se dejaron pendientes cuando
no existía evidencia. Los integrantes deben validar cada resultado y poder
explicar las decisiones técnicas.
