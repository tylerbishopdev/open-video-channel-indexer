/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'open.video',
      },
    ],
  },
}

module.exports = nextConfig
