// Конфигурация Sentry для Edge Runtime
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Процент трейсов для отправки (10%)
  tracesSampleRate: 0.1,

  // Отключаем отладку в production
  debug: false,

  // Окружение
  environment: process.env.NODE_ENV,

  // Не отправляем персональные данные
  sendDefaultPii: false,
});
