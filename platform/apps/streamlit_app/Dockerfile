FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    streamlit>=1.32 \
    pandas>=2.2 \
    numpy>=1.26 \
    mlflow[s3]>=2.9 \
    boto3>=1.34

COPY app.py ./app.py

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
