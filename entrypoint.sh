#!/bin/bash
set -e

echo "Iniciando backend de Reflex (Uvicorn / FastAPI)..."
reflex run --backend-only --backend-port 8000 --env prod &

echo "Iniciando Caddy Reverse Proxy en puerto 3000..."
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
