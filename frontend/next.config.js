/** @type {import('next').NextConfig} */
const FLASK_PORT = process.env.FLASK_PORT || '5000'

const nextConfig = {
  // Proxy /api/* to the Flask backend — no CORS headers needed
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `http://127.0.0.1:${FLASK_PORT}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
