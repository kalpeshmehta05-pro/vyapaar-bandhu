FROM python:3.12-slim

# Install system dependencies for Tesseract OCR and WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements-new.txt .
RUN pip install --no-cache-dir -r requirements-new.txt

# Copy application code
COPY . .

# NOTE: RSA keys are NOT generated at build time.
# In production: mount keys via Kubernetes secrets or pass via env vars.
# In development: docker-compose entrypoint generates them if missing.
# This prevents every image rebuild from invalidating all active JWTs.

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
