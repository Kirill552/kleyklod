import Link from "next/link";
import type { Metadata } from "next";
import {
  Sparkles,
  ArrowRight,
  Clock,
  Printer,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Zap,
  ThermometerSun,
  Snowflake,
  ChevronRight,
  Star,
  TrendingUp,
  Package,
} from "lucide-react";

export const metadata: Metadata = {
  title:
    "Какой принтер купить для этикеток 58x40 — обзор термопринтеров 2026 | KleyKod",
  description:
    "Какой термопринтер для этикеток выбрать селлеру Wildberries и Ozon? Сравнение Xprinter 365B, TSC TE200, Godex G500: цены, характеристики, рекомендации по объёмам.",
  keywords:
    "термопринтер для этикеток, xprinter 365b, tsc te200, какой принтер для этикеток, принтер этикеток для маркетплейсов, термопринтер 58x40",
  openGraph: {
    title: "Какой принтер купить для этикеток 58x40 — обзор 2026",
    description:
      "Сравнение термопринтеров для Wildberries и Ozon: Xprinter, TSC, Godex. Цены, характеристики, рекомендации.",
    type: "article",
    locale: "ru_RU",
  },
};

interface PrinterModel {
  name: string;
  resolution: string;
  type: string;
  price: string;
  speed: string;
  width: string;
  costPerLabel: string;
  forWhom: string;
  recommended?: boolean;
  pros: string[];
  cons: string[];
}

