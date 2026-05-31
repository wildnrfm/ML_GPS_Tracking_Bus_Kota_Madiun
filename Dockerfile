# ─────────────────────────────────────────────────────────────────────────────
#  Dockerfile — HuggingFace Spaces Deployment (ML-ETA)
#  GPS Tracker Bus Sekolah — ETA Prediction
#
#  Spaces requirements:
#    - Expose port 7860
#    - Run as non-root user (UID 1000)
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# 1. Install system dependencies (libgomp1 is required by LightGBM)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy and install Python dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# 4. Set up non-root user (UID 1000 is required by HuggingFace Spaces)
RUN useradd -m -u 1000 hfuser && \
    chown -R hfuser:hfuser /app

# 5. Copy API source code and trained models
COPY --chown=hfuser:hfuser api/     ./api/
COPY --chown=hfuser:hfuser models/  ./models/

# 6. Switch to non-root user
USER hfuser

# 7. Environment configurations
ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 7860

# 8. Container native health check (using endpoint GET /)
HEALTHCHECK --interval=60s --timeout=15s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# 9. Launch FastAPI application server
CMD ["uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--workers", "1", \
     "--log-level", "info"]
