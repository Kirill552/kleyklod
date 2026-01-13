"use client";

import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  Clock,
  CheckCircle2,
  XCircle,
  Minus,
  Zap,
  Shield,
  Eye,
  DollarSign,
  Users,
  Star,
} from "lucide-react";

/**
 * SEO-статья: Альтернатива wbcon и wbarcode
 * Целевые запросы:
 * - wbcon альтернатива (1683)
 * - wbarcode аналог (1321)
 * - генератор этикеток для вайлдберриз бесплатно
 * - wbcon бесплатно
 */

interface ComparisonRow {
  feature: string;
  kleykod: { value: string; status: "best" | "yes" | "partial" | "no" };
  wbcon: { value: string; status: "best" | "yes" | "partial" | "no" };
  wbarcode: { value: string; status: "best" | "yes" | "partial" | "no" };
}

const comparisonData: ComparisonRow[] = [
  {
    feature: "Бесплатный тариф",
    kleykod: { value: "50 этикеток/день навсегда", status: "best" },
    wbcon: { value: "Ограниченный trial", status: "partial" },
    wbarcode: { value: "Нет информации", status: "no" },
  },
  {
    feature: "Цена PRO",
    kleykod: { value: "490 ₽/мес", status: "best" },
    wbcon: { value: "от 990 ₽/мес", status: "partial" },
    wbarcode: { value: "Скрыта", status: "no" },
  },
  {
    feature: "Проверка качества DataMatrix",
    kleykod: { value: "Автоматическая", status: "best" },
    wbcon: { value: "Нет", status: "no" },
    wbarcode: { value: "Нет", status: "no" },
  },
  {
    feature: "Объединение WB + ЧЗ",
    kleykod: { value: "Автоматически", status: "best" },
    wbcon: { value: "Да", status: "yes" },
    wbarcode: { value: "Да", status: "yes" },
  },
  {
    feature: "Telegram-бот",
    kleykod: { value: "@kleykod_bot", status: "yes" },
    wbcon: { value: "Нет", status: "no" },
    wbarcode: { value: "Нет", status: "no" },
  },
  {
    feature: "API для автоматизации",
    kleykod: { value: "REST API", status: "yes" },
    wbcon: { value: "Есть", status: "yes" },
    wbarcode: { value: "Есть", status: "yes" },
  },
  {
    feature: "Прозрачность цен",
    kleykod: { value: "100%", status: "best" },
    wbcon: { value: "Средняя", status: "partial" },
    wbarcode: { value: "Низкая", status: "no" },
  },
  {
    feature: "Скорость генерации",
    kleykod: { value: "Мгновенно", status: "best" },
    wbcon: { value: "Быстро", status: "yes" },
    wbarcode: { value: "1-2 минуты", status: "partial" },
  },
];

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "best":
      return (
        <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
          <CheckCircle2 className="w-3 h-3 text-white" />
        </div>
      );
    case "yes":
      return (
        <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
        </div>
      );
    case "partial":
      return (
        <div className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center">
          <Minus className="w-3 h-3 text-amber-600" />
        </div>
      );
    case "no":
      return (
        <div className="w-5 h-5 rounded-full bg-red-100 flex items-center justify-center">
          <XCircle className="w-3 h-3 text-red-500" />
        </div>
      );
    default:
      return null;
  }
}

