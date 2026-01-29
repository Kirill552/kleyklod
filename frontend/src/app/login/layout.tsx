import { Metadata } from "next";

/**
 * Layout для страницы входа с SEO метаданными.
 * Вынесено из page.tsx потому что page использует "use client".
 */

const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://kleykod.ru";

export const metadata: Metadata = {
  title: "Вход — KleyKod | Генератор этикеток для Вайлдберриз",
  description:
    "Войдите в личный кабинет KleyKod через Telegram или VK. 50 бесплатных этикеток для Wildberries каждый месяц. Без пароля, безопасно.",
  keywords: [
    "вход kleykod",
    "личный кабинет генератор этикеток",
    "войти через telegram",
    "генератор этикеток wildberries вход",
  ],
  alternates: {
    canonical: `${baseUrl}/login`,
  },
  openGraph: {
    title: "Вход в KleyKod — генератор этикеток для WB",
    description: "Войдите через Telegram или VK. 50 бесплатных этикеток в месяц.",
    url: `${baseUrl}/login`,
    siteName: "KleyKod",
    locale: "ru_RU",
    type: "website",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
