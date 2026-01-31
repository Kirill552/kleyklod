import { MetadataRoute } from "next";
import { getArticles } from "@/lib/api";

/**
 * Динамическая генерация sitemap.xml для поисковых систем.
 *
 * Статьи загружаются из API — новые статьи автоматически попадают в sitemap.
 * Формат: https://www.sitemaps.org/protocol.html
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";
  const currentDate = new Date();

  // Статические страницы с разными приоритетами
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: currentDate,
      changeFrequency: "weekly",
      priority: 1.0, // Главная — максимальный приоритет
    },
    {
      url: `${baseUrl}/login`,
      lastModified: currentDate,
      changeFrequency: "monthly",
      priority: 0.9, // Страница входа — высокий приоритет (конверсия)
    },
    {
      url: `${baseUrl}/articles`,
      lastModified: currentDate,
      changeFrequency: "weekly",
      priority: 0.8, // Список статей — обновляется при добавлении
    },
    {
      url: `${baseUrl}/terms`,
      lastModified: new Date("2025-01-01"),
      changeFrequency: "yearly",
      priority: 0.3,
    },
    {
      url: `${baseUrl}/privacy`,
      lastModified: new Date("2025-01-01"),
      changeFrequency: "yearly",
      priority: 0.3,
    },
    {
      url: `${baseUrl}/faq`,
      lastModified: currentDate,
      changeFrequency: "monthly",
      priority: 0.8, // FAQ — высокий приоритет для SEO (rich snippets)
    },
    {
      url: `${baseUrl}/wb-labels`,
      lastModified: currentDate,
      changeFrequency: "weekly",
      priority: 0.9, // SEO-лендинг WB — высокий приоритет (конверсия)
    },
    {
      url: `${baseUrl}/chz-labels`,
      lastModified: currentDate,
      changeFrequency: "weekly",
      priority: 0.9, // SEO-лендинг ЧЗ — высокий приоритет (конверсия)
    },
  ];

  // Статьи — загружаем динамически из API
  const articles = await getArticles();

  const articlePages: MetadataRoute.Sitemap = articles.map((article) => ({
    url: `${baseUrl}/articles/${article.slug}`,
    lastModified: new Date(article.updated_at),
    changeFrequency: "monthly",
    priority: 0.7, // Статьи — хороший приоритет для SEO-трафика
  }));

  return [...staticPages, ...articlePages];
}
