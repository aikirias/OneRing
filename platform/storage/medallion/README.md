# Medallion Architectures 101

## Propósito
- Comprender los roles de las zonas Bronze, Silver y Gold.
- Definir convenciones de naming, formatos y SLAs por capa.
- Diseñar estrategias de versionado, time-travel y borrado seguro para data lakes.

## Contenido sugerido
1. **Bronze (Raw)**
   - Ingesta sin transformar desde Airbyte.
   - Estructuras recomendadas (JSONL, Parquet), particionamiento.
2. **Silver (Conformed)**
   - Transformaciones, deduplicados, enriquecimientos.
   - Validaciones con Great Expectations.
3. **Gold (Curated)**
   - Serving layer para BI/Analytics (ClickHouse/Postgres).
   - KPIs, dashboards, data contracts.

## Actividades
- Diseña un naming convention para rutas S3/MinIO (ej. `<domain>/<dataset>/<year>/<month>`).
- Añade datos de muestra adicional en Bronze y crea scripts para moverlos a Silver.
- Documenta políticas de retención y gobernanza para cada capa.

## Recursos
- Databricks Medallion Architecture (paper): https://databricks.com/blog/2023/01/30/medallion-architecture.html
- Curso gratuito "Lakehouse Fundamentals" (Databricks): https://customer-academy.databricks.com/learn/course/714/play/2535/medallion-architecture
- Video "Modern Data Lake Best Practices" (YouTube): https://www.youtube.com/watch?v=H1Qf5wP0ViM
