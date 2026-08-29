FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SEVAA_DB_PATH=/data/sevaa.db

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY web ./web
COPY scripts ./scripts

RUN mkdir -p /data \
    && useradd --create-home --uid 10001 sevaa \
    && chown -R sevaa:sevaa /app /data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; p=os.getenv('PORT') or os.getenv('SEVAA_PORT') or '8000'; urllib.request.urlopen(f'http://127.0.0.1:{p}/api/health', timeout=3).read()" || exit 1

# The entrypoint starts as root only long enough to fix ownership on a mounted
# SQLite volume, then permanently drops to uid/gid 10001 before exec'ing uvicorn.
CMD ["python", "scripts/container_entrypoint.py"]
