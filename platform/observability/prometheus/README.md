# Prometheus Metrics Track

## Objetivos
- Configurar scrape configs para servicios de datos (Airflow, MinIO, ClickHouse).
- Comprender PromQL para analizar rendimiento y SLAs.
- Integrar Prometheus con Grafana y alertmanager.

## Prerrequisitos
- Prometheus levantado en `http://localhost:9090` y config en `prometheus.yml`.

## Contenido
1. **Setup**: Prometheus.yml, targets, relabeling.
2. **PromQL**: Agregaciones, rate/increase, recording rules.
3. **Alerting**: Alertmanager, routing, silencios.
4. **Exporters**: Airflow metrics endpoint, MinIO cluster metrics, ClickHouse exporter.

## Tareas (Labs)
1) Nuevos targets
   - Añade `postgres_exporter` (opcional) y expón métricas.

2) Consultas PromQL
   - Latencia media de DagRuns: `avg(rate(airflow_dagrun_duration_sum[5m]) / rate(airflow_dagrun_duration_count[5m]))`.
   - Throughput de MinIO: `sum(rate(minio_s3_requests_total[5m])) by (api)`.

3) Reglas de alerta
   - Define un rule file y dispara una alerta cuando no haya métricas de Airflow por N minutos.

## Recursos
- Prometheus Docs: https://prometheus.io/docs/introduction/overview/
- Libro gratuito "Monitoring with Prometheus": https://prometheus.io/docs/introduction/first_steps/
- Curso freeCodeCamp "Prometheus & Grafana" (YouTube): https://youtu.be/h4Sl21AKiDg
- PromQL Playground: https://promlabs.com/promql-cheat-sheet
