# Multi-stage build tuned for small VPS: Debian bookworm-slim (glibc) so npm uses prebuilt
# binaries far more often than Alpine/musl (which forces gcc/python during npm ci and spikes RAM).
# See deploy/build-next-low-mem.sh (BuildKit parallelism) and deploy/ensure-swap-2g.sh.

# Stage 1: Install dependencies (including devDependencies for build)
FROM node:22-bookworm-slim AS deps

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1
ENV npm_config_fetch_retries=10
ENV npm_config_fetch_retry_mintimeout=20000
ENV npm_config_fetch_retry_maxtimeout=120000
ENV npm_config_fetch_timeout=600000
ENV npm_config_maxsockets=1
ENV npm_config_jobs=1
ENV npm_config_loglevel=warn
ENV npm_config_progress=false
ENV npm_config_audit=false
ENV npm_config_fund=false
ENV NODE_OPTIONS=--max-old-space-size=2048

COPY frontend/nextjs_app/package.json frontend/nextjs_app/package-lock.json* ./

# If npm ci fails with node-gyp / native compile errors, add: python3 make g++ to apt-get above.
# No `syntax=docker/dockerfile:1.4` / cache mounts — on 1 GB RAM hosts pulling the Dockerfile frontend image can OOM (137).
RUN set -eux; \
    if [ -f package-lock.json ]; then \
      npm ci --prefer-offline --no-audit --legacy-peer-deps --omit=optional; \
    else \
      npm install --prefer-offline --no-audit --legacy-peer-deps --omit=optional; \
    fi; \
    npm cache clean --force; \
    rm -rf /tmp/* 2>/dev/null || true

# Stage 2: Build the application (must use same libc family as deps — bookworm)
FROM node:22-bookworm-slim AS builder

WORKDIR /app

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
ENV NEXT_BUILD_LOW_MEMORY=1
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

# Stage 3: Production runner (bookworm-slim — matches standalone Node/glibc)
FROM node:22-bookworm-slim AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN groupadd --system --gid 1001 nodejs && \
    useradd --system --uid 1001 --gid nodejs nextjs

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
