FROM python:3.14-slim

ARG VCS_REF=unknown
LABEL org.opencontainers.image.revision=$VCS_REF

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    DATA_DIR=/var/lib/moopiew \
    DATABASE_PATH=/var/lib/moopiew/moopiew.sqlite3

RUN addgroup --gid 10001 moopiew \
    && adduser --uid 10001 --gid 10001 --disabled-password --gecos "" moopiew
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt
COPY --chown=moopiew:moopiew app.py ./
COPY --chown=moopiew:moopiew migrations ./migrations
COPY --chown=moopiew:moopiew scripts/document-storage.py ./scripts/document-storage.py
COPY --chown=moopiew:moopiew web ./web
RUN mkdir -p /var/lib/moopiew && chown moopiew:moopiew /var/lib/moopiew

USER 10001:10001
EXPOSE 8000
VOLUME ["/var/lib/moopiew"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/ready', timeout=3).read()"]
CMD ["python", "app.py"]
