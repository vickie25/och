/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  productionBrowserSourceMaps: false,
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    const django =
      process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8001';
    return [
      {
        source: '/api/profiling/:path*',
        destination: `${django}/api/v1/profiling/:path*`,
      },
      // Proxy Django API (Stream B institutional billing, etc.) — no Next route under /api/v1/
      {
        source: '/api/v1/:path*',
        destination: `${django}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

