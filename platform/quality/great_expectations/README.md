# Great Expectations Workshop

## Objetivos
- Comprender el modelo de `DataContext`, `Expectation Suite` y `Checkpoint`.
- Diseñar validaciones para cada capa del medallion (Bronze/Silver/Gold).
- Integrar GE con Airflow y registrar resultados para observabilidad/catalogación.

## Prerrequisitos
- Entorno levantado y `platform/quality/great_expectations/` montado en Airflow.
- Python 3.9+ opcional para probar GE en local.

## Módulos de aprendizaje
1. **Fundamentos**: Expectations básicas (`expect_column_values_to_not_be_null`, etc.).
2. **Configuración**: `great_expectations.yml`, data connectors, stores.
3. **Ejecución**: Checkpoints, CLI vs programación con Python.
4. **Integraciones**: Notebooks, Data Docs, webhook/Slack.

## Actividades (Labs)
1) Validar Bronze
   - Revisa `expectations/orders_bronze.json` y ejecuta el DAG para ver resultados.
   - Forzar un fallo (ej. poner `min_value` alto) y observar el comportamiento del DAG.

2) Nuevo checkpoint para Gold
   - Crea `checkpoints/orders_gold.yml` que lea desde una query a Postgres.
   - Añade la ejecución en un DAG dedicado.

3) Data Docs
   - Configura un `FilesystemStoreBackend` o S3 (MinIO) para `data_docs_sites` y publica.

## Recursos
- Docs oficiales: https://docs.greatexpectations.io/
- Curso gratis "Data Quality with Great Expectations" (DataCamp free tier): https://app.datacamp.com/learn/courses/data-quality-with-great-expectations
- Workshop PyData 2022: https://www.youtube.com/watch?v=U9n7fB8aQxg
- Repo de ejemplos OSS: https://github.com/great-expectations/great_expectations/tree/develop/examples
