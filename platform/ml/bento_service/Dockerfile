FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BENTOML_HOME=/home/bento/bentoml

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    pip install --no-cache-dir bentoml>=1.1 mlflow[s3]>=2.9 pandas>=2.1 numpy>=1.24 scipy && \
    apt-get purge -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

WORKDIR /service

COPY service.py ./service.py

CMD ["bentoml", "serve", "oner_model_service:latest", "--host", "0.0.0.0", "--port", "3001"]
