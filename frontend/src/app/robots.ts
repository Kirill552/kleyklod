import { MetadataRoute } from "next";

/**
 * Генерация robots.txt для поисковых систем.
 *
 * Настроено для максимальной индексации публичных страниц
 * и блокировки приватных разделов.
 */
export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";

  return {
    rules: [
      {
        // Правила для всех поисковиков
        userAgent: "*",
        allow: [
          "/",
          "/articles",
          "/articles/",
          "/login",
          "/terms",
          "/privacy",
          "/faq",
          "/wb-labels",
          "/chz-labels",
        ],
        disallow: [
          "/app/",        // Личный кабинет
          "/vk/",         // VK Mini App (отдельная индексация)
          "/api/",        // API endpoints
          "/_next/",      // Next.js системные файлы
          "/examples/",   // Примеры файлов (не для индексации)
        ],
        crawlDelay: 1,    // 1 секунда между запросами (вежливость к серверу)
      },
      {
        // Яндекс — более частое сканирование для приоритетного рынка
        userAgent: "Yandex",
        allow: [
          "/",
          "/articles",
          "/articles/",
          "/login",
          "/terms",
          "/privacy",
          "/faq",
          "/wb-labels",
          "/chz-labels",
        ],
        disallow: [
          "/app/",
          "/vk/",
          "/api/",
          "/_next/",
          "/examples/",
        ],
        crawlDelay: 0.5,  // Яндекс — приоритет, быстрее сканируем
      },
      {
        // Google — стандартные правила
        userAgent: "Googlebot",
        allow: [
          "/",
          "/articles",
          "/articles/",
          "/login",
          "/terms",
          "/privacy",
          "/faq",
          "/wb-labels",
          "/chz-labels",
        ],
        disallow: [
          "/app/",
          "/vk/",
          "/api/",
          "/_next/",
          "/examples/",
        ],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
