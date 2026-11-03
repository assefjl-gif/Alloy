# Backend (FastAPI + uvicorn). Contexto de build: raiz do monorepo.
#   docker build -f infrastructure/docker/backend.Dockerfile -t alloy-api .
# O mesmo image roda as migrações (python -m app.cli preparar) no serviço "migrate" do compose.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend

# Dependências primeiro (camada reaproveitada enquanto o pyproject não muda).
COPY backend/pyproject.toml ./
COPY backend/app/__init__.py ./app/__init__.py
# Instala só as dependências: o pacote em si roda do diretório de trabalho, porque o seed e as
# migrações são achados por caminho relativo ao código (../database).
RUN pip install --upgrade pip && pip install . && pip uninstall -y alloy-virtual-lab-backend

# Código, migrações e seeds (o seed SQL lê ../database/seeds).
COPY backend/ ./
COPY database/ /app/database/
RUN useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin alloy \
    && mkdir -p /app/var/arquivos && chown -R alloy /app/var

USER alloy
ENV ALLOY_ENV=prod \
    ALLOY_STORAGE_DIR=/app/var/arquivos
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status == 200 else 1)"

# --proxy-headers: o IP real do cliente vem do Caddy (usado no bloqueio de login por IP).
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*", "--no-server-header"]
