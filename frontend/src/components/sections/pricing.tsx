"use client";

import { motion } from "framer-motion";

const plans = [
  {
    name: "Старт",
    price: "0",
    period: "",
    limit: "50 этикеток/мес",
    features: [
      "Объединение WB + Честный Знак",
      "Проверка качества DataMatrix",
      "Скачивание PDF",
    ],
    cta: "Начать бесплатно",
    href: "/app",
    popular: false,
  },
  {
    name: "Про",
    price: "490",
    period: "/мес",
    limit: "500 этикеток/мес",
    features: [
      "Всё из тарифа Старт",
      "Накопление до 10 000 шт",
      "База товаров (100 карточек)",
      "История генераций",
      "Telegram-бот",
    ],
    cta: "Подключить",
    href: "/app",
    popular: true,
  },
  {
    name: "Бизнес",
    price: "1 990",
    period: "/мес",
    limit: "Безлимит",
    features: [
      "Всё из тарифа Про",
      "API для автоматизации",
      "Интеграция с WB API",
      "Приоритетная поддержка",
    ],
    cta: "Связаться",
    href: "https://t.me/kleykod_support",
    external: true,
    popular: false,
  },
];

export function Pricing() {
  return (
    <section className="py-20 bg-white" id="pricing">
      <div className="container mx-auto px-6">
        {/* Заголовок */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-warm-gray-900 mb-4">
            Тарифы
          </h2>
          <p className="text-warm-gray-600 max-w-xl mx-auto">
            Лимиты накапливаются — неиспользованные этикетки переносятся на следующий месяц
          </p>
        </motion.div>

        {/* Карточки тарифов */}
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto items-start">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: index * 0.1 }}
              className={`relative ${plan.popular ? "md:scale-105 md:z-10" : ""}`}
            >
              <div
                className={`h-full flex flex-col p-6 rounded-xl border-2 ${
                  plan.popular
                    ? "border-emerald-600 shadow-[4px_4px_0px_#047857] bg-white"
                    : "border-warm-gray-200 shadow-[2px_2px_0px_#E7E5E4] bg-white"
                }`}
              >
                {/* Название + бейдж */}
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-xl font-bold text-warm-gray-800">
                    {plan.name}
                  </h3>
                  {plan.popular && (
                    <span className="bg-emerald-600 text-white text-xs font-semibold px-2 py-0.5 rounded">
                      Популярный
                    </span>
                  )}
                </div>

                {/* Цена */}
                <div className="mb-2">
                  <span className="text-4xl font-bold text-warm-gray-900">
                    {plan.price}
                  </span>
                  <span className="text-lg text-warm-gray-500">
                    {" "}₽{plan.period}
                  </span>
                </div>

                {/* Лимит */}
                <div className="text-sm font-medium text-emerald-700 mb-6">
                  {plan.limit}
                </div>

                {/* Фичи */}
                <ul className="flex-grow space-y-2 mb-6">
                  {plan.features.map((feature) => (
                    <li
                      key={feature}
                      className="flex items-start gap-2 text-warm-gray-600 text-sm"
                    >
                      <span className="text-emerald-600 font-medium">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                <a
                  href={plan.href}
                  target={plan.external ? "_blank" : undefined}
                  rel={plan.external ? "noopener noreferrer" : undefined}
                  className={`w-full py-3 rounded-lg font-semibold text-center block transition-all duration-150 ${
                    plan.popular
                      ? "bg-emerald-600 hover:bg-emerald-700 text-white border-2 border-emerald-800 shadow-[2px_2px_0px_#065F46] hover:shadow-[1px_1px_0px_#065F46] hover:translate-x-[1px] hover:translate-y-[1px]"
                      : plan.name === "Бизнес"
                        ? "bg-amber-500 hover:bg-amber-600 text-white border-2 border-amber-700 shadow-[2px_2px_0px_#B45309] hover:shadow-[1px_1px_0px_#B45309] hover:translate-x-[1px] hover:translate-y-[1px]"
                        : "bg-warm-gray-100 hover:bg-warm-gray-200 text-warm-gray-700 border-2 border-warm-gray-300"
                  }`}
                >
                  {plan.cta}
                </a>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
