import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import "./globals.css";

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
      <body className={`${nunito.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
