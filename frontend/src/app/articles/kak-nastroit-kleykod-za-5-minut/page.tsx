"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  Clock,
  Zap,
  CheckCircle2,
  ChevronRight,
  Play,
  Download,
  Eye,
  Sliders,
  Package,
} from "lucide-react";

// Metadata нужно вынести в layout или использовать generateMetadata
// export const metadata = { ... }

interface Step {
  title: string;
  description: string;
  tips?: string[];
}

const excelSteps: Step[] = [
  {
    title: "Скачайте Excel с баркодами из WB",
    description:
      "Зайдите в ЛК Wildberries → Товары и цены → Карточки товаров. Выберите нужные товары и нажмите «Редактировать» → «Excel» → «Сохранить».",
    tips: [
      "Подробная инструкция в статье «Как скачать Excel с баркодами»",
      "Файл должен содержать колонку «Штрихкод товара»",
    ],
  },
  {
    title: "Скачайте PDF с кодами Честный Знак",
    description:
      "В личном кабинете ЧЗ перейдите в «Коды маркировки» → выберите товарную группу → «Скачать PDF». Это файл с DataMatrix кодами.",
    tips: [
      "Инструкция в статье «Как получить коды маркировки ЧЗ»",
      "Один PDF может содержать коды для нескольких товаров",
    ],
  },
  {
    title: "Загрузите файлы в KleyKod",
    description:
      "На главной странице KleyKod нажмите «Создать этикетки». Загрузите Excel-файл из WB и PDF с кодами ЧЗ. Система автоматически сопоставит товары по GTIN.",
    tips: [
      "Можно перетащить файлы мышкой (drag & drop)",
      "Поддерживаются .xlsx, .xls и .pdf форматы",
    ],
  },
  {
    title: "Настройте шаблон этикетки",
    description:
      "Выберите размер этикетки (58×40 мм — стандарт для WB) и layout: Basic (минимум), Professional (с артикулом) или Extended (кастомные поля).",
    tips: ["Preview обновляется в реальном времени"],
  },
  {
    title: "Скачайте готовый PDF",
    description:
      "Нажмите «Создать PDF». KleyKod проверит качество кодов (размер DataMatrix ≥22мм, контрастность ≥80%) и сгенерирует файл для печати.",
    tips: [
      "Если код не проходит проверку — система предупредит",
      "PDF готов к печати на термопринтере",
    ],
  },
];


