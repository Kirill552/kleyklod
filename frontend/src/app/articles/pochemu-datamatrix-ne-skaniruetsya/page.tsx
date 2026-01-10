import Link from "next/link";
import type { Metadata } from "next";
import {
  Sparkles,
  ArrowRight,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Printer,
  ScanLine,
  Settings,
  Lightbulb,
  ChevronRight,
} from "lucide-react";

export const metadata: Metadata = {
  title:
    "Почему DataMatrix не сканируется — причины и решения | KleyKod",
  description:
    "Не читается честный знак? Разбираем типичные проблемы с маркировкой: качество печати, настройки сканера, размер кода. Пошаговые решения для селлеров.",
  keywords:
    "не читается честный знак, datamatrix не сканируется, код маркировки не читается, проблемы с маркировкой честный знак, печать этикеток маркировки",
  openGraph: {
    title: "Почему DataMatrix не сканируется — решение проблем",
    description:
      "Разбираем почему не читается честный знак и как это исправить: качество печати, настройки сканера, размер кода",
    type: "article",
    locale: "ru_RU",
  },
};

interface ProblemCardProps {
  icon: React.ElementType;
  title: string;
  problems: string[];
  solutions: string[];
  color: "red" | "amber" | "blue";
}

function ProblemCard({
  icon: Icon,
  title,
  problems,
  solutions,
  color,
}: ProblemCardProps) {
  const colors = {
    red: {
      bg: "bg-red-50",
      border: "border-red-200",
      iconBg: "bg-red-100",
      iconColor: "text-red-600",
      title: "text-red-800",
      problemBg: "bg-red-100/50",
      problemText: "text-red-700",
      solutionBg: "bg-emerald-100/50",
      solutionText: "text-emerald-700",
    },
    amber: {
      bg: "bg-amber-50",
      border: "border-amber-200",
      iconBg: "bg-amber-100",
      iconColor: "text-amber-600",
      title: "text-amber-800",
      problemBg: "bg-amber-100/50",
      problemText: "text-amber-700",
      solutionBg: "bg-emerald-100/50",
      solutionText: "text-emerald-700",
    },
    blue: {
      bg: "bg-blue-50",
      border: "border-blue-200",
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600",
      title: "text-blue-800",
      problemBg: "bg-blue-100/50",
      problemText: "text-blue-700",
      solutionBg: "bg-emerald-100/50",
      solutionText: "text-emerald-700",
    },
  };

  const c = colors[color];

  return (
    <div className={`${c.bg} ${c.border} border rounded-2xl p-6`}>
      <div className="flex items-start gap-4 mb-4">
        <div
          className={`flex-shrink-0 w-12 h-12 ${c.iconBg} rounded-xl flex items-center justify-center`}
        >
          <Icon className={`w-6 h-6 ${c.iconColor}`} />
        </div>
        <h3 className={`text-xl font-bold ${c.title} pt-2`}>{title}</h3>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className={`${c.problemBg} rounded-xl p-4`}>
          <h4 className={`font-semibold ${c.problemText} mb-2 flex items-center gap-2`}>
            <XCircle className="w-4 h-4" />
            Проблемы
          </h4>
          <ul className={`space-y-2 text-sm ${c.problemText}`}>
            {problems.map((problem, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5">•</span>
                <span>{problem}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className={`${c.solutionBg} rounded-xl p-4`}>
          <h4 className={`font-semibold ${c.solutionText} mb-2 flex items-center gap-2`}>
            <CheckCircle2 className="w-4 h-4" />
            Решения
          </h4>
          <ul className={`space-y-2 text-sm ${c.solutionText}`}>
            {solutions.map((solution, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-emerald-500 mt-0.5">✓</span>
                <span>{solution}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default function ArticlePage() {
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
          <span className="text-warm-gray-700">DataMatrix не сканируется</span>
        </nav>
      </div>

      {/* Article Content */}
      <article className="container mx-auto px-4 sm:px-6 pb-16">
        <div className="max-w-4xl mx-auto">
          {/* Article Header */}
          <header className="mb-10">
            <div className="flex items-center gap-3 mb-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                <AlertTriangle className="w-4 h-4" />
                Решение проблем
              </span>
              <span className="inline-flex items-center gap-1.5 text-warm-gray-500 text-sm">
                <Clock className="w-4 h-4" />4 мин чтения
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold text-warm-gray-900 mb-4 leading-tight">
              Почему DataMatrix не сканируется — причины и решения
            </h1>

            <p className="text-lg text-warm-gray-600 leading-relaxed">
              <strong>Не читается честный знак</strong> при приёмке на складе
              или в магазине? Разбираем типичные <strong>проблемы с маркировкой</strong>{" "}
              и даём пошаговые решения для каждой ситуации.
            </p>
          </header>

          {/* Quick Checklist */}
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-2xl p-6 mb-10">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-emerald-800 mb-4">
              <Lightbulb className="w-5 h-5" />
              Быстрая проверка — 5 пунктов
            </h2>
            <div className="grid sm:grid-cols-2 gap-3">
              {[
                "Размер DataMatrix минимум 22×22 мм",
                "Контрастность не менее 80%",
                "Используется 2D-сканер (не лазерный)",
                "Сканер в режиме COM-порта",
                "Код напечатан на качественной этикетке",
              ].map((item, index) => (
                <label
                  key={index}
                  className="flex items-center gap-3 bg-white/60 rounded-lg p-3 cursor-pointer hover:bg-white/80 transition-colors"
                >
                  <input
                    type="checkbox"
                    className="w-5 h-5 rounded border-emerald-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="text-emerald-700 text-sm">{item}</span>
                </label>
              ))}
            </div>
          </div>

          {/* SEO Text Block 1 */}
          <div className="prose prose-warm-gray max-w-none mb-10">
            <p className="text-warm-gray-600 leading-relaxed">
              Когда <strong>код маркировки не сканируется</strong>, селлеры теряют время
              и деньги: товар не принимают на склад, покупатели возвращают заказы,
              а <strong>печать этикеток маркировки</strong> приходится повторять заново.
              По статистике, 80% проблем связаны с тремя причинами: качество печати,
              размер кода и настройки сканера.
            </p>
          </div>

          {/* Problem Categories */}
          <div className="space-y-6 mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Три главные причины проблем
            </h2>

            <ProblemCard
              icon={Printer}
              title="1. Качество печати"
              color="red"
              problems={[
                "Дешёвые этикетки с плохой адгезией",
                "Изношенный риббон (термотрансферная лента)",
                "Принтер с разрешением ниже 203 dpi",
                "Размытые контуры L-паттерна DataMatrix",
                "Низкая контрастность (код сливается с фоном)",
              ]}
              solutions={[
                "Используйте термотрансферные этикетки (полуглянец/мат)",
                "Меняйте риббон каждые 3-5 рулонов этикеток",
                "Принтер минимум 203 dpi, рекомендуется 300 dpi",
                "Проверяйте чёткость L-паттерна визуально",
                "KleyKod проверяет контрастность автоматически (мин. 80%)",
              ]}
            />

            <ProblemCard
              icon={ScanLine}
              title="2. Размер DataMatrix"
              color="amber"
              problems={[
                "Код меньше 10×10 мм — сканер считывает нестабильно",
                "Код 15×15 мм — требует повторного сканирования",
                "Нарушены требования Честного Знака",
                "Quiet zone (тихая зона) вокруг кода слишком мала",
              ]}
              solutions={[
                "Минимальный размер по ЧЗ — 22×22 мм",
                "KleyKod автоматически проверяет размер при генерации",
                "Оставляйте тихую зону минимум 2 мм вокруг кода",
                "Используйте этикетки 58×40 мм или больше",
              ]}
            />

            <ProblemCard
              icon={Settings}
              title="3. Настройки оборудования"
              color="blue"
              problems={[
                "Линейный лазерный сканер (читает только EAN-13)",
                "Сканер в режиме эмуляции клавиатуры",
                "ПО не разбирает код на компоненты (GTIN, серийник)",
                "1С или касса неправильно настроены",
              ]}
              solutions={[
                "Используйте 2D-сканер (имиджер) с поддержкой DataMatrix",
                "Переключите сканер в режим COM-порта",
                "Настройте парсинг кода в учётной системе",
                "Проверьте полный код включая символы GS и крипто-хвост",
              ]}
            />
          </div>

          {/* SEO Text Block 2 */}
          <div className="bg-warm-gray-50 border border-warm-gray-200 rounded-2xl p-6 mb-10">
            <h2 className="text-xl font-bold text-warm-gray-900 mb-4">
              Почему не читается маркировка Честный Знак?
            </h2>
            <p className="text-warm-gray-600 leading-relaxed mb-4">
              <strong>Честный знак не читается код</strong> чаще всего из-за ошибок
              в структуре GS1 DataMatrix. Визуально код выглядит нормально, но внутри
              нарушена последовательность данных:
            </p>
            <ul className="space-y-2 text-warm-gray-600">
              <li className="flex items-start gap-2">
                <ChevronRight className="w-4 h-4 text-warm-gray-400 mt-1 flex-shrink-0" />
                <span>
                  <strong>FNC1</strong> — специальный символ в начале кода. Если его нет
                  или заменён на текст «FNC1» (4 буквы вместо 1 символа) — код не валиден.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight className="w-4 h-4 text-warm-gray-400 mt-1 flex-shrink-0" />
                <span>
                  <strong>GS-разделители</strong> — отделяют поля в коде. Нельзя ставить
                  после GTIN (поле 01) или заменять на текст «GS».
                </span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight className="w-4 h-4 text-warm-gray-400 mt-1 flex-shrink-0" />
                <span>
                  <strong>Крипто-хвост</strong> — последняя часть кода (91 и 92 поля).
                  Если обрезан или повреждён — верификация не пройдёт.
                </span>
              </li>
            </ul>
          </div>

          {/* Minimum Requirements Table */}
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Минимальные требования для печати
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse bg-white rounded-xl overflow-hidden shadow-sm">
                <thead>
                  <tr className="bg-warm-gray-100">
                    <th className="text-left p-4 font-semibold text-warm-gray-700">
                      Параметр
                    </th>
                    <th className="text-left p-4 font-semibold text-warm-gray-700">
                      Минимум
                    </th>
                    <th className="text-left p-4 font-semibold text-warm-gray-700">
                      Рекомендация
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-gray-100">
                  <tr>
                    <td className="p-4 text-warm-gray-600">Размер DataMatrix</td>
                    <td className="p-4 text-warm-gray-900 font-medium">22×22 мм</td>
                    <td className="p-4 text-emerald-600">25×25 мм</td>
                  </tr>
                  <tr className="bg-warm-gray-50">
                    <td className="p-4 text-warm-gray-600">Разрешение принтера</td>
                    <td className="p-4 text-warm-gray-900 font-medium">203 dpi</td>
                    <td className="p-4 text-emerald-600">300 dpi</td>
                  </tr>
                  <tr>
                    <td className="p-4 text-warm-gray-600">Контрастность</td>
                    <td className="p-4 text-warm-gray-900 font-medium">80%</td>
                    <td className="p-4 text-emerald-600">90%+</td>
                  </tr>
                  <tr className="bg-warm-gray-50">
                    <td className="p-4 text-warm-gray-600">Тихая зона</td>
                    <td className="p-4 text-warm-gray-900 font-medium">1 мм</td>
                    <td className="p-4 text-emerald-600">2-3 мм</td>
                  </tr>
                  <tr>
                    <td className="p-4 text-warm-gray-600">Тип сканера</td>
                    <td className="p-4 text-warm-gray-900 font-medium">2D имиджер</td>
                    <td className="p-4 text-emerald-600">2D имиджер с автофокусом</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* FAQ Section */}
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-warm-gray-900 mb-6">
              Частые вопросы
            </h2>
            <div className="space-y-4">
              {[
                {
                  q: "Почему лазерный сканер не читает DataMatrix?",
                  a: "Лазерные сканеры работают только с линейными штрихкодами (EAN-13, Code-128). DataMatrix — двумерный код, для него нужен 2D-сканер (имиджер), который делает «фото» кода и распознаёт его.",
                },
                {
                  q: "Код сканируется, но Честный Знак его не принимает. Почему?",
                  a: "Скорее всего проблема в структуре кода: отсутствует символ FNC1, неправильно расставлены GS-разделители или повреждён крипто-хвост. Проверьте полный код, включая все служебные символы.",
                },
                {
                  q: "Можно ли печатать DataMatrix на обычном офисном принтере?",
                  a: "Технически можно, но качество будет нестабильным. Лазерные принтеры дают 600 dpi, но тонер может смазываться. Струйные — расплываются на обычной бумаге. Рекомендуем термопринтер от 203 dpi.",
                },
                {
                  q: "Как проверить качество кода перед печатью?",
                  a: "KleyKod автоматически проверяет размер DataMatrix (минимум 22×22 мм) и контрастность (минимум 80%) при генерации этикеток. Если код не проходит проверку — система предупредит.",
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

          {/* CTA Section */}
          <section className="bg-gradient-to-br from-emerald-600 to-teal-600 rounded-2xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-3">
              Проверяйте коды до печати
            </h2>
            <p className="text-emerald-100 mb-6 max-w-lg mx-auto">
              KleyKod автоматически проверяет размер DataMatrix и контрастность.
              Если код не соответствует требованиям ЧЗ — система предупредит до печати.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-emerald-700 rounded-xl font-semibold hover:bg-emerald-50 transition-colors shadow-lg"
              >
                <CheckCircle2 className="w-5 h-5" />
                Создать этикетки с проверкой
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
              50 этикеток в день — бесплатно, без регистрации карты
            </p>
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
                  Выгрузка файла с баркодами из личного кабинета Wildberries
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
                  Пошаговая инструкция по заказу и скачиванию кодов
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
