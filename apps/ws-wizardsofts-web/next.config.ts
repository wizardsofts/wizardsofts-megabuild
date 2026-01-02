import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Enable compression for better performance
  compress: true,
};

export default nextConfig;
