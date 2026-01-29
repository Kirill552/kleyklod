/**
 * Layout для статьи "Как скачать Excel с баркодами из Wildberries".
 * Добавляет Article Schema и BreadcrumbList JSON-LD для SEO.
 */

const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";
const slug = "kak-skachat-excel-s-barkodami-wildberries";

// JSON-LD Article Schema
const articleJsonLd = {
  "@context": "https://schema.org",
  "@type": "Article",
  headline: "Как скачать Excel с баркодами из Wildberries",
  description:
    "Пошаговая инструкция: как выгрузить файл с баркодами товаров из личного кабинета Wildberries для печати этикеток с Честным Знаком.",
  image: `${baseUrl}/articles/wildberries-excel/step-1-kartoochki.webp`,
  author: {
    "@type": "Organization",
    name: "KleyKod",
    url: baseUrl,
  },
  publisher: {
    "@type": "Organization",
    name: "KleyKod",
    logo: {
      "@type": "ImageObject",
      url: `${baseUrl}/android-chrome-512x512.png`,
    },
  },
  datePublished: "2025-12-28",
  dateModified: "2025-12-28",
  mainEntityOfPage: {
    "@type": "WebPage",
    "@id": `${baseUrl}/articles/${slug}`,
  },
};

// JSON-LD BreadcrumbList Schema
const breadcrumbJsonLd = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    {
      "@type": "ListItem",
      position: 1,
      name: "Главная",
      item: baseUrl,
    },
    {
      "@type": "ListItem",
      position: 2,
      name: "Статьи",
      item: `${baseUrl}/articles`,
    },
    {
      "@type": "ListItem",
      position: 3,
      name: "Баркоды Wildberries",
      item: `${baseUrl}/articles/${slug}`,
    },
  ],
};

export default function ArticleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      {children}
    </>
  );
}
