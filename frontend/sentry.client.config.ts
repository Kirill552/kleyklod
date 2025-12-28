/**
 * Конфигурация Sentry/GlitchTip для клиентской части.
 *
 * Этот файл инициализирует мониторинг ошибок в браузере.
 */

import * as Sentry from "@sentry/nextjs";

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,

    // Окружение
    environment: process.env.NODE_ENV,

    // Отправлять 10% транзакций для performance мониторинга
    tracesSampleRate: 0.1,

    // Replay для воспроизведения сессий (опционально)
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0.1,

    // Не отправлять персональные данные
    sendDefaultPii: false,

    // Отключаем в dev режиме
    enabled: process.env.NODE_ENV === "production",
  });
}
