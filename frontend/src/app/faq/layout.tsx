/**
 * Layout для страницы FAQ.
 * Добавляет BreadcrumbList JSON-LD для SEO.
 * FAQPage Schema уже добавлена в page.tsx.
 */

const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";

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
      name: "FAQ",
      item: `${baseUrl}/faq`,
    },
  ],
};

export default function FAQLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      {children}
    </>
  );
}
