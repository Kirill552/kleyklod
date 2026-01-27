"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  ChevronRight,
  QrCode,
  Clock,
  CheckCircle2,
  RefreshCw,
  Download,
  FileText,
} from "lucide-react";

// SEO metadata экспортируется отдельно для client component
export const dynamic = "force-static";

// Шаги первого получения кодов
const firstTimeSteps = [
  {
    id: 1,
    title: "Откройте раздел «Заказы»",
    description:
      "В личном кабинете Честного Знака перейдите в раздел «Заказы». Здесь отображаются все ваши заказы на коды маркировки. После генерации кодов статус заказа изменится на «Доступен».",
    image: "/articles/chestny-znak-kody/step-1.webp",
    tip: "Коды маркировки генерируются автоматически после оплаты. Обычно это занимает от нескольких секунд до нескольких минут.",
  },
  {
    id: 2,
    title: "Выберите заказ",
    description:
      "Найдите нужный заказ в списке и нажмите на его номер (идентификатор). Вы перейдёте на страницу с деталями заказа, где можно скачать коды маркировки.",
    image: "/articles/chestny-znak-kody/step-2.webp",
    tip: "Заказы со статусом «Доступен» содержат готовые коды для печати.",
  },
  {
    id: 3,
    title: "Нажмите «Перейти к печати»",
    description:
      "На странице заказа вы увидите общие данные: товарную группу, статус, способ выпуска товаров в оборот. Нажмите кнопку «Перейти к печати» в правом нижнем углу.",
    image: "/articles/chestny-znak-kody/step-3.webp",
    tip: null,
  },
  {
    id: 4,
    title: "Скачайте коды маркировки",
    description:
      "Откроется вкладка «Товары» со списком кодов. Нажмите на иконку принтера в колонке «Действия» — файл с кодами маркировки начнёт скачиваться на ваш компьютер.",
    image: "/articles/chestny-znak-kody/step-4.webp",
    tip: "Файл скачивается в формате PDF. Это именно тот файл, который нужно загрузить в KleyKod.",
  },
  {
    id: 5,
    title: "Файл успешно сформирован",
    description:
      "После нажатия на принтер система сформирует PDF-файл с кодами маркировки и автоматически скачает его. Для повторной загрузки перейдите в раздел Документы → Печать/Экспорт.",
    image: "/articles/chestny-znak-kody/step-5.webp",
    tip: null,
  },
  {
    id: 6,
    title: "Проверьте вкладку «Выполненные»",
    description:
      "Закрытые и обработанные заказы отображаются во вкладке «Выполненные». Здесь можно найти архив всех ваших заказов на коды маркировки.",
    image: "/articles/chestny-znak-kody/step-6.webp",
    tip: null,
  },
  {
    id: 7,
    title: "Статус «Обработан»",
    description:
      "Если вы всё сделали правильно, заказ получит статус «Обработан». Это означает, что коды маркировки успешно сгенерированы и скачаны.",
    image: "/articles/chestny-znak-kody/step-7.webp",
    tip: null,
  },
  {
    id: 8,
    title: "Коды в разделе «Коды маркировки»",
    description:
      "Все полученные коды отображаются со статусом «Эмитирован» в разделе «Коды маркировки» личного кабинета. Отсюда можно управлять кодами и отслеживать их статус.",
    image: "/articles/chestny-znak-kody/step-8.webp",
    tip: "Статус «Эмитирован» означает, что код выпущен и готов к нанесению на товар.",
  },
];

// Шаги повторного получения
const repeatSteps = [
  {
    id: 1,
    title: "Перейдите в Документы → Печать/Экспорт",
    description:
      "Для повторного получения кодов маркировки откройте раздел «Документы» и выберите вкладку «Печать/Экспорт». Здесь хранятся все ранее сформированные файлы.",
    image: "/articles/chestny-znak-kody/repeat-1.webp",
    tip: "Функция повторного получения файла с кодами маркировки доступна в течение 2 суток.",
  },
  {
    id: 2,
    title: "Выберите действие",
    description:
      "В колонке «Действия» доступны две иконки: «Скачать» — для сохранения ранее сформированного файла, «Печать» — для повторной печати кодов маркировки.",
    image: "/articles/chestny-znak-kody/repeat-2.webp",
    tip: null,
  },
  {
    id: 3,
    title: "Выберите формат файла",
    description:
      "При повторной печати можно выбрать формат: PDF, CSV или EPS. Важно: CSV и EPS не могут быть преобразованы в DataMatrix для нанесения на товар. Для KleyKod выбирайте PDF.",
    image: "/articles/chestny-znak-kody/repeat-3.webp",
    tip: "Для работы с KleyKod всегда выбирайте формат PDF — он содержит DataMatrix коды, готовые для печати.",
  },
];

