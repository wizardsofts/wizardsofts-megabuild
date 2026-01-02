/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',

  // API proxy: Routes /api/* requests to FastAPI backend
  // This avoids CORS issues during development
  async rewrites() {
    const backendPort = process.env.BACKEND_PORT || 5010;
    return [
      {
        source: "/api/v1/:path*",
        destination: `http://localhost:${backendPort}/api/v1/:path*`,
      },
      {
        source: "/backend/:path*",
        destination: `http://localhost:${backendPort}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
