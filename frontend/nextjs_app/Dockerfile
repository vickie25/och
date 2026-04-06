# syntax=docker/dockerfile:1.4
# Multi-stage build tuned for small VPS (1–2 GB RAM): capped Node heap, single-job native builds,
# npm settings via ENV (no extra `npm config` layer that was getting SIGKILL/137 on the droplet).

# Stage 1: Install dependencies (including devDependencies for build)
FROM node:20-alpine AS deps

WORKDIR /app

RUN apk add --no-cache libc6-compat python3 make g++

ENV NEXT_TELEMETRY_DISABLED=1
# npm reads these from the environment — avoids a separate Node process for `npm config set`
ENV npm_config_fetch_retries=10
ENV npm_config_fetch_retry_mintimeout=20000
ENV npm_config_fetch_retry_maxtimeout=120000
ENV npm_config_fetch_timeout=600000
ENV npm_config_maxsockets=1
# One g++/node-gyp job at a time lowers peak RAM during native module builds
ENV npm_config_jobs=1
# Smaller heap during npm ci on 1–2 GB RAM hosts (next build gets a higher cap in builder)
ENV NODE_OPTIONS=--max-old-space-size=1024

COPY frontend/nextjs_app/package.json frontend/nextjs_app/package-lock.json* ./

# set -e: required — plain `sh -c` does not abort on OOM/kill; `||` chains used to continue with broken node_modules.
# --omit=optional: fewer packages → lower peak RAM (if something breaks, remove this flag).
RUN --mount=type=cache,target=/root/.npm \
    set -eux; \
    if [ -f package-lock.json ]; then \
      npm ci --prefer-offline --no-audit --legacy-peer-deps --omit=optional; \
    else \
      npm install --prefer-offline --no-audit --legacy-peer-deps --omit=optional; \
    fi; \
    npm cache clean --force; \
    rm -rf /tmp/* 2>/dev/null || true

# Stage 2: Build the application
FROM node:20-alpine AS builder

WORKDIR /app

# Do NOT install gcc/python here — BuildKit would run this in parallel with the deps stage's
# `npm ci` and roughly double peak RAM (OOM 137 on small VPS). Native modules compile in `deps` only.

COPY --from=deps /app/node_modules ./node_modules

COPY frontend/nextjs_app/package.json frontend/nextjs_app/package-lock.json* ./

COPY frontend/nextjs_app/ .

RUN echo "=== Checking for missionStore ===" && \
    test -f lib/stores/missionStore.ts && echo "✓ missionStore.ts exists at lib/stores/" || echo "✗ missionStore.ts NOT FOUND at lib/stores/" && \
    head -3 lib/stores/missionStore.ts 2>&1 && \
    rm -rf .next node_modules/.cache 2>/dev/null || true

ARG NEXT_PUBLIC_DJANGO_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_FASTAPI_API_URL=http://localhost:8001
ARG NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
ARG NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID=
ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID=
ARG GROK_API_KEY
ARG GROK_API_KEY_RECIPE
ARG GROK_API_KEY_COACHING

ENV NEXT_PUBLIC_DJANGO_API_URL=${NEXT_PUBLIC_DJANGO_API_URL}
ENV NEXT_PUBLIC_FASTAPI_API_URL=${NEXT_PUBLIC_FASTAPI_API_URL}
ENV NEXT_PUBLIC_FRONTEND_URL=${NEXT_PUBLIC_FRONTEND_URL}
ENV NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID=${NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID}
ENV NEXT_PUBLIC_GOOGLE_CLIENT_ID=${NEXT_PUBLIC_GOOGLE_CLIENT_ID}
ENV GROK_API_KEY=${GROK_API_KEY}
ENV GROK_API_KEY_RECIPE=${GROK_API_KEY_RECIPE}
ENV GROK_API_KEY_COACHING=${GROK_API_KEY_COACHING}
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV NEXT_BUILD_VERBOSE=1
# next.config.js reads this: fewer workers / threads → lower peak RAM on small hosts
ENV NEXT_BUILD_LOW_MEMORY=1
# Match deps cap: on a 2 GB RAM host, higher heaps invite OOM; use swap (deploy/ensure-swap-2g.sh) if build OOMs.
ENV NODE_OPTIONS=--max-old-space-size=2048
ENV npm_config_jobs=1

RUN set -eux; \
    mv .eslintrc.json .eslintrc.json.bak 2>/dev/null || true; \
    mv eslint.config.mjs eslint.config.mjs.bak 2>/dev/null || true; \
    echo "=== Starting Next.js build (low-memory profile) ==="; \
    for attempt in 1 2 3; do \
      echo "=== Build attempt $attempt of 3 ===" && \
      if npm run build 2>&1; then \
        echo "✓ Build succeeded on attempt $attempt" && \
        break; \
      else \
        echo "✗ Build failed on attempt $attempt" && \
        if [ $attempt -lt 3 ]; then \
          delay=$((10 * attempt)) && \
          echo "Cleaning cache and waiting ${delay}s before retry..." && \
          rm -rf .next node_modules/.cache 2>/dev/null || true && \
          sleep $delay; \
        else \
          echo "✗ All build attempts failed" && \
          exit 1; \
        fi; \
      fi; \
    done && \
    echo "=== BUILD SUCCEEDED ===" && \
    ls -la /app/.next/ 2>&1 && \
    if [ ! -d /app/.next/standalone ]; then \
      echo "ERROR: Standalone directory not found after build!" && \
      ls -la /app/.next/ 2>&1 && \
      exit 1; \
    fi && \
    if [ -d /app/.next/static ]; then \
      echo "Static directory exists"; \
      ls -la /app/.next/static/ | head -10; \
    else \
      mkdir -p /app/.next/static; \
    fi && \
    npm cache clean --force 2>/dev/null || true && \
    rm -rf /tmp/* /root/.npm/_cacache/tmp/* 2>/dev/null || true

# Stage 3: Production runner (minimal image)
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./app/public
COPY --from=builder /app/.next/static ./app/.next/static

RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})" || exit 1

CMD ["sh", "-c", "if [ -f /app/server.js ]; then node /app/server.js; elif [ -f /app/app/server.js ]; then node /app/app/server.js; elif [ -f /app/.next/standalone/server.js ]; then node /app/.next/standalone/server.js; else echo 'ERROR: No Next.js server entrypoint found'; ls -la /app; ls -la /app/app 2>/dev/null || true; ls -la /app/.next/standalone 2>/dev/null || true; exit 1; fi"]
