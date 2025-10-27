# OpenMetadata Learning Path

## Objetivos
- Comprender la arquitectura (ingestion pipelines, metadata server, Elasticsearch).
- Configurar servicios, tablas, pipelines y lineage desde YAML.
- Integrar fuentes (Airflow, Airbyte, ClickHouse, Postgres, MinIO).
- Explorar UI para gobernanza: glossary, policies, personas.

## Prerrequisitos
- OpenMetadata activo: `http://localhost:8585`.
- Elasticsearch (ya incluido en compose) iniciado.

## Plan
1. **Setup**: Docker Compose, configuración inicial, autenticación.
2. **Ingestion**: Archivos YAML (`ingestion/*.yaml`), CLI `openmetadata-ingestion ingest`.
3. **Lineage y calidad**: Métricas, profiler, integración con Great Expectations.
4. **Gobierno**: Roles, tags, glossary, data insights.

## Ejercicios (Labs)
- Ejecuta `ops/scripts/openmetadata_seed.py` y verifica los servicios creados en la UI.
- Añade un nuevo pipeline para monitorear dashboards de Grafana mediante API.
- Define un Glossary (UI) y etiqueta datasets Bronze/Silver.

## Recursos
- Docs oficiales: https://docs.open-metadata.org/
- Curso gratuito "OpenMetadata 101": https://learn.open-metadata.org/
- Webinar "Data Discovery with OpenMetadata": https://www.youtube.com/watch?v=GmYw4cbZQFw
- Repositorio de ejemplos: https://github.com/open-metadata/openmetadata
