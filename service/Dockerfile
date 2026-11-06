# Task 3: Lightweight Inference Service Dockerfile
# CPU-only PyTorch and pinned dependencies to stay strictly below 2 GB

FROM python:3.11-slim

# Prevent python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install curl for healthcheck probes
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install pinned dependencies
# Install CPU-only torch to keep image size under 1.5 GB
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir \
        transformers==5.22.1 \
        fastapi==0.162.0 \
        uvicorn==0.54.0 \
        pydantic==2.14.3 \
        boto3==1.43.125 \
        jsonschema==4.26.0

# Copy application source code (explicitly excluding model weights)
COPY service/ /app/service/

# Create a non-root user for security
RUN useradd -m -u 1000 appuser \
    && mkdir -p /tmp/model_cache \
    && chown -R appuser:appuser /app /tmp/model_cache

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["python", "-m", "uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
