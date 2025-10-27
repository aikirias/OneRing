# Grafana Observability Lab

## Objetivos
- Construir dashboards para pipelines de datos (Airflow, MinIO, ClickHouse).
- Gestionar datasources (Prometheus) y provisioning as code.
- Crear alertas y compartir paneles.

## Prerrequisitos
- Prometheus datasource provisionado (ver `provisioning/datasources/datasource.yaml`).
- Dashboard de ejemplo disponible en `dashboards/data-platform.json`.

## Roadmap
1. **Fundamentos**: Panels, queries, variables, templating.
2. **Provisioning**: Datasources (`provisioning/datasources`), dashboards como JSON.
3. **Alerting**: Contact points, notification policies, Grafana OnCall.
4. **Extensiones**: Plugins OSS, integra Loki/Tempo para logs/traces.

## Ejercicios (Labs)
1) Importar y extender un dashboard
   - Importa `dashboards/data-platform.json` desde la UI.
   - Añade un panel para `sum(rate(minio_s3_requests_total[5m]))` con breakdown por operación.

2) Variables
   - Crea variables para `dag` y `instance` y úsalas en queries.

3) Alertas
   - Crea una alerta cuando `airflow_task_duration_seconds_bucket` supere un umbral P95.

## Recursos
- Docs oficiales: https://grafana.com/docs/grafana/latest/
- Grafana Fundamentals (gratis): https://grafana.com/grafana/fundamentals
- Playlist ObservabilityCon: https://www.youtube.com/playlist?list=PLDGkOdUX1NlyaSDCdtH-VpdcZ-D6ZuA60
- Dashboards Gallery: https://grafana.com/grafana/dashboards/