export default function WbconAlternativaPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-warm-gray-50 to-white">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-warm-gray-100">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-9 h-9 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
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
          <span className="text-warm-gray-700">Альтернатива wbcon</span>
        </nav>
      </div>

      {/* Article Content */}
      <article className="container mx-auto px-4 sm:px-6 pb-16">
        <div className="max-w-4xl mx-auto">
          {/* Article Header */}
          <header className="mb-10">
            <div className="flex items-center gap-3 mb-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-violet-100 text-violet-700 rounded-full text-sm font-medium">
                <Star className="w-4 h-4" />
                Сравнение
              </span>
              <span className="inline-flex items-center gap-1.5 text-warm-gray-500 text-sm">
                <Clock className="w-4 h-4" />7 мин чтения
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold text-warm-gray-900 mb-4 leading-tight">
              Альтернатива wbcon и wbarcode: бесплатный генератор этикеток для Вайлдберриз
            </h1>

            <p className="text-lg text-warm-gray-600 leading-relaxed">
              Честное сравнение <strong>генераторов этикеток для Wildberries</strong>:
              KleyKod vs wbcon vs wbarcode. Цены, функции, плюсы и минусы каждого сервиса.
              Узнайте, какой <strong>генератор наклеек для вб</strong> подойдёт именно вам.
            </p>
          </header>

          {/* Quick Summary */}
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-2xl p-6 mb-10">
            <h2 className="text-lg font-semibold text-emerald-800 mb-3">
              Коротко: почему селлеры выбирают KleyKod
            </h2>
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-2 text-emerald-700">
                <DollarSign className="w-5 h-5 text-emerald-500" />
                <span className="text-sm">
                  <strong>Дешевле</strong> — PRO 490₽ vs 990₽+
                </span>
              </div>
              <div className="flex items-center gap-2 text-emerald-700">
                <Shield className="w-5 h-5 text-emerald-500" />
                <span className="text-sm">
                  <strong>Проверка качества</strong> DataMatrix
                </span>
              </div>
              <div className="flex items-center gap-2 text-emerald-700">
                <Eye className="w-5 h-5 text-emerald-500" />
                <span className="text-sm">
                  <strong>Прозрачные</strong> цены
                </span>
              </div>
            </div>
          </div>

          {/* Introduction */}
          <section className="prose prose-warm-gray max-w-none mb-10">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-4">
              Зачем нужна альтернатива wbcon?
            </h2>
            <p className="text-warm-gray-600 mb-4">
              <strong>Wbcon</strong> (barcoder.wbcon.ru) — один из первых сервисов для создания
              <strong> этикеток для Вайлдберриз</strong>. Он популярен, но имеет недостатки:
            </p>
            <ul className="space-y-2 text-warm-gray-600 mb-6">
              <li className="flex items-start gap-2">
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <span>Нет проверки качества DataMatrix до печати — возвраты на приёмке WB</span>
              </li>
              <li className="flex items-start gap-2">
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <span>PRO-тариф от 990₽/мес — дороже аналогов</span>
              </li>
              <li className="flex items-start gap-2">
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <span>Бесплатный тариф ограничен — только trial период</span>
              </li>
            </ul>

            <h2 className="text-2xl font-bold text-warm-gray-900 mb-4">
              Проблемы wbarcode
            </h2>
            <p className="text-warm-gray-600 mb-4">
              <strong>Wbarcode</strong> (wbarcode.ru) — ещё один <strong>генератор штрихкодов для Wildberries</strong>.
              Основные минусы:
            </p>
            <ul className="space-y-2 text-warm-gray-600 mb-6">
              <li className="flex items-start gap-2">
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <span>Скрытые цены — непонятно сколько стоит до регистрации</span>
              </li>
              <li className="flex items-start gap-2">
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <span>Медленная генерация — 1-2 минуты на партию</span>
              </li>
              <li className="flex items-start gap-2">
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <span>Нет Telegram-бота для быстрой генерации</span>
              </li>
            </ul>
          </section>

          {/* Comparison Table */}
          <section className="mb-10">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Сравнение генераторов этикеток для Вайлдберриз
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse bg-white rounded-xl overflow-hidden shadow-lg">
                <thead>
                  <tr className="bg-warm-gray-100">
                    <th className="text-left p-4 font-semibold text-warm-gray-700">
                      Функция
                    </th>
                    <th className="text-center p-4 font-semibold bg-emerald-100 text-emerald-800">
                      KleyKod
                      <span className="block text-xs font-normal text-emerald-600">Рекомендуем</span>
                    </th>
                    <th className="text-center p-4 font-semibold text-warm-gray-700">
                      wbcon
                    </th>
                    <th className="text-center p-4 font-semibold text-warm-gray-700">
                      wbarcode
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-gray-100">
                  {comparisonData.map((row, index) => (
                    <tr key={index} className={index % 2 === 0 ? "bg-warm-gray-50/50" : ""}>
                      <td className="p-4 text-warm-gray-700 font-medium">
                        {row.feature}
                      </td>
                      <td className="p-4 bg-emerald-50/50">
                        <div className="flex items-center justify-center gap-2">
                          <StatusIcon status={row.kleykod.status} />
                          <span className={`text-sm ${
                            row.kleykod.status === "best"
                              ? "font-semibold text-emerald-700"
                              : "text-warm-gray-600"
                          }`}>
                            {row.kleykod.value}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center justify-center gap-2">
                          <StatusIcon status={row.wbcon.status} />
                          <span className="text-sm text-warm-gray-600">
                            {row.wbcon.value}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center justify-center gap-2">
                          <StatusIcon status={row.wbarcode.status} />
                          <span className="text-sm text-warm-gray-600">
                            {row.wbarcode.value}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* KleyKod Advantages */}
          <section className="bg-gradient-to-br from-emerald-50 to-white border border-emerald-200 rounded-2xl p-6 mb-10">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-6">
              Почему KleyKod — лучшая альтернатива wbcon
            </h2>

            <div className="grid sm:grid-cols-2 gap-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <Shield className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-warm-gray-800 mb-1">
                    Проверка качества (Preflight)
                  </h3>
                  <p className="text-sm text-warm-gray-600">
                    Единственный сервис, который проверяет DataMatrix <strong>до печати</strong>:
                    размер ≥22мм, контрастность ≥80%, DPI 203. Никаких возвратов на приёмке WB.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-warm-gray-800 mb-1">
                    Честные цены
                  </h3>
                  <p className="text-sm text-warm-gray-600">
                    <strong>Бесплатно</strong>: 50 этикеток/день навсегда.
                    <strong>PRO</strong>: 490₽/мес (500/день).
                    <strong>Enterprise</strong>: 1990₽/мес (безлимит).
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <Zap className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-warm-gray-800 mb-1">
                    Мгновенная генерация
                  </h3>
                  <p className="text-sm text-warm-gray-600">
                    В <strong>50 раз быстрее</strong> ручной работы. Пока wbarcode обрабатывает
                    файлы минутами — мы генерируем PDF мгновенно.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <Users className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-warm-gray-800 mb-1">
                    Telegram-бот
                  </h3>
                  <p className="text-sm text-warm-gray-600">
                    <Link href="https://t.me/kleykod_bot" className="text-emerald-600 hover:underline">
                      @kleykod_bot
                    </Link> — генерируйте <strong>наклейки для вб</strong> прямо в мессенджере.
                    Без регистрации, без установки.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Pricing Comparison */}
          <section className="mb-10">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Сравнение цен: wbcon vs KleyKod
            </h2>

            <div className="grid sm:grid-cols-3 gap-6">
              {/* KleyKod */}
              <div className="relative bg-white border-2 border-emerald-500 rounded-2xl p-6 shadow-lg">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="px-3 py-1 bg-emerald-500 text-white text-sm font-medium rounded-full">
                    Рекомендуем
                  </span>
                </div>
                <div className="text-center mb-4">
                  <h3 className="font-bold text-xl text-warm-gray-800">KleyKod</h3>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">Бесплатно</span>
                    <span className="font-semibold text-emerald-600">50/день</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">PRO</span>
                    <span className="font-semibold">490₽/мес</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">Enterprise</span>
                    <span className="font-semibold">1990₽/мес</span>
                  </div>
                </div>
              </div>

              {/* wbcon */}
              <div className="bg-white border border-warm-gray-200 rounded-2xl p-6">
                <div className="text-center mb-4">
                  <h3 className="font-bold text-xl text-warm-gray-800">wbcon</h3>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">Бесплатно</span>
                    <span className="text-warm-gray-500">Trial</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">PRO</span>
                    <span className="font-semibold">от 990₽/мес</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">Enterprise</span>
                    <span className="text-warm-gray-500">Договор</span>
                  </div>
                </div>
              </div>

              {/* wbarcode */}
              <div className="bg-white border border-warm-gray-200 rounded-2xl p-6">
                <div className="text-center mb-4">
                  <h3 className="font-bold text-xl text-warm-gray-800">wbarcode</h3>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">Бесплатно</span>
                    <span className="text-warm-gray-500">?</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">PRO</span>
                    <span className="text-warm-gray-500">Скрыта</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-warm-gray-600">Enterprise</span>
                    <span className="text-warm-gray-500">Скрыта</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* FAQ */}
          <section className="mb-10">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Частые вопросы об альтернативах wbcon
            </h2>

            <div className="space-y-4">
              {[
                {
                  q: "Можно ли использовать wbcon бесплатно?",
                  a: "Wbcon предлагает только trial-период. После окончания нужно оплатить подписку. KleyKod даёт 50 этикеток в день бесплатно навсегда — без ограничения по времени."
                },
                {
                  q: "Чем KleyKod лучше wbarcode?",
                  a: "KleyKod быстрее (мгновенная генерация vs 1-2 минуты), имеет прозрачные цены (wbarcode скрывает стоимость), и проверяет качество DataMatrix до печати."
                },
                {
                  q: "Можно ли перейти с wbcon на KleyKod?",
                  a: "Да, переход занимает 5 минут. Загрузите тот же Excel из WB и PDF с кодами ЧЗ — KleyKod примет их без изменений. Форматы файлов совместимы."
                },
                {
                  q: "Какой генератор этикеток для Вайлдберриз лучше для начинающих?",
                  a: "KleyKod — бесплатный тариф без ограничения по времени (50 этикеток/день), простой интерфейс, Telegram-бот для быстрой генерации без регистрации."
                },
              ].map((faq, i) => (
                <details key={i} className="group bg-white border border-warm-gray-200 rounded-xl">
                  <summary className="flex items-center justify-between p-5 cursor-pointer list-none">
                    <span className="font-medium text-warm-gray-900 pr-4">{faq.q}</span>
                    <ArrowRight className="w-5 h-5 text-warm-gray-500 group-open:rotate-90 transition-transform flex-shrink-0" />
                  </summary>
                  <div className="px-5 pb-5 pt-0">
                    <p className="text-warm-gray-600">{faq.a}</p>
                  </div>
                </details>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="bg-gradient-to-br from-emerald-600 to-teal-600 rounded-2xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-3">
              Попробуйте лучшую альтернативу wbcon
            </h2>
            <p className="text-emerald-100 mb-6 max-w-lg mx-auto">
              50 этикеток в день бесплатно. Проверка качества DataMatrix.
              Прозрачные цены. Переход с wbcon за 5 минут.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-emerald-700 rounded-xl font-semibold hover:bg-emerald-50 transition-colors shadow-lg"
              >
                <Sparkles className="w-5 h-5" />
                Создать этикетки бесплатно
              </Link>
              <Link
                href="https://t.me/kleykod_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 text-emerald-100 hover:text-white transition-colors"
              >
                Попробовать в Telegram
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </section>

          {/* Related Articles */}
          <section className="mt-12 pt-8 border-t border-warm-gray-200">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-4">
              Полезные статьи
            </h2>

            <div className="grid sm:grid-cols-2 gap-4">
              <Link
                href="/articles/kak-nastroit-kleykod-za-5-minut"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Как настроить KleyKod за 5 минут →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Пошаговая инструкция для новых пользователей
                </p>
              </Link>

              <Link
                href="/articles/pochemu-datamatrix-ne-skaniruetsya"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Почему DataMatrix не сканируется →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Как избежать возвратов на приёмке Wildberries
                </p>
              </Link>

              <Link
                href="/articles/kakoy-printer-kupit-dlya-etiketok-58x40"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Какой принтер купить для этикеток 58×40 →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Обзор термопринтеров для маркировки
                </p>
              </Link>

              <Link
                href="/faq"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Частые вопросы →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Ответы на вопросы о маркировке и генераторе этикеток
                </p>
              </Link>
            </div>
          </section>
        </div>
      </article>

      {/* Footer */}
      <footer className="bg-warm-gray-900 text-warm-gray-500 py-8">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-white">KleyKod</span>
            </Link>
            <p className="text-sm">
              © {new Date().getFullYear()} KleyKod. Все права защищены.
            </p>
            <div className="flex items-center gap-4 text-sm">
              <Link href="/terms" className="hover:text-white transition-colors">
                Условия
              </Link>
              <Link href="/privacy" className="hover:text-white transition-colors">
                Конфиденциальность
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
