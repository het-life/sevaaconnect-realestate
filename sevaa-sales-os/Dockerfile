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

USER sevaa

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).read()" || exit 1

CMD ["python", "-m", "uvicorn", "backend.runtime:app", "--host", "0.0.0.0", "--port", "8000"]
