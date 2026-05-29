FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
# Expone el endpoint anti-patron /reporte-oncall y el trigger de consolidacion.
# La consolidacion masiva se ejecuta con `python manage.py consolidar` (cron/Lambda).
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn extractor_service.wsgi:application --bind 0.0.0.0:8080 --workers 3"]
