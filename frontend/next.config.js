/**
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  output: 'export',  // Required for static Firebase hosting
  images: {
    unoptimized: true, // Needed for static export
  },
  distDir: 'out',
  trailingSlash: false,
};

module.exports = nextConfig;