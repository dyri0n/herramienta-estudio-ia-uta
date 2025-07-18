/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  webpack: (config, { isServer }) => {
    // Configuración para PDF.js
    config.resolve.fallback = {
      ...config.resolve.fallback,
      canvas: false,
      fs: false,
      path: false,
      stream: false,
      zlib: false,
    };

    // Solo en cliente
    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        'pdfjs-dist': 'pdfjs-dist/legacy/build/pdf.min.js',
      };
    }

    // Regla para workers (opcional)
    config.module.rules.push({
      test: /\.worker\.min\.js$/,
      type: 'asset/resource',
    });

    return config;
  },
  experimental: {
    esmExternals: 'loose',
    serverComponentsExternalPackages: ['pdf-lib'], // Si usas pdf-lib
  },
};

export default nextConfig;