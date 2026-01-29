/**
 * Layout для статьи "Почему DataMatrix не сканируется — решение".
 * Добавляет Article Schema и BreadcrumbList JSON-LD для SEO.
 */

const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";
const slug = "pochemu-datamatrix-ne-skaniruetsya";

// JSON-LD Article Schema
const articleJsonLd = {
  "@context": "https://schema.org",
  "@type": "Article",
  headline: "Почему DataMatrix не сканируется — решение",
  description:
    "Не читается честный знак? Разбираем причины: качество печати, размер кода, настройки сканера. Пошаговые решения.",
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
  datePublished: "2025-12-30",
  dateModified: "2025-12-30",
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
      name: "DataMatrix не сканируется",
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
