/**
 * Layout для статьи "Как получить коды маркировки Честный Знак".
 * Добавляет Article Schema и BreadcrumbList JSON-LD для SEO.
 */

const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";
const slug = "kak-poluchit-kody-markirovki-chestny-znak";

// JSON-LD Article Schema
const articleJsonLd = {
  "@context": "https://schema.org",
  "@type": "Article",
  headline: "Как получить коды маркировки Честный Знак",
  description:
    "Пошаговая инструкция: как скачать PDF с кодами маркировки из ЛК Честного Знака для одежды, обуви и других товаров.",
  image: `${baseUrl}/articles/chestny-znak-kody/step-1.webp`,
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
      name: "Коды маркировки ЧЗ",
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
