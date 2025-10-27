# Postgres Curated Data Lab

## Objetivos
- Configurar Postgres como capa Gold para datasets curados.
- Diseñar esquemas analíticos (star schema, snapshots) y políticas de seguridad.
- Automatizar migraciones con Liquibase y monitoreo básico.

## Prerrequisitos
- Postgres expuesto en `localhost:5432` con DB `curated` y usuario `${CURATED_PG_USER}`.

## Contenidos
1. **Fundamentos**: Roles, schemas, extensión `pg_stat_statements`.
2. **Modelado**: Slowly Changing Dimensions, snapshots (`gold.orders_snapshot`).
3. **Operaciones**: Backup/restore, vacuum/analyze, replication.
4. **Integración**: Conexión con Airflow, BI tools, CDC hacia ClickHouse.

## Ejercicios (Labs)
1) Modelado y migraciones
   - Revisa `seeds/001_init.sql` y agrega nuevos schemas (finance, marketing).
   - Aplica cambios con Liquibase (ver README de Liquibase).

2) Vistas materializadas
   - Crea una MV que consuma desde `gold.orders_snapshot`.
   - Programa refresh con Airflow.

3) Observabilidad
   - Añade `postgres_exporter` y configúralo en Prometheus.

## Recursos
- Docs oficiales: https://www.postgresql.org/docs/
- Libro gratuito "PostgreSQL Tutorial": https://www.postgresqltutorial.com/
- Curso freeCodeCamp "PostgreSQL Full Course" (YouTube): https://youtu.be/qw--VYLpxG4
- Data Modeling Guide: https://www.vertabelo.com/blog/data-modeling-in-postgresql
