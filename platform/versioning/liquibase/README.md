# Liquibase Schema Versioning Track

## Objetivos
- Entender el flujo de `changeLogFile`, `changeSets` y contextos.
- Gestionar migraciones para Postgres y ClickHouse desde Docker.
- Integrar Liquibase con pipelines CI/CD y orquestadores.

## Prerrequisitos
- Contenedores en marcha y propiedades listas en `platform/versioning/liquibase/liquibase-*.properties`.

## Contenido recomendado
1. **Fundamentos**: `databaseChangeLog`, tipos de cambios, tags.
2. **Configuración**: Propiedades (`liquibase-*.properties`), drivers, CLI.
3. **Mejores prácticas**: Convenciones de IDs, rollback, testing.
4. **Automatización**: Uso de `docker compose --profile tools run liquibase`.

## Ejercicios (Labs)
1) Postgres
   - Revisa `changelogs/postgres/0001-create-gold-table.xml` y añade índices.
   - Aplica con: `docker compose --profile tools run --rm liquibase --defaultsFile=platform/versioning/liquibase/liquibase-postgres.properties update`.

2) ClickHouse
   - Crea un changeSet que añada una materialized view para agregados.
   - Ejecuta update (requiere driver):
     ```bash
     docker compose --profile tools run --rm -e LIQUIBASE_CLASSPATH=/liquibase/drivers/liquibase-clickhouse-extension.jar \
       liquibase --defaultsFile=platform/versioning/liquibase/liquibase-clickhouse.properties update
     ```

3) Diff y rollback
   - Genera un `updateSQL` y `rollbackSQL` para validar antes de aplicar.

## Recursos
- Docs oficiales: https://docs.liquibase.com/
- Curso gratis "Liquibase Fundamentals" (YouTube): https://www.youtube.com/playlist?list=PLbAYX18iLtMaSXDhHBfqoTUeb5GsyhQOd
- Workshop OSS: https://learn.liquibase.com/
- Ejemplos multi-base de datos: https://github.com/liquibase/liquibase-examples