const printers: PrinterModel[] = [
  {
    name: "MPRINT LP58 EVA",
    resolution: "203 dpi",
    type: "Термо",
    price: "4 500 — 12 800 ₽",
    speed: "100 мм/сек",
    width: "72 мм",
    costPerLabel: "0.15 — 0.20 ₽",
    forWhom: "До 50 этикеток/день",
    pros: ["Самый дешёвый", "Компактный", "Plug-and-play"],
    cons: ["Только термопечать", "Узкая ширина 72мм", "203 dpi — минимум"],
  },
  {
    name: "Xprinter XP-365B",
    resolution: "203 dpi",
    type: "Термо",
    price: "5 000 — 8 000 ₽",
    speed: "127 мм/сек",
    width: "82 мм",
    costPerLabel: "0.15 — 0.20 ₽",
    forWhom: "До 100 этикеток/день",
    pros: ["Популярный", "Много инструкций", "Дешёвые расходники"],
    cons: ["Только термопечать", "203 dpi", "Китайские драйверы"],
  },
  {
    name: "АТОЛ ТТ42",
    resolution: "203 dpi",
    type: "Термотрансфер",
    price: "~13 800 ₽",
    speed: "102 мм/сек",
    width: "108 мм",
    costPerLabel: "0.25 — 0.35 ₽",
    forWhom: "До 100 этикеток/день",
    pros: ["Российский бренд", "Термотрансфер", "Хорошая поддержка"],
    cons: ["203 dpi", "Дороже Xprinter", "Нужен риббон"],
  },
  {
    name: "Honeywell PC42T",
    resolution: "203 dpi",
    type: "Термотрансфер",
    price: "15 500 — 19 300 ₽",
    speed: "102 мм/сек",
    width: "104 мм",
    costPerLabel: "0.25 — 0.35 ₽",
    forWhom: "50-200 этикеток/день",
    pros: ["Надёжный бренд", "Термотрансфер", "104мм ширина"],
    cons: ["203 dpi", "Дороже конкурентов", "Медленнее TSC"],
  },
  {
    name: "TSC TE200 / TE300",
    resolution: "203 / 300 dpi",
    type: "Термотрансфер",
    price: "15 000 — 35 000 ₽",
    speed: "127 мм/сек",
    width: "108 мм",
    costPerLabel: "0.25 — 0.35 ₽",
    forWhom: "100-500 этикеток/день",
    recommended: true,
    pros: ["300 dpi (TE300)", "Стандарт WB/Ozon", "Надёжный"],
    cons: ["Дороже бюджетных", "Доставка 1-2 недели"],
  },
  {
    name: "Godex G500 / G530",
    resolution: "203 / 300 dpi",
    type: "Термотрансфер",
    price: "30 000 — 45 000 ₽",
    speed: "127 мм/сек",
    width: "108 мм",
    costPerLabel: "0.20 — 0.30 ₽",
    forWhom: "200-800 этикеток/день",
    pros: ["300 dpi (G530)", "Промышленный ресурс", "Ethernet"],
    cons: ["Высокая цена", "Избыточен для малых объёмов"],
  },
  {
    name: "TSC ML340",
    resolution: "300 dpi",
    type: "Термотрансфер",
    price: "60 000 — 85 000 ₽",
    speed: "127 мм/сек",
    width: "108 мм",
    costPerLabel: "0.20 — 0.30 ₽",
    forWhom: "1000+ этикеток/день",
    pros: ["300 dpi", "Промышленный", "Ethernet + USB Host"],
    cons: ["Высокая цена", "Для крупного бизнеса"],
  },
  {
    name: "Zebra ZT510",
    resolution: "203/300/600 dpi",
    type: "Термотрансфер",
    price: "139 000 — 252 000 ₽",
    speed: "305 мм/сек",
    width: "104 мм",
    costPerLabel: "0.18 — 0.28 ₽",
    forWhom: "5000+ этикеток/день",
    pros: ["Промышленный стандарт", "До 600 dpi", "Экстремальная надёжность"],
    cons: ["Очень дорогой", "Только для крупного производства"],
  },
];

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
          <span className="text-warm-gray-700">Выбор принтера</span>
        </nav>
      </div>

      {/* Article Content */}
      <article className="container mx-auto px-4 sm:px-6 pb-24">
        <div className="max-w-5xl mx-auto">
          {/* Article Header */}
          <header className="mb-10">
            <div className="flex items-center gap-3 mb-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                <Printer className="w-4 h-4" />
                Обзор
              </span>
              <span className="inline-flex items-center gap-1.5 text-warm-gray-500 text-sm">
                <Clock className="w-4 h-4" />7 мин чтения
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold text-warm-gray-900 mb-4 leading-tight">
              Какой принтер купить для этикеток 58×40
            </h1>

            <p className="text-lg text-warm-gray-600 leading-relaxed">
              Объективное сравнение <strong>термопринтеров для этикеток</strong>{" "}
              с кодами маркировки Честный Знак. Разбираем{" "}
              <strong>Xprinter 365B</strong>, <strong>TSC TE200</strong>, Godex и
              другие модели: цены, характеристики, рекомендации по объёмам.
            </p>
          </header>

          {/* Quick Recommendation */}
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 mb-10">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-emerald-800 mb-4">
              <Star className="w-5 h-5 fill-emerald-500 text-emerald-500" />
              Быстрая рекомендация
            </h2>
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="bg-white/60 rounded-xl p-4">
                <p className="text-xs text-emerald-600 font-medium mb-1">
                  До 50 шт/день
                </p>
                <p className="font-semibold text-emerald-800">Xprinter XP-365B</p>
                <p className="text-sm text-emerald-700">5 000 — 8 000 ₽</p>
              </div>
              <div className="bg-white/60 rounded-xl p-4 ring-2 ring-emerald-400">
                <p className="text-xs text-emerald-600 font-medium mb-1">
                  50-500 шт/день
                </p>
                <p className="font-semibold text-emerald-800">TSC TE300 (300 dpi)</p>
                <p className="text-sm text-emerald-700">25 000 — 35 000 ₽</p>
                <span className="inline-block mt-1 text-xs bg-emerald-600 text-white px-2 py-0.5 rounded">
                  Рекомендуем
                </span>
              </div>
              <div className="bg-white/60 rounded-xl p-4">
                <p className="text-xs text-emerald-600 font-medium mb-1">
                  500+ шт/день
                </p>
                <p className="font-semibold text-emerald-800">TSC ML340 / Godex G530</p>
                <p className="text-sm text-emerald-700">45 000 — 85 000 ₽</p>
              </div>
            </div>
          </div>

          {/* Key Requirements */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-10">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-amber-800 mb-4">
              <AlertTriangle className="w-5 h-5" />
              Главное при выборе термопринтера для этикеток
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-warm-gray-800">
                      Разрешение 300 dpi
                    </p>
                    <p className="text-sm text-warm-gray-600">
                      Для стабильной печати DataMatrix. 203 dpi — минимум, но
                      рискованно.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-warm-gray-800">
                      Ширина печати ≥104 мм
                    </p>
                    <p className="text-sm text-warm-gray-600">
                      Для этикетки 58×40 + текст. 72 мм — впритык.
                    </p>
                  </div>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-warm-gray-800">
                      Термотрансфер (риббон)
                    </p>
                    <p className="text-sm text-warm-gray-600">
                      Для долговечности. Термо — только для краткосрочного хранения.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-warm-gray-800">
                      Запас по объёму +20-30%
                    </p>
                    <p className="text-sm text-warm-gray-600">
                      Выбирайте с запасом на рост. Переплата за избыточную
                      мощность — впустую.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Сравнительная таблица термопринтеров
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse bg-white rounded-xl overflow-hidden shadow-sm text-sm">
                <thead>
                  <tr className="bg-warm-gray-100">
                    <th className="text-left p-3 font-semibold text-warm-gray-700">
                      Модель
                    </th>
                    <th className="text-left p-3 font-semibold text-warm-gray-700">
                      Разрешение
                    </th>
                    <th className="text-left p-3 font-semibold text-warm-gray-700">
                      Тип
                    </th>
                    <th className="text-left p-3 font-semibold text-warm-gray-700">
                      Цена
                    </th>
                    <th className="text-left p-3 font-semibold text-warm-gray-700">
                      Для кого
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-gray-100">
                  {printers.map((printer, index) => (
                    <tr
                      key={index}
                      className={
                        printer.recommended
                          ? "bg-emerald-50"
                          : index % 2 === 0
                            ? "bg-white"
                            : "bg-warm-gray-50"
                      }
                    >
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          {printer.recommended && (
                            <Star className="w-4 h-4 fill-emerald-500 text-emerald-500" />
                          )}
                          <span
                            className={
                              printer.recommended
                                ? "font-bold text-emerald-800"
                                : "font-medium text-warm-gray-900"
                            }
                          >
                            {printer.name}
                          </span>
                        </div>
                      </td>
                      <td className="p-3 text-warm-gray-600">
                        {printer.resolution}
                      </td>
                      <td className="p-3 text-warm-gray-600">{printer.type}</td>
                      <td className="p-3 text-warm-gray-900 font-medium">
                        {printer.price}
                      </td>
                      <td className="p-3 text-warm-gray-600">
                        {printer.forWhom}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-warm-gray-500 mt-2">
              * Цены актуальны на январь 2026. Себестоимость этикетки включает
              расходники при оптовом заказе.
            </p>
          </div>

          {/* Thermo vs Thermotransfer */}
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Термопечать vs Термотрансфер — что выбрать?
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-orange-50 border border-orange-200 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                    <ThermometerSun className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-orange-800">Термопечать</h3>
                    <p className="text-sm text-orange-600">Прямая термо</p>
                  </div>
                </div>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2 text-orange-700">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5" />
                    <span>Принтер дешевле на 20-30%</span>
                  </li>
                  <li className="flex items-start gap-2 text-orange-700">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5" />
                    <span>Только этикетки (0.10-0.15 ₽/шт)</span>
                  </li>
                  <li className="flex items-start gap-2 text-orange-700">
                    <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                    <span>Срок жизни 3-12 месяцев</span>
                  </li>
                  <li className="flex items-start gap-2 text-orange-700">
                    <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                    <span>Выцветает на солнце</span>
                  </li>
                  <li className="flex items-start gap-2 text-orange-700">
                    <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                    <span>Боится влаги и мороза</span>
                  </li>
                </ul>
                <p className="mt-4 text-xs text-orange-600 bg-orange-100 rounded-lg p-2">
                  <strong>Подходит:</strong> продукты питания, расходники —
                  товары с коротким циклом продажи (2-3 недели).
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Snowflake className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-blue-800">Термотрансфер</h3>
                    <p className="text-sm text-blue-600">С риббоном</p>
                  </div>
                </div>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2 text-blue-700">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5" />
                    <span>Срок жизни до 3 лет</span>
                  </li>
                  <li className="flex items-start gap-2 text-blue-700">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5" />
                    <span>Водостойкость, морозостойкость до -40°C</span>
                  </li>
                  <li className="flex items-start gap-2 text-blue-700">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5" />
                    <span>Устойчивость к УФ и механике</span>
                  </li>
                  <li className="flex items-start gap-2 text-blue-700">
                    <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                    <span>Нужен риббон (0.25-0.35 ₽/шт)</span>
                  </li>
                  <li className="flex items-start gap-2 text-blue-700">
                    <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                    <span>Принтер дороже</span>
                  </li>
                </ul>
                <p className="mt-4 text-xs text-blue-600 bg-blue-100 rounded-lg p-2">
                  <strong>Рекомендуем для WB/Ozon:</strong> товары на складах,
                  логистика, возвраты — нужна долговечность.
                </p>
              </div>
            </div>
          </div>

          {/* Recommendations by Volume */}
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Рекомендации по объёмам
            </h2>
            <div className="space-y-6">
              {/* Volume 1 */}
              <div className="bg-white border border-warm-gray-200 rounded-xl p-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-16 h-16 bg-warm-gray-100 rounded-xl flex items-center justify-center">
                    <Package className="w-8 h-8 text-warm-gray-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-warm-gray-900 mb-1">
                      До 50 этикеток/день
                    </h3>
                    <p className="text-warm-gray-600 mb-3">
                      Микро-бизнес, начинающий селлер, тестирование ниши.
                    </p>
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="bg-warm-gray-50 rounded-xl p-4">
                        <p className="font-semibold text-warm-gray-800">
                          Xprinter XP-365B
                        </p>
                        <p className="text-sm text-warm-gray-600">
                          5 000 — 8 000 ₽ • Термо • 203 dpi
                        </p>
                        <p className="text-xs text-warm-gray-500 mt-1">
                          Самый популярный бюджетный вариант. Много инструкций в
                          интернете.
                        </p>
                      </div>
                      <div className="bg-warm-gray-50 rounded-xl p-4">
                        <p className="font-semibold text-warm-gray-800">
                          АТОЛ ТТ42
                        </p>
                        <p className="text-sm text-warm-gray-600">
                          ~13 800 ₽ • Термотрансфер • 203 dpi
                        </p>
                        <p className="text-xs text-warm-gray-500 mt-1">
                          Если нужна долговечность этикетки. Российский бренд.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Volume 2 */}
              <div className="bg-emerald-50 border-2 border-emerald-300 rounded-xl p-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-16 h-16 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <TrendingUp className="w-8 h-8 text-emerald-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg font-bold text-emerald-800">
                        50-500 этикеток/день
                      </h3>
                      <span className="text-xs bg-emerald-600 text-white px-2 py-0.5 rounded">
                        Рекомендуем
                      </span>
                    </div>
                    <p className="text-emerald-700 mb-3">
                      Малый бизнес, активный селлер Wildberries/Ozon.
                    </p>
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="bg-white rounded-xl p-4 ring-2 ring-emerald-400">
                        <p className="font-bold text-emerald-800">
                          TSC TE300 (300 dpi)
                        </p>
                        <p className="text-sm text-emerald-700">
                          25 000 — 35 000 ₽ • Термотрансфер
                        </p>
                        <p className="text-xs text-emerald-600 mt-1">
                          <strong>Лучший выбор.</strong> 300 dpi — стандарт для
                          WB/Ozon. Надёжный, быстрый.
                        </p>
                      </div>
                      <div className="bg-white rounded-xl p-4">
                        <p className="font-semibold text-warm-gray-800">
                          Honeywell PC42T
                        </p>
                        <p className="text-sm text-warm-gray-600">
                          15 500 — 19 300 ₽ • Термотрансфер • 203 dpi
                        </p>
                        <p className="text-xs text-warm-gray-500 mt-1">
                          Бюджетнее, но 203 dpi — риск с качеством DataMatrix.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Volume 3 */}
              <div className="bg-white border border-warm-gray-200 rounded-xl p-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Zap className="w-8 h-8 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-warm-gray-900 mb-1">
                      500+ этикеток/день
                    </h3>
                    <p className="text-warm-gray-600 mb-3">
                      Средний бизнес, склад, производство.
                    </p>
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="bg-warm-gray-50 rounded-xl p-4">
                        <p className="font-semibold text-warm-gray-800">
                          TSC ML340 (300 dpi)
                        </p>
                        <p className="text-sm text-warm-gray-600">
                          60 000 — 85 000 ₽ • Промышленный
                        </p>
                        <p className="text-xs text-warm-gray-500 mt-1">
                          Лучший компромисс цена/производительность. До 2500
                          этикеток/час.
                        </p>
                      </div>
                      <div className="bg-warm-gray-50 rounded-xl p-4">
                        <p className="font-semibold text-warm-gray-800">
                          Godex G530 (300 dpi)
                        </p>
                        <p className="text-sm text-warm-gray-600">
                          37 800 — 45 100 ₽ • Полупромышленный
                        </p>
                        <p className="text-xs text-warm-gray-500 mt-1">
                          Дешевле TSC, но тот же уровень качества. Ethernet.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Common Mistakes */}
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-12">
            <h2 className="flex items-center gap-2 text-xl font-bold text-red-800 mb-4">
              <XCircle className="w-6 h-6" />
              Частые ошибки при выборе
            </h2>
            <div className="space-y-4">
              {[
                {
                  title: "Экономия на 203 dpi для маркировки",
                  desc: 'Коды либо не читаются на сортировочном центре WB, либо читаются с ошибками. Переотправка = убыток. Экономия 5-10 тыс. стирается за 2-3 брака.',
                },
                {
                  title: "Ширина печати 72-80 мм",
                  desc: "Xprinter, MPRINT LP58, HPRT LPQ80 — достаточно для кода 58×40, но без места на текст производителя. Минимум 104-108 мм.",
                },
                {
                  title: "Термопечать для товаров с длинным циклом",
                  desc: "Если товар лежит на складе месяц+ или едет в регионы зимой — термоэтикетка выцветет или отвалится. Нужен термотрансфер.",
                },
                {
                  title: "Переплата за производительность",
                  desc: "Продавец 200 этикеток/день не получит пользу от принтера на 5000 шт/день. Выбирайте +20-30% от текущих объёмов.",
                },
              ].map((mistake, index) => (
                <div key={index} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-red-200 text-red-700 rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </span>
                  <div>
                    <p className="font-semibold text-red-800">{mistake.title}</p>
                    <p className="text-sm text-red-700">{mistake.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* FAQ */}
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Частые вопросы
            </h2>
            <div className="space-y-4">
              {[
                {
                  q: "Какое минимальное разрешение нужно для DataMatrix 22×22 мм?",
                  a: "203 dpi — минимум, но рискованно. При 203 dpi каждый модуль кода получит ~2 пикселя. При 300 dpi — 3-4 пикселя, что достаточно для надёжного считывания. Для маркетплейсов рекомендуем 300 dpi.",
                },
                {
                  q: "Xprinter 365B подходит для Честного Знака?",
                  a: "Да, но с оговорками. 203 dpi и термопечать — минимум. Работает для небольших объёмов (до 50-100 шт/день) и товаров с коротким циклом. Для серьёзных объёмов лучше TSC TE300.",
                },
                {
                  q: "Нужен ли калибратор для проверки качества DataMatrix?",
                  a: "Для селлеров — нет. Достаточно: 1) визуальная проверка чёткости, 2) тест мобильным приложением-сканером, 3) проверка при приёмке на склад WB/Ozon. Аппаратные калибраторы (50-500 тыс. ₽) нужны только крупным производствам.",
                },
                {
                  q: "Где купить принтер с гарантией?",
                  a: "АТОЛ и Mertech — лучшее соотношение наличие/цена в России. TSC — стандарт рынка, но доставка 1-2 недели. Honeywell — хорошая поддержка, но дороже. Официальные дилеры: Scanberry, ТСД Эксперт, Smartcode.",
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
          <section className="bg-emerald-700 rounded-xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-3">
              Принтер есть? Печатайте этикетки!
            </h2>
            <p className="text-emerald-100 mb-6 max-w-lg mx-auto">
              KleyKod создаёт готовые PDF для любого термопринтера. Загрузите
              баркоды из WB + коды ЧЗ — получите этикетки за секунды.
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
                href="/articles/kak-nastroit-kleykod-za-5-minut"
                className="inline-flex items-center gap-2 px-6 py-3 text-emerald-100 hover:text-white transition-colors"
              >
                Как настроить KleyKod
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <p className="text-emerald-200 text-sm mt-4">
              50 этикеток в день — бесплатно
            </p>
          </section>

          {/* Related Articles */}
          <section className="mt-12 pt-8 border-t border-warm-gray-200">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-4">
              Полезные статьи
            </h2>

            <div className="grid sm:grid-cols-2 gap-4">
              <Link
                href="/articles/pochemu-datamatrix-ne-skaniruetsya"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Почему DataMatrix не сканируется →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Решение проблем с качеством печати и настройками
                </p>
              </Link>

              <Link
                href="/articles/kak-nastroit-kleykod-za-5-minut"
                className="group p-5 bg-warm-gray-50 rounded-xl hover:bg-warm-gray-100 transition-colors"
              >
                <h3 className="font-semibold text-warm-gray-800 mb-1 group-hover:text-emerald-600 transition-colors">
                  Как настроить KleyKod за 5 минут →
                </h3>
                <p className="text-sm text-warm-gray-600">
                  Быстрый старт: от загрузки файлов до печати
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
