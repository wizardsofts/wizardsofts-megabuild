/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',

  // Turbopack configuration (Next.js 16+ default)
  // Empty config silences the webpack config warning
  turbopack: {},

  // Transpile local packages from monorepo
  transpilePackages: ['@wizwebui/core', '@wizardsofts/wizchart-interactive'],

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

  // Webpack config (used during production build with --webpack flag)
  webpack: (config) => {
    config.resolve.symlinks = true;
    return config;
  },
};

module.exports = nextConfig;
