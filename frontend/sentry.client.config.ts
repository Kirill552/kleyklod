// Конфигурация Sentry для клиентской части (браузер)
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Процент трейсов для отправки (10%)
  tracesSampleRate: 0.1,

  // Записываем 10% сессий
  replaysSessionSampleRate: 0.1,

  // Записываем 100% сессий с ошибками
  replaysOnErrorSampleRate: 1.0,

  // Отключаем отладку в production
  debug: false,

  // Окружение
  environment: process.env.NODE_ENV,

  // Не отправляем персональные данные
  sendDefaultPii: false,

  // Интеграции
  integrations: [Sentry.replayIntegration()],
});
