/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',

  // Turbopack configuration (Next.js 16+ default)
  // Empty config silences the webpack config warning
  turbopack: {},

  // Transpile local packages from monorepo
  // Note: Must include all wizchart dependencies since they're all symlinked
  transpilePackages: [
    '@wizwebui/core',
    '@wizardsofts/wizchart-interactive',
    '@wizardsofts/wizchart-core',
    '@wizardsofts/wizchart-coordinates',
  ],

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
    config.resolve.alias = {
      ...config.resolve.alias,
      '@wizwebui/core': require.resolve('../../../wizardsofts/wizwebui/packages/core/dist'),
      '@wizardsofts/wizchart-core$': require.resolve('../../../wizardsofts/wizchart/packages/core/lib/index.js'),
      '@wizardsofts/wizchart-core/': require.resolve('../../../wizardsofts/wizchart/packages/core/lib/'),
      '@wizardsofts/wizchart-coordinates$': require.resolve('../../../wizardsofts/wizchart/packages/coordinates/lib/index.js'),
      '@wizardsofts/wizchart-coordinates/': require.resolve('../../../wizardsofts/wizchart/packages/coordinates/lib/'),
      '@wizardsofts/wizchart-interactive$': require.resolve('../../../wizardsofts/wizchart/packages/interactive/lib/index.js'),
      '@wizardsofts/wizchart-interactive/': require.resolve('../../../wizardsofts/wizchart/packages/interactive/lib/'),
    };
    return config;
  },
};

module.exports = nextConfig;
