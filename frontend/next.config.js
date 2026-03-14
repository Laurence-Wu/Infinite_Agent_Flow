/** @type {import('next').NextConfig} */
const FLASK_PORT = process.env.FLASK_PORT || '5000'

const nextConfig = {
  // Expose Flask port to the browser so SSE can connect directly,
  // bypassing the Next.js proxy which does not support long-lived streams.
  env: {
    NEXT_PUBLIC_FLASK_PORT: FLASK_PORT,
  },

  // Proxy /api/* to the Flask backend — no CORS headers needed.
  // SSE (/api/agent/stream) is intentionally excluded; the browser
  // connects to it directly on the Flask port to avoid ECONNRESET.
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
