import { Metadata } from "next";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  MessageCircle,
  Send,
  HelpCircle,
  Tag,
  Printer,
  ShieldCheck,
  CreditCard,
  Package,
} from "lucide-react";

/**
 * FAQ Page со Schema.org FAQPage разметкой
 * Целевые запросы:
 * - этикетки для вайлдберриз (1954)
 * - маркировка честный знак (70709)
 * - генератор этикеток для вайлдберриз (367)
 * - печать этикеток 58 40 (188)
 * - datamatrix код честный знак (215)
 */

// FAQ данные для отображения и Schema.org
const faqCategories = [
  {
    id: "general",
    title: "Общие вопросы",
    icon: HelpCircle,
    questions: [
      {
        question: "Что такое КлейКод и зачем он нужен?",
        answer: "КлейКод — это онлайн-генератор этикеток для Вайлдберриз и Ozon, который объединяет штрихкод товара и код маркировки Честный Знак (DataMatrix) на одной наклейке 58×40 мм. Вместо двух этикеток на товаре — одна. Это экономит время, материалы и решает проблему «2 стикеров на товаре».",
      },
      {
        question: "Можно ли клеить код Честного Знака и штрихкод WB на одной этикетке?",
        answer: "Да, это полностью легально и соответствует требованиям Wildberries и системы «Честный знак». Главное условие — оба кода должны читаться сканером, не перекрываться и иметь зону покоя минимум 3 мм. КлейКод автоматически размещает коды с соблюдением всех требований.",
      },
      {
        question: "Чем КлейКод лучше wbcon и wbarcode?",
        answer: "КлейКод — единственный сервис с проверкой качества DataMatrix ДО печати. Мы проверяем размер ≥22мм, контрастность ≥80%, DPI 203. Также у нас прозрачные цены (Старт — 50 шт/мес бесплатно, Про — 2000 шт/мес с накоплением за 490₽/мес), Telegram-бот для генерации без регистрации.",
      },
    ],
  },
  {
    id: "sizes",
    title: "Размеры этикеток",
    icon: Tag,
    questions: [
      {
        question: "Какой размер этикетки для Честного Знака нужен?",
        answer: "Стандартный размер этикетки — 58×40 мм. Это универсальный формат для термопринтеров и маркетплейсов (Wildberries, Ozon). KleyKod также поддерживает размеры 58×30 мм (для мелких товаров) и 58×60 мм (для крупных товаров с большим количеством информации).",
      },
      {
        question: "Какое разрешение нужно для печати DataMatrix?",
        answer: "Минимальное разрешение для DataMatrix — 203 DPI (точек на дюйм). Это стандарт термопринтеров. При меньшем разрешении код может не сканироваться на приёмке WB. KleyKod генерирует PDF именно в 203 DPI для гарантированного прохождения сканера.",
      },
      {
        question: "Какой минимальный размер DataMatrix кода?",
        answer: "Минимальный размер DataMatrix для Честного Знака — 22×22 мм. При меньшем размере код может не читаться сканером. KleyKod проверяет размер автоматически и предупреждает, если код слишком маленький.",
      },
    ],
  },
  {
    id: "printing",
    title: "Печать этикеток",
    icon: Printer,
    questions: [
      {
        question: "Как распечатать этикетку Честный Знак?",
        answer: "1) Загрузите Excel с баркодами из ЛК Wildberries. 2) Загрузите PDF с кодами ЧЗ из markirovka.crpt.ru. 3) KleyKod объединит их на одной этикетке 58×40. 4) Скачайте готовый PDF и распечатайте на термопринтере. Весь процесс занимает 2-3 минуты.",
      },
      {
        question: "Какой принтер нужен для печати этикеток 58×40?",
        answer: "Любой термопринтер с разрешением от 203 DPI. Популярные модели: Xprinter XP-365B (бюджет, ~5000₽), TSC TE200 (средний, ~15000₽), Godex G500 (профессиональный, ~25000₽). Рекомендуем термотрансферную печать для долговечности этикеток.",
      },
      {
        question: "Почему DataMatrix не сканируется после печати?",
        answer: "Частые причины: 1) Низкое разрешение печати (<203 DPI). 2) Маленький размер DataMatrix (<22мм). 3) Недостаточная контрастность (<80%). 4) Отсутствие зоны покоя (нужно минимум 3мм). KleyKod проверяет все эти параметры до печати и предупреждает о проблемах.",
      },
    ],
  },
  {
    id: "marking",
    title: "Маркировка Честный Знак",
    icon: ShieldCheck,
    questions: [
      {
        question: "Какой штраф за отсутствие маркировки Честный Знак?",
        answer: "Штраф за нарушение маркировки: до 300 000₽ для ИП, до 1 000 000₽ для юридических лиц. Товар без читаемого DataMatrix возвращается с приёмки FBS. KleyKod проверяет код до печати — гарантируем прохождение сканера WB.",
      },
      {
        question: "Где получить коды маркировки Честный Знак?",
        answer: "Коды маркировки заказываются в личном кабинете «Честный знак» (markirovka.crpt.ru). После заказа скачайте PDF с DataMatrix кодами и загрузите в KleyKod вместе с Excel из Wildberries. Система автоматически сопоставит товары по GTIN.",
      },
      {
        question: "Что делать если количество кодов ЧЗ не совпадает с товарами?",
        answer: "KleyKod сгенерирует этикетки по меньшему количеству и покажет предупреждение. Например: 50 товаров + 45 кодов ЧЗ = 45 готовых этикеток. Остальные товары можно обработать после получения дополнительных кодов.",
      },
    ],
  },
  {
    id: "pricing",
    title: "Тарифы и оплата",
    icon: CreditCard,
    questions: [
      {
        question: "Можно ли создать этикетку для маркетплейса бесплатно?",
        answer: "Да! Тариф Старт — 50 этикеток в месяц бесплатно навсегда. Без ограничений по функциям. Достаточно для FBS селлеров с небольшими объёмами. Про (2000/мес + накопление) — 490₽/мес, Бизнес (безлимит) — 1990₽/мес.",
      },
      {
        question: "Какие способы оплаты доступны?",
        answer: "Оплата банковской картой через ЮКасса (Visa, MasterCard, МИР). Для корпоративных клиентов возможна оплата по счёту. Подписка автоматически продлевается, отменить можно в любой момент в личном кабинете.",
      },
    ],
  },
  {
    id: "integration",
    title: "Интеграции",
    icon: Package,
    questions: [
      {
        question: "Есть ли Telegram-бот для генерации этикеток?",
        answer: "Да, @kleykod_bot позволяет генерировать этикетки прямо в Telegram без регистрации на сайте. Отправьте Excel с баркодами и PDF с кодами ЧЗ — получите готовый PDF для печати. Доступен на всех тарифах.",
      },
      {
        question: "Есть ли API для автоматизации?",
        answer: "Да, REST API доступен на тарифе Бизнес. Позволяет интегрировать генерацию этикеток в ваши системы: 1С, МойСклад, собственные CRM. Документация API в личном кабинете после активации тарифа.",
      },
      {
        question: "Работает ли КлейКод с Ozon и другими маркетплейсами?",
        answer: "Да, генератор этикеток работает с любыми маркетплейсами. Нужен Excel с баркодами товаров (из Wildberries, Ozon или вручную) и PDF с кодами Честный Знак — формат универсальный.",
      },
    ],
  },
];

