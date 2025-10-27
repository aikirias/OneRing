# Airbyte Accelerator

## Objetivos de aprendizaje
- Entender la arquitectura Airbyte (server, worker, temporal, webapp).
- Configurar conectores source/destination y programar sincronizaciones.
- Gestionar workspaces, conexiones y deployments automatizados.
- Integrar Airbyte con MinIO/S3 y orquestar ejecuciones desde Airflow.

## Prerrequisitos
- Stack en marcha (`docker compose up -d`).
- Opcional: ejecutar `make bootstrap` para registrar una conexión demo.

## Plan de estudio
1. **Introducción**: Conexiones full-refresh vs incremental, normalización.
2. **Instalación y configuración**: Docker Compose, variables de entorno, autenticación.
3. **Automatización**: Uso de la API REST (`ops/scripts/bootstrap_airbyte.py`).
4. **Monitoreo y debugging**: Logs, métricas, retries, schema changes.

## Prácticas guiadas (Labs)
1) Crear conexión desde la UI
   - Ir a `http://localhost:8000`, crear Source `Faker` y Destination `S3` (endpoint `http://minio:9000`).
   - Seleccionar bucket `${MINIO_BUCKET_BRONZE}` y formato JSONL sin compresión.
   - Ejecutar la sincronización y verificar archivos en MinIO.

2) Automatizar con la API
   - Revisa `ops/scripts/bootstrap_airbyte.py` y ejecuta: `python3 ops/scripts/bootstrap_airbyte.py`.
   - Cambia el destino a Postgres (consulta `destination-postgres` en docs) y vuelve a crear.

3) Incremental vs Full refresh
   - Cambia el modo de sync y observa cambios de archivos/particiones.
   - Agrega normalización si corresponde.

## Recursos adicionales
- Docs oficiales: https://docs.airbyte.com/
- Playlist Airbyte OSS (YouTube): https://www.youtube.com/playlist?list=PL6SpBOt1KXwaPBRDsoZcH6RyXRIGHTxd
- Curso gratuito "Airbyte Tutorial" (DataTalks.Club): https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/airbyte
- Comunidad Slack: https://airbyte.com/community
