#!/bin/bash
set -e

echo "1. Iniciando Caddy Reverse Proxy en segundo plano (puerto 3000)..."
caddy start --config /etc/caddy/Caddyfile --adapter caddyfile

echo "2. Iniciando Reflex Backend en primer plano (puerto 8000)..."
exec reflex run --backend-only --backend-port 8000 --env prod
