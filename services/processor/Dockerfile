# Usar imagen ligera de Python
FROM python:3.9-slim

# Instalar librerías de sistema para PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev gcc

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY worker.py .

# Comando para arrancar
CMD ["python", "worker.py"]