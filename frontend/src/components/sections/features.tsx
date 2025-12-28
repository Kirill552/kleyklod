"use client";

import { motion } from "framer-motion";
import { Zap, Shield, Eye } from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Генератор этикеток онлайн",
    description: "Печать 1000 этикеток 58x40 за 5 секунд. wbcon и wbarcode обрабатывают заказ часами — мы делаем мгновенно.",
    metric: "5 сек",
    metricLabel: "печать 1000 этикеток",
    gradient: "from-amber-400 to-orange-500",
  },
  {
    icon: Shield,
    title: "Проверка качества DataMatrix",
    description: "Проверяем код маркировки Честного Знака ДО печати. Предупредим, если DataMatrix не пройдёт сканер WB.",
    metric: "99.9%",
    metricLabel: "кодов проходят приёмку",
    gradient: "from-emerald-400 to-teal-500",
  },
  {
    icon: Eye,
    title: "Бесплатно для селлеров",
    description: "Создать этикетку онлайн бесплатно — 50 штук в день навсегда. Прозрачные тарифы, дешевле wbarcode.",
    metric: "0 ₽",
    metricLabel: "50 этикеток/день бесплатно",
    gradient: "from-violet-400 to-purple-500",
  },
];

export function Features() {
  return (
    <section className="section" id="features">
      <div className="container mx-auto px-6">
        {/* Заголовок секции */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 bg-emerald-100 text-emerald-600 rounded-full text-sm font-medium mb-4">
            Генератор этикеток для маркетплейсов
          </span>
          <h2 className="heading-2 text-warm-gray-900 mb-4">
            Почему <span className="gradient-text">KleyKod</span>?
          </h2>
          <p className="text-warm-gray-500 max-w-2xl mx-auto text-lg">
            Три причины, по которым селлеры Wildberries выбирают нас вместо wbcon и wbarcode
          </p>
        </motion.div>

        {/* Карточки фичей */}
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;

            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: index * 0.15, duration: 0.5 }}
                className="group"
              >
                <div className="sticker p-8 h-full flex flex-col relative overflow-hidden">
                  {/* Градиентный фон при наведении */}
                  <div
                    className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`}
                  />

                  {/* Иконка */}
                  <div className="relative mb-6">
                    <div
                      className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center shadow-lg`}
                    >
                      <Icon className="w-7 h-7 text-white" />
                    </div>
                  </div>

                  {/* Метрика */}
                  <div className="mb-4">
                    <div className="text-4xl font-bold text-warm-gray-800">
                      {feature.metric}
                    </div>
                    <div className="text-sm text-warm-gray-400">
                      {feature.metricLabel}
                    </div>
                  </div>

                  {/* Заголовок и описание */}
                  <h3 className="heading-3 text-warm-gray-800 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-warm-gray-500 flex-grow">
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Дополнительный блок */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="mt-16 sticker p-8 md:p-12 bg-gradient-to-br from-emerald-50 to-white"
        >
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h3 className="heading-2 text-warm-gray-800 mb-4">
                Killer Feature: <br />
                <span className="text-emerald-600">Проверка качества</span>
              </h3>
              <p className="text-warm-gray-600 mb-6">
                Единственный сервис, который проверяет качество кодов до печати.
                Мы симулируем сканирование WB и предупреждаем о проблемах заранее.
              </p>
              <ul className="space-y-3">
                {[
                  "Проверка DPI ≥ 203",
                  "Контрастность ≥ 80%",
                  "Размер DataMatrix ≥ 22×22 мм",
                  "Зона покоя ≥ 3 мм",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-warm-gray-600">
                    <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                      <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Визуализация проверки */}
            <div className="relative">
              <div className="label-card p-6">
                <div className="flex gap-4 mb-4">
                  {/* WB штрихкод */}
                  <div className="flex-1 bg-warm-gray-100 rounded-lg p-4 flex flex-col items-center">
                    <div className="w-full h-12 bg-warm-gray-300 rounded mb-2" />
                    <span className="text-xs text-warm-gray-500">Штрихкод WB</span>
                  </div>
                  {/* DataMatrix */}
                  <div className="flex-1 bg-emerald-50 rounded-lg p-4 flex flex-col items-center">
                    <div className="w-12 h-12 bg-emerald-300 rounded mb-2" />
                    <span className="text-xs text-emerald-600">DataMatrix ЧЗ</span>
                  </div>
                </div>

                {/* Статус проверки */}
                <div className="bg-emerald-100 rounded-lg p-3 flex items-center gap-3">
                  <div className="w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center">
                    <Shield className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-emerald-700">
                      Проверка пройдена
                    </div>
                    <div className="text-xs text-emerald-600">
                      DPI: 203 • Контраст: 92% • Размер: OK
                    </div>
                  </div>
                </div>
              </div>

              {/* Декоративные элементы */}
              <div className="absolute -top-4 -right-4 w-8 h-8 bg-emerald-200 rounded-full opacity-50" />
              <div className="absolute -bottom-2 -left-2 w-6 h-6 bg-amber-200 rounded-full opacity-50" />
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
