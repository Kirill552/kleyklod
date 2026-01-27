import Link from "next/link";
import type { Metadata } from "next";
import {
  Sparkles,
  ArrowRight,
  FileSpreadsheet,
  QrCode,
  Printer,
  AlertTriangle,
  Zap,
  Clock,
  Star,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Статьи и инструкции | KleyKod",
  description:
    "Полезные статьи для селлеров Wildberries: как печатать этикетки, работать с Честным Знаком, избежать штрафов за маркировку.",
  keywords:
    "маркировка честный знак, этикетки wildberries, печать этикеток, штрафы за маркировку, datamatrix код",
};

interface Article {
  slug: string;
  title: string;
  description: string;
  icon: React.ElementType;
  readTime: string;
  category: string;
  available: boolean;
}

const articles: Article[] = [
  {
    slug: "kak-skachat-excel-s-barkodami-wildberries",
    title: "Как скачать Excel с баркодами из Wildberries",
    description:
      "Пошаговая инструкция по выгрузке файла с баркодами товаров из личного кабинета WB Partners.",
    icon: FileSpreadsheet,
    readTime: "3 мин",
    category: "Инструкция",
    available: true,
  },
  {
    slug: "kak-poluchit-kody-markirovki-chestny-znak",
    title: "Как получить коды маркировки Честный Знак",
    description:
      "Пошаговая инструкция: как скачать PDF с кодами маркировки из ЛК Честного Знака для одежды, обуви и других товаров.",
    icon: QrCode,
    readTime: "5 мин",
    category: "Инструкция",
    available: true,
  },
  {
    slug: "kakoy-printer-kupit-dlya-etiketok-58x40",
    title: "Какой принтер купить для этикеток 58x40",
    description:
      "Сравнение термопринтеров: Xprinter 365B, TSC TE200, Godex. Цены 2026, рекомендации по объёмам для WB и Ozon.",
    icon: Printer,
    readTime: "7 мин",
    category: "Обзор",
    available: true,
  },
  {
    slug: "pochemu-datamatrix-ne-skaniruetsya",
    title: "Почему DataMatrix не сканируется — решение",
    description:
      "Не читается честный знак? Разбираем причины: качество печати, размер кода, настройки сканера. Пошаговые решения.",
    icon: AlertTriangle,
    readTime: "4 мин",
    category: "Решение проблем",
    available: true,
  },
  {
    slug: "kak-nastroit-kleykod-za-5-minut",
    title: "Как настроить KleyKod за 5 минут",
    description:
      "Генератор этикеток для Wildberries и Ozon: пошаговая инструкция от загрузки файлов до печати.",
    icon: Zap,
    readTime: "5 мин",
    category: "Быстрый старт",
    available: true,
  },
  {
    slug: "wbcon-alternativa",
    title: "Альтернатива wbcon и wbarcode — сравнение генераторов",
    description:
      "Честное сравнение KleyKod vs wbcon vs wbarcode: цены, функции, проверка качества DataMatrix. Какой генератор этикеток выбрать?",
    icon: Star,
    readTime: "7 мин",
    category: "Сравнение",
    available: true,
  },
];

