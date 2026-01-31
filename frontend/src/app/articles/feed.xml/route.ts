import { getArticles } from '@/lib/api';

/**
 * RSS 2.0 лента для статей KleyKod.
 *
 * URL: /articles/feed.xml
 * Используется для: Яндекс.Дзен, RSS-ридеры, Telegram-боты.
 */
export async function GET() {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://kleykod.ru';
  const articles = await getArticles();

  const rssItems = articles
    .map((article) => {
      const pubDate = new Date(article.created_at).toUTCString();
      return `
    <item>
      <title><![CDATA[${article.title}]]></title>
      <link>${baseUrl}/articles/${article.slug}</link>
      <description><![CDATA[${article.description}]]></description>
      <pubDate>${pubDate}</pubDate>
      <guid isPermaLink="true">${baseUrl}/articles/${article.slug}</guid>
      <category>${article.category}</category>
    </item>`;
    })
    .join('');

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>KleyKod — Статьи для селлеров Wildberries</title>
    <link>${baseUrl}/articles</link>
    <description>Полезные статьи о маркировке, этикетках и работе с Честным Знаком для селлеров Wildberries</description>
    <language>ru-ru</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${baseUrl}/articles/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>${baseUrl}/logo.png</url>
      <title>KleyKod</title>
      <link>${baseUrl}</link>
    </image>${rssItems}
  </channel>
</rss>`;

  return new Response(rss, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}
