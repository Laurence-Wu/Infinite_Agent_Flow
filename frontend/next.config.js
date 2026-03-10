/** @type {import('next').NextConfig} */
const FLASK_PORT = process.env.FLASK_PORT || '5000'

const nextConfig = {
  // Proxy /api/* to the Flask backend — no CORS headers needed
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `http://localhost:${FLASK_PORT}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
