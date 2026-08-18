FROM python:3.12-slim

WORKDIR /srv

# Dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt ./app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

COPY . .

WORKDIR /srv/app

EXPOSE 10000

# Forma "shell" (sin corchetes) para que $PORT se expanda en tiempo de arranque:
# Render inyecta la variable de entorno PORT y espera que la app escuche ahí.
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 \
    --access-logfile - --error-logfile - --log-level info \
    app:app
