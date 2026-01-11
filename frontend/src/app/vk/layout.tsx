import type { Metadata, Viewport } from "next";

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
 * VK Bridge загружается из root layout (beforeInteractive работает только там).
 * VKWebAppInit вызывается в vk-auth-context.tsx при монтировании.
 */
export default function VKLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
