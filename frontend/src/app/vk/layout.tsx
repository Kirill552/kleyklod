import type { Metadata, Viewport } from "next";
import Script from "next/script";

export const metadata: Metadata = {
  title: "KleyKod — VK Mini App",
  description: "Генератор этикеток WB + Честный Знак",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

/**
 * Layout для VK Mini App.
 *
 * КРИТИЧНО: VKWebAppInit должен вызываться как можно раньше,
 * иначе VK покажет ошибку "Приложение не инициализировано".
 */
export default function VKLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/* Загружаем VK Bridge и вызываем init ДО React hydration */}
      <Script
        id="vk-bridge-init"
        strategy="beforeInteractive"
        dangerouslySetInnerHTML={{
          __html: `
            (function() {
              // Создаём promise для отслеживания инициализации
              window.__vkBridgeReady = new Promise(function(resolve, reject) {
                var script = document.createElement('script');
                script.src = 'https://unpkg.com/@vkontakte/vk-bridge@2.15.11/dist/browser.min.js';
                script.onload = function() {
                  if (window.vkBridge) {
                    window.vkBridge.send('VKWebAppInit')
                      .then(function() {
                        console.log('[VK] Bridge initialized');
                        resolve();
                      })
                      .catch(function(err) {
                        console.error('[VK] Init error:', err);
                        reject(err);
                      });
                  } else {
                    reject(new Error('vkBridge not found'));
                  }
                };
                script.onerror = function() {
                  reject(new Error('Failed to load vk-bridge'));
                };
                document.head.appendChild(script);
              });
            })();
          `,
        }}
      />
      {children}
    </>
  );
}
