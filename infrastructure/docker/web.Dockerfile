# Borda web: build do frontend (esbuild) servido pelo Caddy, que também faz o proxy de /api para o
# backend — mesmo domínio, sem CORS (ADR-011). Contexto de build: raiz do monorepo.
#   docker build -f infrastructure/docker/web.Dockerfile -t alloy-web .
FROM node:22-slim AS build
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
COPY docs/openapi.json /src/docs/openapi.json
RUN npm run typecheck && npm run lint && npm run build

FROM caddy:2.8-alpine
COPY infrastructure/deployment/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/frontend/dist /srv
EXPOSE 80 443
