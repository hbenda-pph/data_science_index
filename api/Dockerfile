# Dockerfile para API FastAPI
FROM python:3.11-slim

WORKDIR /app

# Establecer PYTHONPATH para encontrar shared
ENV PYTHONPATH=/app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar módulos shared (desde directorio raíz)
COPY shared /app/shared

# Copiar código de la API
COPY api/main.py /app/

# Exponer puerto
EXPOSE 8080

# Comando para ejecutar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

