import { withSentryConfig } from "@sentry/nextjs";
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

// Оборачиваем конфиг в Sentry только если есть DSN
const sentryEnabled = !!process.env.SENTRY_DSN || !!process.env.NEXT_PUBLIC_SENTRY_DSN;

export default sentryEnabled
  ? withSentryConfig(nextConfig, {
      // Отключаем source maps в production для безопасности
      hideSourceMaps: true,

      // Отключаем телеметрию Sentry
      telemetry: false,

      // Не расширять серверный bundle лишними зависимостями
      disableLogger: true,
    })
  : nextConfig;
