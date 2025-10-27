# Airflow Bootcamp

## Objetivos de aprendizaje
- Comprender la arquitectura de Airflow (scheduler, webserver, workers, metastore) y el modelo DAG/task.
- Configurar conexiones, variables y backends de secretos en un entorno distribuido.
- Diseñar DAGs orientados a data engineering (medallion, orquestación de pipelines, integración con APIs).
- Integrar Airflow con herramientas externas (Airbyte, ClickHouse, Postgres, Great Expectations).

## Prerrequisitos
- Docker en local y este repo levantado con `docker compose up -d`.
- Python 3.9+ para ejecutar scripts de apoyo (opcional).

## Itinerario sugerido
1. **Fundamentos**
   - Conceptos clave de DAG, operadores, sensores, hooks.
   - Diferencias entre ejecutores (Sequential, Local, Celery, Kubernetes).
   - Gestión de dependencias y programación.
2. **Configuración avanzada**
   - Backend de secretos (`InfisicalSecretsBackend`).
   - Conexiones dinámicas vía API/UI y `airflow connections` CLI.
   - Gestión de logs remotos y observabilidad con Prometheus/Grafana.
3. **Desarrollo de DAGs**
   - DAG medallion (`medallion_batch_demo`) como caso de estudio.
   - `@task` vs `PythonOperator`, uso de XCom y TaskFlow API.
   - Integración con Airbyte y ClickHouse mediante hooks/requests.
4. **Operaciones**
   - Estrategias de despliegue Docker Compose/Kubernetes.
   - Monitoreo con Flower, métricas y alertas.
   - Buenas prácticas de versionado y testing de DAGs.

## Hands-on (Labs guiados)
1) Explorar el DAG de ejemplo
   - Accede a `http://localhost:8080` (usuario: admin, pass: admin si no cambiaste `.env`).
   - Localiza `medallion_batch_demo` y revisa su grafo y tareas.
   - Desde CLI: `docker compose exec airflow-webserver airflow dags list`.

2) Ejecutar el DAG end-to-end
   - Asegúrate de tener MinIO con datos: `python3 ops/scripts/seed_minio.py` (opcional, Airbyte también los genera).
   - Dispara el DAG: `docker compose exec airflow-webserver airflow dags trigger medallion_batch_demo`.
   - Monitorea logs desde UI o `docker compose logs -f airflow-worker`.

3) Añadir una validación con GE
   - Edita `platform/quality/great_expectations/expectations/orders_silver.json` para agregar una expectation extra.
   - Re-ejecuta el DAG y verifica fallos en la tarea de validación.

4) Crear un nuevo DAG
   - Copia `platform/orchestration/airflow/dags/medallion_batch.py` como base.
   - Cambia el origen (prefijo de MinIO) y la tabla destino en ClickHouse.
   - Comprueba import con `docker compose exec airflow-webserver airflow dags list`.

## Recursos recomendados
- Documentación oficial: https://airflow.apache.org/docs/
- Curso freeCodeCamp "Apache Airflow 2.0 for Beginners" (YouTube): https://youtu.be/2lzmAlUHT0w
- Astronomer Academy (gratuito): https://academy.astronomer.io/
- Guía TaskFlow API: https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html
- Talk "Scaling Airflow" (Data Council): https://www.youtube.com/watch?v=nhx6l3-BVrY