export default function ArticlesPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 border-b border-warm-gray-100">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-9 h-9 bg-emerald-600 rounded-xl flex items-center justify-center shadow-[2px_2px_0px_#047857]">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-lg text-warm-gray-800">
                KleyKod
              </span>
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
            >
              Попробовать бесплатно
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Breadcrumbs */}
      <div className="container mx-auto px-4 sm:px-6 py-4">
        <nav className="flex items-center gap-2 text-sm text-warm-gray-500">
          <Link href="/" className="hover:text-emerald-600 transition-colors">
            Главная
          </Link>
          <span>/</span>
          <span className="text-warm-gray-700">Статьи</span>
        </nav>
      </div>

      {/* Page Content */}
      <main className="container mx-auto px-4 sm:px-6 pb-24">
        <div className="max-w-4xl mx-auto">
          {/* Page Header */}
          <header className="mb-10">
            <h1 className="text-3xl sm:text-4xl font-bold text-warm-gray-900 mb-4">
              Статьи и инструкции
            </h1>
            <p className="text-lg text-warm-gray-600">
              Полезные материалы для селлеров Wildberries: как работать с
              этикетками, маркировкой Честный Знак и избежать штрафов.
            </p>
          </header>

          {/* Articles Grid */}
          <div className="grid gap-6">
            {articles.map((article) => {
              const Icon = article.icon;

              if (!article.available) {
                return (
                  <div
                    key={article.slug}
                    className="group relative bg-warm-gray-50 rounded-xl p-6 border border-warm-gray-200 opacity-60"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-12 h-12 bg-warm-gray-200 rounded-xl flex items-center justify-center">
                        <Icon className="w-6 h-6 text-warm-gray-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium text-warm-gray-400 uppercase tracking-wide">
                            {article.category}
                          </span>
                          <span className="text-xs text-warm-gray-400">•</span>
                          <span className="inline-flex items-center gap-1 text-xs text-warm-gray-400">
                            <Clock className="w-3 h-3" />
                            {article.readTime}
                          </span>
                        </div>
                        <h2 className="text-lg font-semibold text-warm-gray-500 mb-2">
                          {article.title}
                        </h2>
                        <p className="text-warm-gray-400 text-sm">
                          {article.description}
                        </p>
                        <span className="inline-block mt-3 text-xs font-medium text-warm-gray-400 bg-warm-gray-200 px-2 py-1 rounded">
                          Скоро
                        </span>
                      </div>
                    </div>
                  </div>
                );
              }

              return (
                <Link
                  key={article.slug}
                  href={`/articles/${article.slug}`}
                  className="group relative bg-white rounded-xl p-6 border border-warm-gray-200 hover:border-emerald-300 hover:shadow-[2px_2px_0px_#047857] transition-all"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-12 h-12 bg-emerald-100 group-hover:bg-emerald-200 rounded-xl flex items-center justify-center transition-colors">
                      <Icon className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-emerald-600 uppercase tracking-wide">
                          {article.category}
                        </span>
                        <span className="text-xs text-warm-gray-400">•</span>
                        <span className="inline-flex items-center gap-1 text-xs text-warm-gray-500">
                          <Clock className="w-3 h-3" />
                          {article.readTime}
                        </span>
                      </div>
                      <h2 className="text-lg font-semibold text-warm-gray-900 group-hover:text-emerald-700 mb-2 transition-colors">
                        {article.title}
                      </h2>
                      <p className="text-warm-gray-600 text-sm">
                        {article.description}
                      </p>
                    </div>
                    <ArrowRight className="flex-shrink-0 w-5 h-5 text-warm-gray-400 group-hover:text-emerald-600 group-hover:translate-x-1 transition-all" />
                  </div>
                </Link>
              );
            })}
          </div>

          {/* CTA */}
          <div className="mt-12 bg-emerald-50 border border-emerald-200 rounded-xl p-8 text-center">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-2">
              Не нашли ответ?
            </h2>
            <p className="text-warm-gray-600 mb-4">
              Напишите нам — ответим и добавим статью в базу знаний.
            </p>
            <Link
              href="https://t.me/kleykod_bot"
              target="_blank"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
            >
              Написать в Telegram
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 bg-emerald-700 text-emerald-200 py-8">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center border-2 border-emerald-500">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-white">KleyKod</span>
            </Link>
            <p className="text-sm text-emerald-300">
              © {new Date().getFullYear()} KleyKod. Все права защищены.
            </p>
            <div className="flex items-center gap-4 text-sm">
              <Link
                href="/terms"
                className="text-emerald-200 hover:text-white transition-colors"
              >
                Условия
              </Link>
              <Link
                href="/privacy"
                className="text-emerald-200 hover:text-white transition-colors"
              >
                Конфиденциальность
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