function StepCard({
  step,
  index,
  isActive,
  isCompleted,
  onClick,
}: {
  step: Step;
  index: number;
  isActive: boolean;
  isCompleted: boolean;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={`
        relative p-5 rounded-xl border-2 cursor-pointer transition-all
        ${
          isActive
            ? "border-emerald-500 bg-emerald-50 shadow-lg shadow-emerald-100"
            : isCompleted
              ? "border-emerald-300 bg-emerald-50/50"
              : "border-warm-gray-200 bg-white hover:border-warm-gray-300"
        }
      `}
    >
      <div className="flex items-start gap-4">
        <div
          className={`
            flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg
            ${
              isActive
                ? "bg-emerald-600 text-white"
                : isCompleted
                  ? "bg-emerald-500 text-white"
                  : "bg-warm-gray-200 text-warm-gray-600"
            }
          `}
        >
          {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : index + 1}
        </div>

        <div className="flex-1">
          <h3
            className={`font-semibold mb-2 ${isActive ? "text-emerald-800" : "text-warm-gray-800"}`}
          >
            {step.title}
          </h3>
          <p
            className={`text-sm leading-relaxed ${isActive ? "text-emerald-700" : "text-warm-gray-600"}`}
          >
            {step.description}
          </p>

          {isActive && step.tips && (
            <div className="mt-3 space-y-1">
              {step.tips.map((tip, i) => (
                <p
                  key={i}
                  className="text-xs text-emerald-600 flex items-start gap-1.5"
                >
                  <span className="text-emerald-400 mt-0.5">•</span>
                  {tip}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ArticlePage() {
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const steps = excelSteps;

  const handleStepClick = (index: number) => {
    setActiveStep(index);
    if (index > 0 && !completedSteps.includes(index - 1)) {
      setCompletedSteps([...completedSteps, index - 1]);
    }
  };

  const handleNext = () => {
    if (activeStep < steps.length - 1) {
      setCompletedSteps([...completedSteps, activeStep]);
      setActiveStep(activeStep + 1);
    } else {
      setCompletedSteps([...completedSteps, activeStep]);
    }
  };

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
          <span className="text-warm-gray-700">Быстрый старт</span>
        </nav>
      </div>

      {/* Article Content */}
      <article className="container mx-auto px-4 sm:px-6 pb-16">
        <div className="max-w-4xl mx-auto">
          {/* Article Header */}
          <header className="mb-10">
            <div className="flex items-center gap-3 mb-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                <Zap className="w-4 h-4" />
                Быстрый старт
              </span>
              <span className="inline-flex items-center gap-1.5 text-warm-gray-500 text-sm">
                <Clock className="w-4 h-4" />5 мин чтения
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold text-warm-gray-900 mb-4 leading-tight">
              Как настроить KleyKod за 5 минут
            </h1>

            <p className="text-lg text-warm-gray-600 leading-relaxed">
              <strong>Генератор этикеток</strong> для Wildberries и Ozon с{" "}
              <strong>кодами маркировки Честный Знак</strong>. Пошаговая
              инструкция: от загрузки файлов до{" "}
              <strong>печати этикеток</strong> на термопринтере.
            </p>
          </header>

          {/* SEO Block 1 */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6 mb-10">
            <h2 className="text-lg font-semibold text-blue-800 mb-3">
              Что такое KleyKod?
            </h2>
            <p className="text-blue-700 leading-relaxed mb-4">
              KleyKod — это <strong>генератор этикеток для маркетплейсов</strong>{" "}
              (Wildberries, Ozon), который объединяет штрихкоды товаров и{" "}
              <strong>коды маркировки Честный Знак</strong> в одну наклейку.
              Вместо двух этикеток на товаре — одна.
            </p>
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-2 text-blue-700">
                <CheckCircle2 className="w-5 h-5 text-blue-500" />
                <span className="text-sm">
                  <strong>Бесплатно</strong> — 50 этикеток/день
                </span>
              </div>
              <div className="flex items-center gap-2 text-blue-700">
                <CheckCircle2 className="w-5 h-5 text-blue-500" />
                <span className="text-sm">
                  <strong>Проверка качества</strong> DataMatrix
                </span>
              </div>
              <div className="flex items-center gap-2 text-blue-700">
                <CheckCircle2 className="w-5 h-5 text-blue-500" />
                <span className="text-sm">
                  <strong>Без установки</strong> — работает в браузере
                </span>
              </div>
            </div>
          </div>

          {/* Steps */}
          <div className="mb-10">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-warm-gray-900">
                5 шагов к готовым этикеткам
              </h2>
              <span className="text-sm text-warm-gray-500">
                {completedSteps.length} / {steps.length} выполнено
              </span>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-warm-gray-200 rounded-full mb-6 overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-300"
                style={{
                  width: `${(completedSteps.length / steps.length) * 100}%`,
                }}
              />
            </div>

            <div className="space-y-4">
              {steps.map((step, index) => (
                <StepCard
                  key={index}
                  step={step}
                  index={index}
                  isActive={activeStep === index}
                  isCompleted={completedSteps.includes(index)}
                  onClick={() => handleStepClick(index)}
                />
              ))}
            </div>

            {/* Next Button */}
            <div className="mt-6 flex justify-center">
              <button
                onClick={handleNext}
                className={`
                  inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all
                  ${
                    completedSteps.length === steps.length
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-emerald-600 text-white hover:bg-emerald-700"
                  }
                `}
              >
                {completedSteps.length === steps.length ? (
                  <>
                    <CheckCircle2 className="w-5 h-5" />
                    Готово!
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    {activeStep === steps.length - 1
                      ? "Завершить"
                      : "Следующий шаг"}
                  </>
                )}
              </button>
            </div>
          </div>

          {/* SEO Block 2 - Features */}
          <div className="bg-warm-gray-50 border border-warm-gray-200 rounded-2xl p-6 mb-10">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-4">
              Возможности генератора этикеток
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {[
                {
                  icon: Eye,
                  title: "Live-превью",
                  desc: "Видите готовую этикетку до печати в реальном времени.",
                },
                {
                  icon: Sliders,
                  title: "3 шаблона",
                  desc: "Basic, Professional, Extended — от минимума до полной кастомизации.",
                },
                {
                  icon: Package,
                  title: "База товаров",
                  desc: "PRO: сохраняйте карточки товаров для быстрой генерации.",
                },
                {
                  icon: Download,
                  title: "Диапазон печати",
                  desc: "Печатайте частями: этикетки 5-15 из 50, например.",
                },
              ].map((feature, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                    <feature.icon className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-warm-gray-800">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-warm-gray-600">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sizes and Layouts Table */}
          <div className="mb-10">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-4">
              Размеры этикеток для маркетплейсов
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse bg-white rounded-xl overflow-hidden shadow-sm">
                <thead>
                  <tr className="bg-warm-gray-100">
                    <th className="text-left p-4 font-semibold text-warm-gray-700">
                      Размер
                    </th>
                    <th className="text-left p-4 font-semibold text-warm-gray-700">
                      Применение
                    </th>
                    <th className="text-left p-4 font-semibold text-warm-gray-700">
                      Layouts
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-gray-100">
                  <tr>
                    <td className="p-4 text-warm-gray-900 font-medium">
                      58×30 мм
                    </td>
                    <td className="p-4 text-warm-gray-600">
                      Мелкие товары, косметика
                    </td>
                    <td className="p-4 text-warm-gray-600">
                      Basic, Professional
                    </td>
                  </tr>
                  <tr className="bg-emerald-50">
                    <td className="p-4 text-emerald-800 font-bold">58×40 мм</td>
                    <td className="p-4 text-emerald-700">
                      Стандарт WB и Ozon
                    </td>
                    <td className="p-4 text-emerald-700">Все шаблоны</td>
                  </tr>
                  <tr>
                    <td className="p-4 text-warm-gray-900 font-medium">
                      58×60 мм
                    </td>
                    <td className="p-4 text-warm-gray-600">
                      Крупные товары, много информации
                    </td>
                    <td className="p-4 text-warm-gray-600">Все шаблоны</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* FAQ */}
          <div className="mb-12">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-6">
              Частые вопросы
            </h2>
            <div className="space-y-4">
              {[
                {
                  q: "Как печатать этикетки на термопринтере?",
                  a: "Скачайте PDF из KleyKod и откройте в любой программе для печати. Выберите принтер, установите размер бумаги 58×40 мм (или ваш размер), масштаб 100%. Печатайте без полей.",
                },
                {
                  q: "Какой принтер нужен для печати этикеток Честный Знак?",
                  a: "Любой термопринтер с разрешением от 203 dpi. Популярные модели: Xprinter XP-365B (бюджет), TSC TE200 (средний), Godex G500 (проф). Подробнее в статье «Какой принтер купить».",
                },
                {
                  q: "Можно ли печатать этикетки бесплатно?",
                  a: "Да, бесплатный тариф — 50 этикеток в день. Без ограничений по функциям. PRO (500/день) — 490₽/мес, Enterprise (безлимит) — 1990₽/мес.",
                },
                {
                  q: "Работает ли KleyKod с Ozon и другими маркетплейсами?",
                  a: "Да, генератор этикеток работает с любыми маркетплейсами. Нужен Excel с баркодами товаров и PDF с кодами Честный Знак — формат универсальный.",
                },
                {
                  q: "Что делать если количество кодов ЧЗ не совпадает с товарами?",
                  a: "KleyKod сгенерирует этикетки по меньшему количеству и покажет предупреждение. Например, 50 товаров + 45 кодов ЧЗ = 45 этикеток.",
                },
              ].map((faq, index) => (
                <details
                  key={index}
                  className="group bg-white border border-warm-gray-200 rounded-xl"
                >
                  <summary className="flex items-center justify-between p-5 cursor-pointer list-none">
                    <span className="font-medium text-warm-gray-900 pr-4">
                      {faq.q}
                    </span>
                    <ChevronRight className="w-5 h-5 text-warm-gray-400 group-open:rotate-90 transition-transform flex-shrink-0" />
                  </summary>
                  <div className="px-5 pb-5 pt-0">
                    <p className="text-warm-gray-600">{faq.a}</p>
                  </div>
                </details>
              ))}
            </div>
          </div>

          {/* CTA */}
          <section className="bg-gradient-to-br from-emerald-600 to-teal-600 rounded-2xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-3">Готовы начать?</h2>
            <p className="text-emerald-100 mb-6 max-w-lg mx-auto">
              Создайте первые этикетки прямо сейчас. 50 штук в день — бесплатно,
              без регистрации карты.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-emerald-700 rounded-xl font-semibold hover:bg-emerald-50 transition-colors shadow-lg"
              >
                <Sparkles className="w-5 h-5" />
                Создать этикетки
              </Link>
              <Link
                href="/#how-it-works"
                className="inline-flex items-center gap-2 px-6 py-3 text-emerald-100 hover:text-white transition-colors"
              >
                Смотреть демо
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
                href="/articles/kak-skachat-excel-s-barkodami-wildberries"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Как скачать Excel с баркодами из WB →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Пошаговая инструкция по выгрузке файла из ЛК Wildberries
                </p>
              </Link>

              <Link
                href="/articles/kak-poluchit-kody-markirovki-chestny-znak"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Как получить коды маркировки ЧЗ →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Где взять PDF с DataMatrix кодами из Честного Знака
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
                  Решение проблем с качеством печати и настройками сканера
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
                  Размеры этикеток, требования ЧЗ, тарифы и оплата
                </p>
              </Link>
            </div>
          </section>
        </div>
      </article>

      {/* Footer */}
      <footer className="bg-warm-gray-900 text-warm-gray-400 py-8">
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
              <Link
                href="/terms"
                className="hover:text-white transition-colors"
              >
                Условия
              </Link>
              <Link
                href="/privacy"
                className="hover:text-white transition-colors"
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
