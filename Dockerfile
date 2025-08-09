# Use official Python image matching Render's supported version
FROM python:3.10.13-slim-buster

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Install system dependencies + PostgreSQL client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project (with .dockerignore filtering)
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Runtime command (overridden for workers in render.yaml)
CMD ["gunicorn", "DjangoCommerce.wsgi:application", \
     "--bind", "0.0.0.0:$PORT", \
     "--workers", "4", \
     "--timeout", "120"]