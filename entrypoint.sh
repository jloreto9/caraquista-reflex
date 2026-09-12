#!/bin/bash
set -e

# Desactivar telemetria de Reflex y fijar single worker para prevenir bloqueos por fork
export REFLEX_TELEMETRY_ENABLED=false
export GRANIAN_WORKERS=1
export PYTHONUNBUFFERED=1

echo "1. Iniciando Caddy Reverse Proxy en segundo plano (puerto 3000)..."
caddy start --config /etc/caddy/Caddyfile --adapter caddyfile

echo "2. Esperando que Caddy inicialice..."
sleep 1

echo "3. Iniciando Reflex Backend en primer plano (puerto 8000)..."
exec reflex run --backend-only --backend-port 8000 --env prod

