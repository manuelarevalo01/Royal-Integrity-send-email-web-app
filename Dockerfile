FROM python:3.11-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1  # Evita que Python escriba archivos .pyc
ENV PYTHONUNBUFFERED 1        # Fuerza a que los logs de Python salgan directamente (mejor para Docker)

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./contact_api_project/app /app/app
COPY ./contact_api_project/app/templates /app/templates

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-b", "0.0.0.0:8000"]