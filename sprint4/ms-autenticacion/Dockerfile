FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
# Aplica migraciones y arranca gunicorn. La semilla se ejecuta aparte (ver seed/).
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn empresas_service.wsgi:application --bind 0.0.0.0:8080 --workers 3"]