function StepperProgress({
  currentStep,
  totalSteps,
}: {
  currentStep: number;
  totalSteps: number;
}) {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: totalSteps }).map((_, index) => (
        <div
          key={index}
          className={`h-1.5 rounded-full transition-all ${
            index < currentStep
              ? "bg-emerald-500 w-8"
              : index === currentStep
                ? "bg-emerald-500 w-12"
                : "bg-warm-gray-200 w-8"
          }`}
        />
      ))}
    </div>
  );
}

export default function ArticlePage() {
  const [activeTab, setActiveTab] = useState<"first" | "repeat">("first");
  const [currentStep, setCurrentStep] = useState(0);

  const steps = activeTab === "first" ? firstTimeSteps : repeatSteps;
  const step = steps[currentStep];

  const handleTabChange = (tab: "first" | "repeat") => {
    setActiveTab(tab);
    setCurrentStep(0);
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

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
              Создать этикетки
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
          <ChevronRight className="w-4 h-4" />
          <Link
            href="/articles"
            className="hover:text-emerald-600 transition-colors"
          >
            Статьи
          </Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-warm-gray-700">Коды маркировки ЧЗ</span>
        </nav>
      </div>

      {/* Article Content */}
      <article className="container mx-auto px-4 sm:px-6 pb-24">
        <div className="max-w-4xl mx-auto">
          {/* Article Header */}
          <header className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm font-medium">
                <QrCode className="w-4 h-4" />
                Интерактивный гайд
              </span>
              <span className="inline-flex items-center gap-1.5 text-warm-gray-500 text-sm">
                <Clock className="w-4 h-4" />5 мин
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold text-warm-gray-900 mb-4 leading-tight">
              Как получить коды маркировки Честный Знак
            </h1>

            <p className="text-lg text-warm-gray-600 leading-relaxed">
              Пошаговая инструкция по скачиванию{" "}
              <strong>кодов маркировки</strong> из личного кабинета системы{" "}
              <strong>Честный Знак</strong>. Покажем, как заказать коды впервые и
              как повторно распечатать уже полученные.
            </p>
          </header>

          {/* SEO Text Block */}
          <div className="bg-warm-gray-50 rounded-xl p-6 mb-8">
            <h2 className="text-lg font-semibold text-warm-gray-900 mb-3">
              Что такое коды маркировки?
            </h2>
            <p className="text-warm-gray-600 text-sm leading-relaxed mb-4">
              <strong>Коды маркировки Честный Знак</strong> — это уникальные
              идентификаторы товаров в формате DataMatrix. Каждый код содержит
              информацию о товаре и криптографическую подпись. Без{" "}
              <strong>кодов маркировки</strong> нельзя легально продавать товары,
              подлежащие обязательной маркировке: одежду, обувь, парфюмерию и
              другие категории.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="px-2 py-1 bg-white rounded text-xs text-warm-gray-600">
                коды маркировки честный знак
              </span>
              <span className="px-2 py-1 bg-white rounded text-xs text-warm-gray-600">
                заказ кодов маркировки
              </span>
              <span className="px-2 py-1 bg-white rounded text-xs text-warm-gray-600">
                печать кодов маркировки
              </span>
              <span className="px-2 py-1 bg-white rounded text-xs text-warm-gray-600">
                DataMatrix
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => handleTabChange("first")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all ${
                activeTab === "first"
                  ? "bg-emerald-600 text-white shadow-[2px_2px_0px_#047857]"
                  : "bg-warm-gray-100 text-warm-gray-600 hover:bg-warm-gray-200"
              }`}
            >
              <FileText className="w-4 h-4" />
              Первое получение
            </button>
            <button
              onClick={() => handleTabChange("repeat")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all ${
                activeTab === "repeat"
                  ? "bg-emerald-600 text-white shadow-[2px_2px_0px_#047857]"
                  : "bg-warm-gray-100 text-warm-gray-600 hover:bg-warm-gray-200"
              }`}
            >
              <RefreshCw className="w-4 h-4" />
              Повторное получение
            </button>
          </div>

          {/* Stepper */}
          <div className="bg-white rounded-xl border border-warm-gray-200 overflow-hidden shadow-sm">
            {/* Progress Header */}
            <div className="px-6 py-4 border-b border-warm-gray-100 bg-warm-gray-50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-warm-gray-600">
                  Шаг {currentStep + 1} из {steps.length}
                </span>
                <StepperProgress
                  currentStep={currentStep}
                  totalSteps={steps.length}
                />
              </div>
              <h3 className="text-xl font-bold text-warm-gray-900">
                {step.title}
              </h3>
            </div>

            {/* Step Content */}
            <div className="p-6">
              <p className="text-warm-gray-600 mb-6 leading-relaxed">
                {step.description}
              </p>

              {/* Image */}
              <div className="relative rounded-xl overflow-hidden border border-warm-gray-200 shadow-[2px_2px_0px_#E7E5E4] mb-6">
                <Image
                  src={step.image}
                  alt={step.title}
                  width={1200}
                  height={600}
                  className="w-full h-auto"
                  priority={currentStep === 0}
                />
              </div>

              {/* Tip */}
              {step.tip && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                  <span className="text-amber-500 text-xl flex-shrink-0">
                    💡
                  </span>
                  <p className="text-amber-800 text-sm">{step.tip}</p>
                </div>
              )}
            </div>

            {/* Navigation */}
            <div className="px-6 py-4 border-t border-warm-gray-100 bg-warm-gray-50 flex items-center justify-between">
              <button
                onClick={handlePrev}
                disabled={currentStep === 0}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  currentStep === 0
                    ? "text-warm-gray-300 cursor-not-allowed"
                    : "text-warm-gray-600 hover:bg-warm-gray-200"
                }`}
              >
                <ArrowLeft className="w-4 h-4" />
                Назад
              </button>

              {currentStep < steps.length - 1 ? (
                <button
                  onClick={handleNext}
                  className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors shadow-[2px_2px_0px_#047857]"
                >
                  Далее
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <Link
                  href="/login"
                  className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors shadow-[2px_2px_0px_#047857]"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Создать этикетки
                </Link>
              )}
            </div>
          </div>

          {/* Quick Navigation */}
          <div className="mt-6 flex flex-wrap gap-2">
            {steps.map((s, index) => (
              <button
                key={s.id}
                onClick={() => setCurrentStep(index)}
                className={`w-8 h-8 rounded-lg text-sm font-medium transition-all ${
                  index === currentStep
                    ? "bg-emerald-600 text-white"
                    : index < currentStep
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-warm-gray-100 text-warm-gray-500 hover:bg-warm-gray-200"
                }`}
              >
                {index + 1}
              </button>
            ))}
          </div>

          {/* CTA Section */}
          <section className="mt-12 bg-emerald-700 rounded-xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-3">Скачали коды маркировки?</h2>
            <p className="text-emerald-100 mb-6 max-w-lg mx-auto">
              Загрузите PDF с <strong>кодами маркировки</strong> в KleyKod вместе
              с Excel-файлом из Wildberries — получите готовые этикетки с{" "}
              <strong>DataMatrix</strong> за 5 секунд.
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
                href="/articles/kak-skachat-excel-s-barkodami-wildberries"
                className="inline-flex items-center gap-2 px-6 py-3 text-emerald-100 hover:text-white transition-colors"
              >
                Как скачать Excel из WB
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <p className="text-emerald-200 text-sm mt-4">
              50 этикеток в месяц — бесплатно
            </p>
          </section>

          {/* SEO Bottom Text */}
          <section className="mt-12 prose prose-warm-gray max-w-none">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-4">
              Часто задаваемые вопросы о кодах маркировки
            </h2>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-warm-gray-800 mb-2">
                  Сколько стоят коды маркировки Честный Знак?
                </h3>
                <p className="text-warm-gray-600 text-sm">
                  Стоимость одного кода маркировки составляет 60 копеек без НДС
                  (с 1 февраля 2025 года). Оплата производится при заказе кодов
                  в личном кабинете Честного Знака.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-warm-gray-800 mb-2">
                  Можно ли повторно распечатать коды маркировки?
                </h3>
                <p className="text-warm-gray-600 text-sm">
                  Да, повторная печать кодов маркировки доступна в течение 2
                  суток через раздел Документы → Печать/Экспорт. Выбирайте формат
                  PDF для работы с KleyKod.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-warm-gray-800 mb-2">
                  В каком формате скачиваются коды маркировки?
                </h3>
                <p className="text-warm-gray-600 text-sm">
                  Коды маркировки скачиваются в формате PDF с DataMatrix кодами.
                  Этот файл можно загрузить в KleyKod для создания этикеток с
                  штрихкодом Wildberries и кодом Честного Знака на одной
                  наклейке.
                </p>
              </div>
            </div>
          </section>

          {/* Related Articles */}
          <section className="mt-12 pt-8 border-t border-warm-gray-200">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-4">
              Читайте также
            </h2>

            <div className="grid sm:grid-cols-2 gap-4">
              <Link
                href="/articles/kak-skachat-excel-s-barkodami-wildberries"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Как скачать Excel с баркодами из Wildberries →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Пошаговая инструкция по выгрузке файла с баркодами товаров
                </p>
              </Link>

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
