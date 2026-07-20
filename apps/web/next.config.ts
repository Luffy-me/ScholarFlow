import type { NextConfig } from "next";
import path from "path";

const API_ORIGIN = process.env.SCHOLARFLOW_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts", "framer-motion"],
  },
  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: `${API_ORIGIN}/:path*`,
      },
    ];
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "@repo": path.resolve(__dirname, "../.."),
    };
    return config;
  },
};

export default nextConfig;
