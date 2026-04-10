# Base image
FROM python:3.11-slim

# Env settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (MySQL support)
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    gcc \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies first (cache optimization 🔥)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create static & media dirs
RUN mkdir -p /app/staticfiles /app/media

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Give permission
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8002

# 🔥 Wait for DB + run app
CMD ["sh", "-c", "sleep 10 && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8002 --workers 3 --timeout 300"]