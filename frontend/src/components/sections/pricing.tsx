"use client";

import { motion } from "framer-motion";
import { Check, Sparkles, Zap, Building2 } from "lucide-react";

const plans = [
  {
    name: "Старт",
    description: "Бесплатно навсегда",
    price: "0",
    period: "",
    icon: Sparkles,
    features: [
      "50 этикеток в месяц",
      "Объединение WB + Честный Знак",
      "Проверка качества DataMatrix",
      "Скачивание PDF для термопринтера",
      "Генерация из Excel с баркодами",
    ],
    limitations: [
      "Без сохранения истории",
    ],
    cta: "Начать бесплатно",
    popular: false,
    gradient: "from-warm-gray-100 to-warm-gray-50",
  },
  {
    name: "Про",
    description: "Для активных селлеров",
    price: "490",
    period: "в месяц",
    icon: Zap,
    features: [
      "2000 этикеток в месяц",
      "Накопление до 10 000 шт",
      "Генерация из Excel с баркодами",
      "Проверка качества DataMatrix",
      "История генераций 7 дней",
      "Telegram-бот генератор",
    ],
    limitations: [],
    cta: "Подключить Про",
    popular: true,
    gradient: "from-emerald-500 to-teal-500",
  },
  {
    name: "Бизнес",
    description: "Для крупных продавцов",
    price: "1990",
    period: "в месяц",
    icon: Building2,
    features: [
      "Безлимит этикеток",
      "Генерация из Excel с баркодами",
      "История генераций 30 дней",
      "API для автоматизации",
      "Интеграция с Wildberries",
      "Персональный менеджер",
    ],
    limitations: [],
    cta: "Связаться с нами",
    popular: false,
    gradient: "from-violet-500 to-purple-500",
  },
];

export function Pricing() {
  return (
    <section className="section section-alt" id="pricing">
      <div className="container mx-auto px-6">
        {/* Заголовок */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 bg-emerald-100 text-emerald-600 rounded-full text-sm font-medium mb-4">
            Тарифы генератора этикеток
          </span>
          <h2 className="heading-2 text-warm-gray-900 mb-4">
            Дешевле wbarcode и wbcon
          </h2>
          <p className="text-warm-gray-500 max-w-2xl mx-auto text-lg">
            50 этикеток в месяц бесплатно — навсегда.{" "}
            <span className="font-medium text-warm-gray-700">
              Тариф Про дешевле чашки кофе в месяц.
            </span>
          </p>
        </motion.div>

        {/* Карточки тарифов */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, index) => {
            const Icon = plan.icon;

            return (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: index * 0.15, duration: 0.5 }}
                className={`relative ${plan.popular ? "md:-mt-4 md:mb-4" : ""}`}
              >
                {/* Популярный бейдж */}
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10">
                    <span className="px-4 py-1 bg-emerald-500 text-white text-sm font-medium rounded-full shadow-lg">
                      Популярный
                    </span>
                  </div>
                )}

                <div
                  className={`sticker p-8 h-full flex flex-col ${
                    plan.popular
                      ? "ring-2 ring-emerald-500 ring-offset-4"
                      : ""
                  }`}
                >
                  {/* Иконка и название */}
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className={`w-12 h-12 rounded-xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center`}
                    >
                      <Icon className={`w-6 h-6 ${plan.popular ? "text-white" : "text-warm-gray-600"}`} />
                    </div>
                    <div>
                      <h3 className="font-bold text-xl text-warm-gray-800">
                        {plan.name}
                      </h3>
                      <p className="text-sm text-warm-gray-500">
                        {plan.description}
                      </p>
                    </div>
                  </div>

                  {/* Цена */}
                  <div className="mb-6">
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold text-warm-gray-900">
                        {plan.price}
                      </span>
                      <span className="text-lg text-warm-gray-500">₽</span>
                    </div>
                    <span className="text-sm text-warm-gray-500">
                      {plan.period}
                    </span>
                  </div>

                  {/* Фичи */}
                  <div className="flex-grow">
                    <ul className="space-y-3 mb-6">
                      {plan.features.map((feature) => (
                        <li
                          key={feature}
                          className="flex items-start gap-3 text-warm-gray-600"
                        >
                          <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Check className="w-3 h-3 text-emerald-600" />
                          </div>
                          <span className="text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    {/* Ограничения */}
                    {plan.limitations.length > 0 && (
                      <ul className="space-y-2 mb-6">
                        {plan.limitations.map((limitation) => (
                          <li
                            key={limitation}
                            className="flex items-start gap-3 text-warm-gray-500"
                          >
                            <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                              <div className="w-1 h-1 bg-warm-gray-300 rounded-full" />
                            </div>
                            <span className="text-sm">{limitation}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* CTA */}
                  <a
                    href={plan.name === "Бизнес" ? "https://vk.ru/kleykod" : "/app"}
                    target={plan.name === "Бизнес" ? "_blank" : undefined}
                    rel={plan.name === "Бизнес" ? "noopener noreferrer" : undefined}
                    className={`w-full py-3 rounded-xl font-semibold transition-all block text-center ${
                      plan.popular
                        ? "bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/20"
                        : "bg-warm-gray-100 hover:bg-warm-gray-200 text-warm-gray-700"
                    }`}
                  >
                    {plan.cta}
                  </a>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Дополнительная информация */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="mt-12 text-center"
        >
          <div className="inline-flex flex-wrap items-center justify-center gap-6 text-sm text-warm-gray-500">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-500" />
              Отмена в любой момент
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-500" />
              Без скрытых платежей
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-500" />
              Оплата картой через ЮКассу
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
