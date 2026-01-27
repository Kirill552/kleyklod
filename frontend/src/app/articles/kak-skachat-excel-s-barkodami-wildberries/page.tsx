import Image from "next/image";
import Link from "next/link";
import type { Metadata } from "next";
import {
  Sparkles,
  Download,
  FileSpreadsheet,
  CheckCircle2,
  ArrowRight,
  Clock,
  BookOpen,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Как скачать Excel с баркодами из Wildberries | KleyKod",
  description:
    "Пошаговая инструкция: как выгрузить файл с баркодами товаров из личного кабинета Wildberries для печати этикеток с Честным Знаком.",
  keywords:
    "баркод товара вб, штрихкод wildberries, выгрузить товары wildberries, скачать баркоды wildberries, excel wildberries",
  openGraph: {
    title: "Как скачать Excel с баркодами из Wildberries",
    description:
      "Пошаговая инструкция по выгрузке баркодов из ЛК Wildberries для печати этикеток",
    type: "article",
    locale: "ru_RU",
  },
};

export default function ArticlePage() {
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
          <Link
            href="/articles"
            className="hover:text-emerald-600 transition-colors"
          >
            Статьи
          </Link>
          <span>/</span>
          <span className="text-warm-gray-700">Баркоды Wildberries</span>
        </nav>
      </div>

      {/* Article Content */}
      <article className="container mx-auto px-4 sm:px-6 pb-24">
        <div className="max-w-3xl mx-auto">
          {/* Article Header */}
          <header className="mb-10">
            <div className="flex items-center gap-3 mb-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                <FileSpreadsheet className="w-4 h-4" />
                Инструкция
              </span>
              <span className="inline-flex items-center gap-1.5 text-warm-gray-500 text-sm">
                <Clock className="w-4 h-4" />3 мин чтения
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold text-warm-gray-900 mb-4 leading-tight">
              Как скачать Excel с баркодами из Wildberries
            </h1>

            <p className="text-lg text-warm-gray-600 leading-relaxed">
              Пошаговая инструкция по выгрузке файла с{" "}
              <strong>баркодами товаров</strong> из личного кабинета WB Partners.
              Этот файл нужен для создания этикеток с{" "}
              <strong>маркировкой Честный Знак</strong>.
            </p>
          </header>

          {/* Quick Summary */}
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl p-6 mb-10">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-emerald-800 mb-3">
              <BookOpen className="w-5 h-5" />
              Коротко
            </h2>
            <ol className="space-y-2 text-emerald-700">
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-emerald-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  1
                </span>
                <span>
                  Откройте <strong>Товары и цены → Карточки товаров</strong>
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-emerald-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  2
                </span>
                <span>Выберите нужные товары галочками</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-emerald-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  3
                </span>
                <span>
                  Нажмите <strong>Редактировать → Excel → Сохранить</strong>
                </span>
              </li>
            </ol>
          </div>

          {/* Step 1 */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-4 flex items-center gap-3">
              <span className="flex-shrink-0 w-8 h-8 bg-emerald-600 text-white rounded-lg flex items-center justify-center text-lg font-bold">
                1
              </span>
              Откройте раздел «Карточки товаров»
            </h2>

            <p className="text-warm-gray-600 mb-4 leading-relaxed">
              Войдите в личный кабинет{" "}
              <a
                href="https://seller.wildberries.ru"
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-600 hover:underline font-medium"
              >
                WB Partners
              </a>{" "}
              и перейдите в раздел <strong>«Товары и цены»</strong> →{" "}
              <strong>«Карточки товаров»</strong>. Здесь отображается список
              всех ваших товаров с <strong>баркодами</strong> (штрихкодами).
            </p>

            <p className="text-warm-gray-600 mb-6 leading-relaxed">
              Выберите товары, для которых нужно скачать баркоды — поставьте
              галочки слева. Можно выбрать все товары или только часть.
            </p>

            <figure className="mb-4">
              <div className="relative rounded-xl overflow-hidden border border-warm-gray-200 shadow-[2px_2px_0px_#E7E5E4]">
                <Image
                  src="/articles/wildberries-excel/step-1-kartoochki.webp"
                  alt="Выбор товаров в разделе Карточки товаров Wildberries"
                  width={1200}
                  height={600}
                  className="w-full h-auto"
                  priority
                />
              </div>
              <figcaption className="text-sm text-warm-gray-500 mt-3 text-center">
                Выберите товары галочками и нажмите «Редактировать»
              </figcaption>
            </figure>

            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
              <span className="text-amber-500 text-xl">💡</span>
              <p className="text-amber-800 text-sm">
                <strong>Совет:</strong> После выбора товаров внизу появится
                панель с кнопками. Нажмите <strong>«Редактировать»</strong> для
                перехода к массовому редактированию.
              </p>
            </div>
          </section>

          {/* Step 2 */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-4 flex items-center gap-3">
              <span className="flex-shrink-0 w-8 h-8 bg-emerald-600 text-white rounded-lg flex items-center justify-center text-lg font-bold">
                2
              </span>
              Выгрузите данные в Excel
            </h2>

            <p className="text-warm-gray-600 mb-4 leading-relaxed">
              На странице массового редактирования найдите кнопку{" "}
              <strong>«Excel»</strong> в правом верхнем углу. Нажмите на неё и
              выберите <strong>«Сохранить»</strong>. Файл начнёт загружаться.
            </p>

            <figure className="mb-4">
              <div className="relative rounded-xl overflow-hidden border border-warm-gray-200 shadow-[2px_2px_0px_#E7E5E4]">
                <Image
                  src="/articles/wildberries-excel/step-2-vygruzit.webp"
                  alt="Кнопка Excel и Сохранить в массовом редактировании Wildberries"
                  width={1200}
                  height={400}
                  className="w-full h-auto"
                />
              </div>
              <figcaption className="text-sm text-warm-gray-500 mt-3 text-center">
                Нажмите «Excel» → «Сохранить» для выгрузки файла
              </figcaption>
            </figure>
          </section>

          {/* Step 3 */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-4 flex items-center gap-3">
              <span className="flex-shrink-0 w-8 h-8 bg-emerald-600 text-white rounded-lg flex items-center justify-center text-lg font-bold">
                3
              </span>
              Проверьте скачанный файл
            </h2>

            <p className="text-warm-gray-600 mb-4 leading-relaxed">
              Откройте скачанный <strong>.xlsx файл</strong>. Он содержит все
              данные о товарах, включая колонку{" "}
              <strong>«Штрихкод товара»</strong> (баркод) — именно она нужна для
              создания этикеток.
            </p>

            <figure className="mb-4">
              <div className="relative rounded-xl overflow-hidden border border-warm-gray-200 shadow-[2px_2px_0px_#E7E5E4]">
                <Image
                  src="/articles/wildberries-excel/excel-example.webp"
                  alt="Пример Excel файла с баркодами товаров Wildberries"
                  width={1200}
                  height={400}
                  className="w-full h-auto"
                />
              </div>
              <figcaption className="text-sm text-warm-gray-500 mt-3 text-center">
                Пример выгруженного Excel-файла с баркодами
              </figcaption>
            </figure>

            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
              <h3 className="font-semibold text-emerald-800 mb-2 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5" />
                Что содержит файл:
              </h3>
              <ul className="text-emerald-700 text-sm space-y-1">
                <li>
                  • <strong>Штрихкод товара</strong> — баркод для этикетки
                </li>
                <li>
                  • <strong>Наименование</strong> — название товара
                </li>
                <li>
                  • <strong>Артикул продавца</strong> — ваш внутренний артикул
                </li>
                <li>
                  • <strong>Размер, цвет</strong> — характеристики товара
                </li>
              </ul>
            </div>
          </section>

          {/* CTA Section */}
          <section className="bg-emerald-700 rounded-xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-3">
              Готовы создать этикетки?
            </h2>
            <p className="text-emerald-100 mb-6 max-w-lg mx-auto">
              Загрузите этот Excel-файл в KleyKod вместе с кодами{" "}
              <strong>Честного Знака</strong> — получите готовые этикетки для
              печати за 5 секунд.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-emerald-700 rounded-xl font-semibold hover:bg-emerald-50 transition-colors shadow-[2px_2px_0px_#E7E5E4]"
              >
                <Download className="w-5 h-5" />
                Создать этикетки бесплатно
              </Link>
              <Link
                href="/#how-it-works"
                className="inline-flex items-center gap-2 px-6 py-3 text-emerald-100 hover:text-white transition-colors"
              >
                Как это работает
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <p className="text-emerald-200 text-sm mt-4">
              50 этикеток в месяц — бесплатно, без регистрации карты
            </p>
          </section>

          {/* Related Info */}
          <section className="mt-12 pt-8 border-t border-warm-gray-200">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-4">
              Что дальше?
            </h2>

            <div className="grid sm:grid-cols-2 gap-4">
              <Link
                href="/#how-it-works"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Как работает KleyKod →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Объединение этикеток WB и Честного Знака в одну наклейку
                </p>
              </Link>

              <Link
                href="/#faq"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Частые вопросы →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Размеры этикеток, требования ЧЗ, настройка принтера
                </p>
              </Link>
            </div>
          </section>
        </div>
      </article>

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
