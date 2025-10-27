# ClickHouse Analytics Sprint

## Objetivos
- Entender el motor columnar, MergeTree y estrategias de particionamiento.
- Diseñar tablas Silver/Analytics con TTL, índices secundarios y materialized views.
- Integrar ClickHouse con Airflow y herramientas BI.

## Prerrequisitos
- ClickHouse activo (HTTP 8123) y base `analytics` creada.

## Plan temático
1. **Conceptos base**: Engines, primary key vs order by, TTL.
2. **Ingesta**: Client CLI, HTTP API, drivers Python (`clickhouse-driver`).
3. **Optimización**: Particiones, compression, projections, materialized views.
4. **Observabilidad**: Métricas en `/metrics`, integración Prometheus.

## Actividades (Labs)
1) Crear tabla y cargar datos
   - Revisa `changelogs/clickhouse/0001-create-silver-table.xml`.
   - Inserta datos desde Python/HTTP o `clickhouse-client`:
     ```bash
     docker compose exec clickhouse clickhouse-client -q "SELECT count() FROM analytics.orders_clean"
     ```

2) Materialized View
   - Crea una vista materializada para ventas diarias por estado.
   - Grafica en Grafana como timeseries.

## Recursos
- Docs oficiales: https://clickhouse.com/docs/en/
- Curso gratuito "ClickHouse 101": https://clickhouse.com/learn/courses
- Playlist "ClickHouse University" (YouTube): https://www.youtube.com/playlist?list=PL8ZX84YcDtz1eWfb9PcgY_QNoXjYvqcI8
- Awesome ClickHouse repos: https://github.com/Altinity/awesome-clickhouse
