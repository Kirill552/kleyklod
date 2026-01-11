import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import Script from "next/script";
import { AuthProvider } from "@/contexts/auth-context";
import "./globals.css";

/**
 * Inline скрипт для загрузки VK Bridge через CDN.
 * КРИТИЧНО: должен быть в root layout с beforeInteractive,
 * т.к. beforeInteractive не работает в nested layouts (Next.js ограничение).
 *
 * Этот скрипт только загружает библиотеку и создаёт window.vkBridge.
 * VKWebAppInit вызывается отдельно в vk-auth-context.tsx.
 */
const vkBridgeScript = `
(function() {
  if (typeof window === 'undefined') return;

  // Promise для отслеживания загрузки VK Bridge
  window.__vkBridgeReady = new Promise(function(resolve, reject) {
    // Создаём скрипт для загрузки VK Bridge CDN
    var script = document.createElement('script');
    script.src = 'https://unpkg.com/@vkontakte/vk-bridge@2.15.11/dist/browser.min.js';
    script.async = false; // Синхронная загрузка для гарантии порядка

    script.onload = function() {
      if (window.vkBridge) {
        console.log('[VK Bridge] Loaded from CDN');
        resolve();
      } else {
        console.error('[VK Bridge] Script loaded but vkBridge not found');
        reject(new Error('vkBridge not found after script load'));
      }
    };

    script.onerror = function() {
      console.error('[VK Bridge] Failed to load from CDN');
      reject(new Error('Failed to load vk-bridge from CDN'));
    };

    // Добавляем в head для ранней загрузки
    document.head.appendChild(script);
  });
})();
`;

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Генератор этикеток WB + Честный Знак | Печать 58x40 бесплатно | KleyKod",
  description: "Объедините штрихкод Wildberries и DataMatrix Честного Знака на одной этикетке 58x40. Решение проблемы 2 стикеров на товаре. 50 этикеток в день бесплатно. Альтернатива wbarcode и wbcon.",
  keywords: "генератор этикеток для вайлдберриз, этикетки честный знак, печать этикеток 58 40, 2 стикера на товаре, wbarcode альтернатива, wbcon, маркировка fbs, datamatrix код, этикетки для маркетплейсов",
  authors: [{ name: "KleyKod" }],
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
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <head>
        {/* VK Bridge CDN - загружается рано для /vk страниц */}
        <Script
          id="vk-bridge-loader"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{ __html: vkBridgeScript }}
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
