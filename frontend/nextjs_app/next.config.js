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
