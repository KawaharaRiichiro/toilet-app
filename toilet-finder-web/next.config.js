/** @type {import('next').NextConfig} */
const nextConfig = {
  // 既存の設定（Reactの厳格モード）
  reactStrictMode: false,
  
  // ★★★ 新規追加：FastAPIへのプロキシ設定（リライティング）★★★
  async rewrites() {
    return [
      {
        // localhost:3000/api/ に来たリクエストをすべて
        source: '/api/:path*',
        // localhost:8000/api/ に転送する
        destination: 'http://127.0.0.1:8000/api/:path*', 
      },
    ];
  },
  // ★★★ ここまで新規追加 ★★★
};

module.exports = nextConfig;