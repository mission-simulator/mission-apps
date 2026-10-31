FROM python:3.13-slim
WORKDIR /app

COPY sensor-sim/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY libs/models/ /app/models/
COPY sensor-sim/ /app/

CMD ["python", "main.py"]