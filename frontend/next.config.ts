import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output для Docker
  output: "standalone",

  // Оптимизация изображений
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "kleykod.ru",
      },
    ],
  },

  // Переменные окружения для клиента
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://kleykod.ru/api",
  },
};

export default nextConfig;
