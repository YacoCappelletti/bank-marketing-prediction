# Single image, three services (api / predict-app / dashboard) differing only by command.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

WORKDIR /app

# System deps for some wheels + a CA bundle; kept minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install pinned dependencies first for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code, config, models, and data.
COPY . .

# Run as a non-root user.
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    LOG_LEVEL=INFO

EXPOSE 8000 8501 8502

# Default command runs the API; docker-compose overrides per service.
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
