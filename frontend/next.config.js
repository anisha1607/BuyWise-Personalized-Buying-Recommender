const os = require("os");
const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use default .next directory
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
