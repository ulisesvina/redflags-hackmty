import type { NextConfig } from "next";

const backendUrl = process.env.REDFLAGS_BACKEND_URL ?? "http://localhost:8001";

const nextConfig: NextConfig = {
  agentRules: false,
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/redflags/:path*", destination: `${backendUrl}/:path*` }];
  },
};

export default nextConfig;