// Собираем все вопросы для Schema.org
const allQuestions = faqCategories.flatMap((cat) => cat.questions);

// Schema.org FAQPage JSON-LD
const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: allQuestions.map((q) => ({
    "@type": "Question",
    name: q.question,
    acceptedAnswer: {
      "@type": "Answer",
      text: q.answer,
    },
  })),
};

export const metadata: Metadata = {
  title: "FAQ — Частые вопросы о маркировке и генераторе этикеток для Wildberries",
  description:
    "Ответы на частые вопросы: как создать этикетку для Вайлдберриз, размеры этикеток 58×40, маркировка Честный Знак, печать DataMatrix, тарифы KleyKod. Бесплатная помощь селлерам WB.",
  keywords: [
    "этикетки для вайлдберриз",
    "маркировка честный знак",
    "генератор этикеток для вайлдберриз",
    "печать этикеток 58 40",
    "datamatrix код честный знак",
    "штрихкод wildberries",
    "наклейки вб",
    "faq этикетки",
    "вопросы маркировка",
  ],
  openGraph: {
    title: "FAQ — Частые вопросы | KleyKod",
    description: "Ответы на вопросы о маркировке товаров для Wildberries и Честного Знака",
    type: "website",
  },
  alternates: {
    canonical: "https://kleykod.ru/faq",
  },
};

