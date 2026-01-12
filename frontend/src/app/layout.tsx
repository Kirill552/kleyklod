import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import Script from "next/script";
import { AuthProvider } from "@/contexts/auth-context";
import "./globals.css";

/**
 * Root Layout для KleyKod.
 *
 * VK Bridge загружается через npm пакет в vk-bridge.ts (рекомендация VK).
 */

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700", "800"],
});

const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";

export const metadata: Metadata = {
  metadataBase: new URL(baseUrl),
  title: {
    default: "Генератор этикеток WB + Честный Знак | Печать 58x40 бесплатно | KleyKod",
    template: "%s | KleyKod",
  },
  description: "Объедините штрихкод Wildberries и DataMatrix Честного Знака на одной этикетке 58x40. Решение проблемы 2 стикеров на товаре. 50 этикеток в день бесплатно. Альтернатива wbarcode и wbcon.",
  keywords: [
    "генератор этикеток для вайлдберриз",
    "этикетки честный знак",
    "печать этикеток 58 40",
    "2 стикера на товаре",
    "wbarcode альтернатива",
    "wbcon",
    "маркировка fbs",
    "datamatrix код",
    "этикетки для маркетплейсов",
    "штрихкод wildberries",
    "честный знак маркировка",
    "этикетки для wb",
  ],
  authors: [{ name: "KleyKod", url: baseUrl }],
  creator: "KleyKod",
  publisher: "KleyKod",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: [
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: "/apple-icon.png",
    other: [
      { rel: "android-chrome", url: "/android-chrome-192x192.png", sizes: "192x192" },
    ],
  },
  manifest: "/manifest.json",
  openGraph: {
    title: "Генератор этикеток WB + Честный Знак | KleyKod",
    description: "Объедините 2 стикера в один. Печать этикеток 58x40 для Wildberries с кодом Честного Знака. Бесплатно 50 шт/день.",
    type: "website",
    locale: "ru_RU",
    url: baseUrl,
    siteName: "KleyKod",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "KleyKod — объединение кодов для Wildberries. Два кода в один клейкод.",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Генератор этикеток WB + Честный Знак | KleyKod",
    description: "Объедините 2 стикера в один. 50 этикеток в день бесплатно.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: baseUrl,
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION,
    yandex: process.env.NEXT_PUBLIC_YANDEX_VERIFICATION,
  },
  category: "technology",
};

// JSON-LD структурированные данные для поисковых систем
const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": `${baseUrl}/#website`,
      url: baseUrl,
      name: "KleyKod",
      description: "Генератор этикеток для Wildberries с кодом Честного Знака",
      publisher: { "@id": `${baseUrl}/#organization` },
      potentialAction: {
        "@type": "SearchAction",
        target: `${baseUrl}/articles?q={search_term_string}`,
        "query-input": "required name=search_term_string",
      },
      inLanguage: "ru-RU",
    },
    {
      "@type": "Organization",
      "@id": `${baseUrl}/#organization`,
      name: "KleyKod",
      url: baseUrl,
      logo: {
        "@type": "ImageObject",
        url: `${baseUrl}/android-chrome-512x512.png`,
        width: 512,
        height: 512,
      },
      sameAs: [
        "https://t.me/kleykod_bot",
        "https://vk.com/app51920328",
      ],
      contactPoint: {
        "@type": "ContactPoint",
        contactType: "customer support",
        availableLanguage: "Russian",
      },
    },
    {
      "@type": "SoftwareApplication",
      name: "KleyKod",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "RUB",
        description: "50 этикеток в день бесплатно",
      },
      aggregateRating: {
        "@type": "AggregateRating",
        ratingValue: "4.8",
        ratingCount: "150",
        bestRating: "5",
        worstRating: "1",
      },
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <head>
        {/* JSON-LD структурированные данные */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className={`${nunito.variable} font-sans antialiased`}>
        <AuthProvider>{children}</AuthProvider>
        {process.env.NEXT_PUBLIC_METRIKA_ID && (
          <Script id="yandex-metrika" strategy="afterInteractive">
            {`
              (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
              m[i].l=1*new Date();
              for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
              k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
              (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
              ym(${process.env.NEXT_PUBLIC_METRIKA_ID}, "init", {
                clickmap:true,
                trackLinks:true,
                accurateTrackBounce:true,
                webvisor:true
              });
            `}
          </Script>
        )}
      </body>
    </html>
  );
}
