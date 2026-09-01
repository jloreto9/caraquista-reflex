# ========================================================
# Stage 1: Build Frontend and Compile Assets
# ========================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system packages & build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install bun runtime
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:${PATH}"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and lockfiles
COPY . .

# Export and build static frontend & production bundle
RUN reflex export --no-zip

# ========================================================
# Stage 2: Production Runner with Caddy & FastAPI
# ========================================================
FROM python:3.12-slim

WORKDIR /app

# Install Caddy web server & runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    caddy \
    curl \
    ca-certificates \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python environment from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code, core modules, and built web assets
COPY --from=builder /app /app

# Copy Caddy reverse proxy config and entrypoint
COPY Caddyfile /etc/caddy/Caddyfile
COPY entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 3000

ENV PYTHONUNBUFFERED=1

CMD ["/app/entrypoint.sh"]
