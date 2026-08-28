# AIPI — AI Protocol Interface Production Docker Image (Developed by gnonymous)
# Build: docker build -t aipi .
# Run:   docker run -d -p 11434:11434 -v aipi_data:/app/data --name aipi aipi

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gateway_server.py api_client.py db.py vault.py router.py cache.py virtual_keys.py \
     analytics.py auth.py license.py ratelimit.py oidc.py reports.py providers_preset.py \
     claude_profiles.py history.py ide_config.py oauth_manager.py \
     pii_redactor.py build_app.py ./
COPY web/ ./web/

# Volumes for persistent data (SQLite DB + config)
ENV AIMM_DATA_DIR=/app/data
ENV AIMM_BIND_HOST=0.0.0.0
VOLUME ["/app/data"]

EXPOSE 11434

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:11434/v1/health', timeout=3)" || exit 1

CMD ["python", "gateway_server.py", "run", "11434", "--host", "0.0.0.0"]
