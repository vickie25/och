const { PHASE_DEVELOPMENT_SERVER } = require('next/constants');
const path = require('path');

/** @type {(phase: string) => import('next').NextConfig} */
module.exports = (phase) => {
  const djangoBase =
    process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
  const normalizedDjangoBase = djangoBase
    .replace(/\/$/, '')
    .replace(/\/api\/v1$/, '')
    .replace(/\/api$/, '');

  /** @type {import('next').NextConfig} */
  const nextConfig = {
    output: 'standalone',
    outputFileTracingRoot: path.join(__dirname, '../..'),
    productionBrowserSourceMaps: false,
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
                "font-src 'self' https://fonts.gstatic.com",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' http://localhost:8000 http://localhost:8001 https://cybochengine.africa https://www.cybochengine.africa",
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