export default function FAQPage() {
  return (
    <>
      {/* Schema.org FAQPage JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />

      <div className="min-h-screen bg-warm-gray-50">
        {/* Header */}
        <header className="sticky top-0 z-50 bg-white border-b-2 border-warm-gray-200">
          <div className="container mx-auto px-4 sm:px-6">
            <div className="flex items-center justify-between h-16">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-9 h-9 bg-emerald-500 rounded-xl flex items-center justify-center shadow-[2px_2px_0px_#E7E5E4]">
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
            <span className="text-warm-gray-700">FAQ</span>
          </nav>
        </div>

        {/* Hero */}
        <section className="container mx-auto px-4 sm:px-6 py-8">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-3xl sm:text-4xl font-bold text-warm-gray-900 mb-4">
              Частые вопросы о маркировке и{" "}
              <span className="text-emerald-600">этикетках для Wildberries</span>
            </h1>
            <p className="text-lg text-warm-gray-600 mb-8">
              Ответы на вопросы селлеров о генераторе этикеток, маркировке Честный Знак,
              печати DataMatrix и работе с KleyKod
            </p>

            {/* Quick Links */}
            <div className="flex flex-wrap justify-center gap-2 mb-8">
              {faqCategories.map((cat) => (
                <a
                  key={cat.id}
                  href={`#${cat.id}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border-2 border-warm-gray-200 rounded-full text-sm text-warm-gray-600 hover:border-emerald-400 hover:text-emerald-600 transition-colors"
                >
                  <cat.icon className="w-4 h-4" />
                  {cat.title}
                </a>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Categories */}
        <main className="container mx-auto px-4 sm:px-6 pb-16">
          <div className="max-w-4xl mx-auto space-y-12">
            {faqCategories.map((category) => {
              const Icon = category.icon;
              return (
                <section key={category.id} id={category.id}>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <Icon className="w-5 h-5 text-emerald-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-warm-gray-900">
                      {category.title}
                    </h2>
                  </div>

                  <div className="space-y-4">
                    {category.questions.map((faq, index) => (
                      <details
                        key={index}
                        className="group bg-white border-2 border-warm-gray-200 rounded-xl shadow-[2px_2px_0px_#E7E5E4]"
                      >
                        <summary className="flex items-center justify-between p-5 cursor-pointer list-none">
                          <span className="font-medium text-warm-gray-900 pr-4">
                            {faq.question}
                          </span>
                          <ArrowRight className="w-5 h-5 text-warm-gray-500 group-open:rotate-90 transition-transform flex-shrink-0" />
                        </summary>
                        <div className="px-5 pb-5 pt-0">
                          <p className="text-warm-gray-600 leading-relaxed">
                            {faq.answer}
                          </p>
                        </div>
                      </details>
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        </main>

        {/* Contact Section */}
        <section className="bg-warm-gray-100 py-12">
          <div className="container mx-auto px-4 sm:px-6">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-2xl font-bold text-warm-gray-900 mb-4">
                Не нашли ответ на свой вопрос?
              </h2>
              <p className="text-warm-gray-600 mb-6">
                Напишите нам в Telegram или VK — ответим в течение часа в рабочее время
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <a
                  href="https://t.me/kleykod_bot"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-[#0088cc] text-white rounded-xl font-medium hover:bg-[#007bb5] transition-colors"
                >
                  <Send className="w-5 h-5" />
                  Написать в Telegram
                </a>
                <a
                  href="https://vk.ru/kleykod"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-[#0077ff] text-white rounded-xl font-medium hover:bg-[#0066dd] transition-colors"
                >
                  <MessageCircle className="w-5 h-5" />
                  Написать в VK
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="container mx-auto px-4 sm:px-6 py-12">
          <div className="max-w-4xl mx-auto">
            <div className="bg-emerald-600 rounded-xl p-8 text-white text-center shadow-[2px_2px_0px_#E7E5E4]">
              <h2 className="text-2xl font-bold mb-3">
                Готовы создать этикетки для Wildberries?
              </h2>
              <p className="text-emerald-100 mb-6 max-w-lg mx-auto">
                50 этикеток в месяц бесплатно. Проверка качества DataMatrix до печати.
                Генерация в 50 раз быстрее ручной работы.
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-white text-emerald-700 rounded-xl font-semibold hover:bg-emerald-50 transition-colors shadow-[2px_2px_0px_#E7E5E4]"
                >
                  <Sparkles className="w-5 h-5" />
                  Создать этикетки бесплатно
                </Link>
                <Link
                  href="/articles"
                  className="inline-flex items-center gap-2 px-6 py-3 text-emerald-100 hover:text-white transition-colors"
                >
                  Читать статьи
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-warm-gray-900 text-warm-gray-500 py-8">
          <div className="container mx-auto px-4 sm:px-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
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
    </>
  );
}
