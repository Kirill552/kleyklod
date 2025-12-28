/**
 * Конфигурация Sentry/GlitchTip для Edge Runtime.
 *
 * Используется для middleware и Edge API routes.
 */

import * as Sentry from "@sentry/nextjs";

const SENTRY_DSN = process.env.SENTRY_DSN;

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,

    // Окружение
    environment: process.env.NODE_ENV,

    // Отправлять 10% транзакций
    tracesSampleRate: 0.1,

    // Не отправлять персональные данные
    sendDefaultPii: false,

    // Отключаем в dev режиме
    enabled: process.env.NODE_ENV === "production",
  });
}
