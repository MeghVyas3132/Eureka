/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    // react-konva pulls in `konva/lib/index-node.js` for SSR, which requires the
    // optional `canvas` package. We render Konva client-only via `next/dynamic`,
    // so mark `canvas` as external to keep it out of the bundle.
    config.externals = [...(config.externals || []), { canvas: "commonjs canvas" }];
    return config;
  },
};

module.exports = nextConfig;
