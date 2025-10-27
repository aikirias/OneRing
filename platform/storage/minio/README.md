# MinIO S3 Bootcamp

## Objetivos de aprendizaje
- Entender el modelo S3-compatible de MinIO (buckets, objetos, políticas).
- Operar MinIO vía consola web, `mc` (MinIO Client) y `awscli`.
- Diseñar convenciones para zonas Bronze/Silver/Gold y versionado.
- Integrarlo con Airbyte (destino S3) y Airflow (hook boto3).

## Prerrequisitos
- Stack levantado con Docker (`docker compose up -d`).
- Credenciales desde `.env` (MINIO_ROOT_USER / MINIO_ROOT_PASSWORD) o en Infisical.

## Conceptos clave
- Buckets: `${MINIO_BUCKET_BRONZE}`, `${MINIO_BUCKET_SILVER}`, `${MINIO_BUCKET_GOLD}`.
- Endpoints: API `http://localhost:9000` y consola `http://localhost:9001`.
- Compatibilidad S3: SDKs (boto3), herramientas (`aws s3`, `mc`).

## Labs paso a paso
1) Acceso web
- Navega a `http://localhost:9001`, login con las credenciales de `.env`.
- Verifica que existan los 3 buckets (creados por `minio-client`).

2) CLI MinIO (`mc`)
- Alias y listado:
  ```bash
  docker compose run --rm minio/mc:RELEASE.2024-02-23T02-53-19Z sh -lc "\
    mc alias set local http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD && \ 
    mc ls local"
  ```
- Carga un archivo de ejemplo:
  ```bash
  mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
  mc cp platform/analytics/postgres/seeds/orders_raw.csv local/$MINIO_BUCKET_BRONZE/sample/orders_raw.csv
  ```

3) SDK boto3 (Python)
- Usa el script `ops/scripts/seed_minio.py` o un snippet:
  ```python
  import boto3
  s3 = boto3.client('s3', endpoint_url='http://localhost:9000',
                    aws_access_key_id='minioadmin', aws_secret_access_key='minioadmin',
                    region_name='us-east-1')
  s3.upload_file('platform/analytics/postgres/seeds/orders_raw.csv', 'bronze', 'samples/orders_raw.csv')
  ```

4) awscli (opcional)
- Configura perfil con endpoint custom:
  ```bash
  aws configure --profile minio
  # luego edita ~/.aws/config para agregar: endpoint_url = http://localhost:9000
  aws --profile minio s3 ls
  ```

## Ejercicios
- Define un scheme de particionamiento para Bronze (`domain/dataset/year=YYYY/month=MM/day=DD/`).
- Sube objetos comprimidos (gzip/parquet) y mide tamaños/tiempos.
- Crea una política de sólo lectura para un bucket temporal.

## Recursos
- Documentación MinIO: https://min.io/docs/minio/linux/index.html
- MinIO Client (mc): https://min.io/docs/minio/linux/reference/minio-mc.html
- Curso gratis: "MinIO for S3 practitioners" (playlist): https://www.youtube.com/playlist?list=PLFOIsHSSYIK2UO0m6CqXUOfkv8x7x2ux3
- SDK boto3: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
