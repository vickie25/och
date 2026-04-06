const { PHASE_DEVELOPMENT_SERVER } = require('next/constants');
const path = require('path');

/**
 * CSP connect-src tokens: env-driven API origins (http + https), dev localhost, prod defaults,
 * paired ws/wss for realtime, and Google OAuth endpoints. Same-origin `/api/*` BFF calls use 'self'
 * and never hit browser CORS when the client uses relative URLs (see googleOAuthClient).
 */
function buildConnectSrcExtra() {
  const origins = new Set();
  const add = (s) => {
    if (!s || typeof s !== 'string') return;
    const t = s.trim();
    if (!t) return;
    try {
      const u = new URL(t.includes('://') ? t : `https://${t}`);
      origins.add(u.origin);
      if (u.protocol === 'https:') origins.add(`wss://${u.host}`);
      if (u.protocol === 'http:') origins.add(`ws://${u.host}`);
    } catch {
      /* ignore */
    }
  };

  [
    process.env.NEXT_PUBLIC_DJANGO_API_URL,
    process.env.NEXT_PUBLIC_FASTAPI_API_URL,
    process.env.NEXT_PUBLIC_APP_URL,
    process.env.NEXT_PUBLIC_WS_URL,
  ].forEach(add);

  [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:8001',
    'http://127.0.0.1:8001',
    'ws://localhost:8000',
    'ws://127.0.0.1:8000',
    'ws://localhost:8001',
    'ws://127.0.0.1:8001',
    'https://cybochengine.africa',
    'https://www.cybochengine.africa',
    'wss://cybochengine.africa',
    'wss://www.cybochengine.africa',
    'https://accounts.google.com',
    'https://www.googleapis.com',
  ].forEach(add);

  return Array.from(origins).join(' ');
}

/** @type {(phase: string) => import('next').NextConfig} */
module.exports = (phase) => {
  const djangoBase =
    process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
  const normalizedDjangoBase = djangoBase
    .replace(/\/$/, '')
    .replace(/\/api\/v1$/, '')
    .replace(/\/api$/, '');

  /** Lower parallelism during `next build` on small VPS / Docker builders (see Dockerfile NEXT_BUILD_LOW_MEMORY). */
  const lowResourceBuild = process.env.NEXT_BUILD_LOW_MEMORY === '1';

  /** @type {import('next').NextConfig} */
  const nextConfig = {
    output: 'standalone',
    outputFileTracingRoot: path.join(__dirname, '../..'),
    productionBrowserSourceMaps: false,
    ...(lowResourceBuild
      ? {
          experimental: {
            cpus: 1,
            workerThreads: false,
          },
        }
      : {}),
    typescript: {
      ignoreBuildErrors: true,
    },
    // Security configurations
    compiler: {
      removeConsole: {
        exclude: ['error'], // Keep error logs for production debugging
      },
    },
    // Additional security headers
    async headers() {
      return [
        {
          source: '/(.*)',
          headers: [
            {
              key: 'X-Frame-Options',
              value: 'DENY',
            },
            {
              key: 'X-Content-Type-Options',
              value: 'nosniff',
            },
            {
              key: 'Referrer-Policy',
              value: 'strict-origin-when-cross-origin',
            },
            {
              key: 'Permissions-Policy',
              value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
            },
            {
              key: 'Content-Security-Policy',
              value: [
                "default-src 'self'",
                "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://js.stripe.com https://checkout.stripe.com",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                // MUI / some icon fonts load embedded WOFF as data: URIs
                "font-src 'self' data: https://fonts.gstatic.com",
                "img-src 'self' data: https: blob:",
                `connect-src 'self' ${buildConnectSrcExtra()} https://js.stripe.com https://checkout.stripe.com`,
                "frame-src 'self' https://js.stripe.com https://checkout.stripe.com",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
              ].join('; '),
            },
          ],
        },
      ];
    },
    // App Router handlers under app/api/** take precedence; these proxy only unmatched paths.
    async rewrites() {
      return [
        {
          source: '/api/profiling/:path*',
          destination: `${normalizedDjangoBase}/api/v1/profiling/:path*`,
        },
        {
          source: '/api/v1/:path*',
          destination: `${normalizedDjangoBase}/api/v1/:path*`,
        },
      ];
    },
  };

  // Must match outputFileTracingRoot (Next 16). Use webpack dev (`npm run dev`) if Turbopack is slow here.
  if (phase === PHASE_DEVELOPMENT_SERVER) {
    nextConfig.turbopack = { root: path.join(__dirname, '../..') };
  }

  return nextConfig;
};
