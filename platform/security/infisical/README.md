# Infisical Secrets Clinic

## Objetivos
- Configurar Infisical (server, DB, Redis) y comprender su modelo de workspaces & environments.
- Gestionar machine identities y CLI para automatizar cargas de secretos.
- Integrar Infisical con Airflow y otras apps mediante SDK/API.

## Prerrequisitos
- Infisical activo en `http://localhost:8082` y DB/Redis en marcha.
- Workspace creado y Machine Identity disponible (ID/Secret) para el entorno `dev`.

## Plan
1. **Setup**: Inicialización con Docker, variables clave, UI.
2. **Secret Management**: Workspaces, folders, permissioning, rotation.
3. **Integraciones**: Airflow backend (`InfisicalSecretsBackend`), env injection, Terraform provider.
4. **Buenas prácticas**: Auditoría, RBAC, segregación dev/stage/prod.

## Actividades (Labs)
1) Sembrar secretos
   - Completa `.env` con `INFISICAL_*` y ejecuta `ops/scripts/infisical_seed.sh`.
   - Verifica en la UI de Infisical que existan `AIRFLOW_CONN_*` y `AIRFLOW_VAR_*`.

2) Airflow secret backend
   - Abre `platform/orchestration/airflow/config/infisical_backend.py` y estudia su flujo.
   - Reinicia Airflow y prueba `docker compose exec airflow-webserver env | grep AIRFLOW_CONN_` (para verificar fallback si aplica).

3) Rotación
   - Cambia `MINIO_ROOT_PASSWORD` en Infisical y reinicia Airflow.
   - Verifica que operaciones contra MinIO siguen funcionando.

## Recursos
- Docs oficiales: https://infisical.com/docs
- Quickstart video (YouTube): https://www.youtube.com/watch?v=MG3V9tOFY-8
- Comunidad Discord: https://infisical.com/discord
- Ejemplos repositorios: https://github.com/Infisical/infisical/tree/main/examples
