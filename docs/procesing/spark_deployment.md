# Spark Deployment Notes

## Cluster Startup
- Ensure `.env` is populated with `SPARK_MASTER_RPC_PORT`, `SPARK_MASTER_WEB_PORT`, and `SPARK_WORKER_WEB_PORT` values.
- Start the Spark master and worker via the ingestion profile:
  ```bash
  make up PROFILES="ingestion"
  ```
- Verify services:
  - Master web UI: `http://localhost:${SPARK_MASTER_WEB_PORT}` (default `8081`).
  - Worker web UI: `http://localhost:${SPARK_WORKER_WEB_PORT}` (default `8084`).

## Submitting Jobs
- Package application code inside `platform/procesing/spark/jobs/` (bind-mount the folder in `docker-compose.yml` if you need live editing).
- Submit a job against the local cluster:
  ```bash
  docker compose exec spark-master spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    /jobs/example_job.py
  ```
- Monitor executors and stages from the master UI; logs stream to the container stdout (`docker compose logs -f spark-master`).

## Integrations
- Airflow tasks under `platform/orchestration/airflow/dags/` can trigger Spark jobs using `SparkSubmitOperator`; update connection `spark_default` if you adjust ports.
- To read from MinIO, configure the `s3a://` endpoint with credentials from `.env` and ensure the Hadoop AWS jar is available on the classpath.
- For streaming sources (Pulsar, Kafka), add the relevant connector jars to the job submission path and expose broker hostnames through Docker networking.
