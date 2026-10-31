FROM python:3.13-slim
WORKDIR /app

COPY ingest/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY libs/models/ /app/models/
COPY ingest/ /app/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]