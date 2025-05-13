# 1. Usar una imagen base oficial de Python ligera
FROM python:3.11-slim
# O usa la versión exacta de Python con la que desarrollaste si es crítica.

# 2. Establecer variables de entorno (opcional pero bueno)
ENV PYTHONDONTWRITEBYTECODE 1  # Evita que Python escriba archivos .pyc
ENV PYTHONUNBUFFERED 1        # Fuerza a que los logs de Python salgan directamente (mejor para Docker)

# 3. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Copiar solo el archivo de requerimientos primero
# Esto aprovecha el caché de Docker: si requirements.txt no cambia, no reinstala todo
COPY requirements.txt .

# 5. Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copiar todo el código de tu aplicación al directorio de trabajo /app
# Asegúrate que la ruta 'contact_api_project/.' sea correcta si tu código está dentro de esa carpeta
# Si 'app' y 'templates' están directamente en la raíz junto al Dockerfile, sería:
# COPY ./app /app/app
# COPY ./templates /app/templates
# AJUSTA ESTO SEGÚN TU ESTRUCTURA EXACTA. Viendo tu imagen, parece que tu código Python está en contact_api_project/app
COPY ./contact_api_project/app /app/app
COPY ./contact_api_project/app/templates /app/templates

# 7. Exponer el puerto en el que Gunicorn/Uvicorn escuchará dentro del contenedor
# Este es el puerto INTERNO del contenedor. Lo mapearás a un puerto externo al ejecutarlo.
EXPOSE 8000

# 8. Comando para ejecutar la aplicación cuando el contenedor inicie
# Usa gunicorn con workers uvicorn para producción.
# Asegúrate que 'app.main:app' apunte a tu instancia FastAPI en app/main.py
# Escucha en 0.0.0.0 para ser accesible desde fuera del contenedor.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-b", "0.0.0.0:8000"]