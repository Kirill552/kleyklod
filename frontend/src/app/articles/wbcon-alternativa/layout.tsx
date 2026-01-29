import { Metadata } from "next";

/**
 * Layout для статьи "Альтернатива wbcon" с SEO метаданными.
 * Вынесено из page.tsx потому что page использует "use client".
 */

const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";

export const metadata: Metadata = {
  title: "Альтернатива wbcon и wbarcode — бесплатный генератор этикеток для Вайлдберриз",
  description:
    "Честное сравнение генераторов этикеток для Wildberries: KleyKod vs wbcon vs wbarcode. Цены, функции, проверка качества DataMatrix. Какой выбрать в 2026?",
  keywords: [
    "wbcon альтернатива",
    "wbarcode аналог",
    "генератор этикеток для вайлдберриз бесплатно",
    "wbcon бесплатно",
    "сравнение wbcon kleykod",
    "этикетки wildberries бесплатно",
  ],
  alternates: {
    canonical: `${baseUrl}/articles/wbcon-alternativa`,
  },
  openGraph: {
    title: "Альтернатива wbcon — сравнение генераторов этикеток для WB",
    description:
      "KleyKod vs wbcon vs wbarcode: цены, функции, проверка качества. Какой генератор этикеток лучше?",
    url: `${baseUrl}/articles/wbcon-alternativa`,
    siteName: "KleyKod",
    locale: "ru_RU",
    type: "article",
    publishedTime: "2026-01-13T00:00:00.000Z",
    authors: ["KleyKod"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Альтернатива wbcon и wbarcode — сравнение 2026",
    description: "Какой генератор этикеток для Вайлдберриз выбрать? Честное сравнение.",
  },
};

// JSON-LD Article Schema
const articleJsonLd = {
  "@context": "https://schema.org",
  "@type": "Article",
  headline: "Альтернатива wbcon и wbarcode: бесплатный генератор этикеток для Вайлдберриз",
  description:
    "Честное сравнение генераторов этикеток для Wildberries: KleyKod vs wbcon vs wbarcode.",
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
  datePublished: "2026-01-13",
  dateModified: "2026-01-13",
  mainEntityOfPage: {
    "@type": "WebPage",
    "@id": `${baseUrl}/articles/wbcon-alternativa`,
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
      name: "Альтернатива wbcon",
      item: `${baseUrl}/articles/wbcon-alternativa`,
    },
  ],
};

export default function WbconAlternativaLayout({
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
