FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit>=1.31 requests>=2.31 pandas>=2.1

COPY app.py ./app.py

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
