# ---- Base image ----
FROM python:3.12-slim AS base

# ---- Environment variables ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/makinishop

# ---- System dependencies ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# ---- Set working directory ----
WORKDIR /app

# ---- Install Python dependencies ----
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---- Copy project files ----
COPY . /app/

# ---- Create non-root user ----
RUN useradd -m django \
    && mkdir -p /app/media /app/static

# ---- Set proper permissions for the non-root user ----
RUN chown -R django:django /app

# ---- Switch to django user ----
USER django

# ---- Expose port ----
EXPOSE 8000

# ---- Copy entrypoint ----
COPY entrypoint.sh /app/entrypoint.sh

# ---- Use sh to run entrypoint (avoids chmod issues) ----
ENTRYPOINT ["sh", "/app/entrypoint.sh"]

# ---- CMD to start Gunicorn ----
CMD ["gunicorn", "makinishop.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=4"]