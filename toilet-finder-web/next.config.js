/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  
  // ★ここを変更: 日本語化プラグインを追加
  transpilePackages: ['react-map-gl', 'mapbox-gl', '@mapbox/mapbox-gl-language'],

  webpack: (config) => {
    config.cache = false;
    return config;
  },

  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*', 
      },
    ];
  },
};

module.exports = nextConfig;