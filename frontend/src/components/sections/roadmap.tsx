"use client";

import { motion } from "framer-motion";
import {
  FileSpreadsheet,
  Link2,
  FileSearch,
  Wrench,
  Check,
  Bot,
  CreditCard,
  Database,
  Shield,
  Smartphone,
  Clock,
} from "lucide-react";

interface RoadmapItem {
  icon: React.ElementType;
  title: string;
  description: string;
}

const doneItems: RoadmapItem[] = [
  {
    icon: Check,
    title: "Генератор этикеток 58x40",
    description: "Объединение WB штрихкодов и DataMatrix Честного Знака",
  },
  {
    icon: FileSpreadsheet,
    title: "Excel режим",
    description: "Загрузка баркодов напрямую из Excel файла Wildberries",
  },
  {
    icon: Bot,
    title: "Telegram бот",
    description: "Генерация этикеток прямо в Telegram без регистрации",
  },
  {
    icon: CreditCard,
    title: "PRO тарифы",
    description: "Расширенные лимиты для активных продавцов",
  },
  {
    icon: Database,
    title: "База карточек товаров",
    description: "Сохранение данных товаров для быстрой генерации",
  },
  {
    icon: Shield,
    title: "Preflight проверка",
    description: "Валидация качества DataMatrix до печати",
  },
];

const plannedItems: RoadmapItem[] = [
  {
    icon: Link2,
    title: "WB API интеграция",
    description: "Автоматическое получение баркодов из личного кабинета Wildberries",
  },
  {
    icon: FileSearch,
    title: "Трекер УПД",
    description: "Отслеживание статусов документов в Честном Знаке",
  },
  {
    icon: Smartphone,
    title: "Мобильное приложение",
    description: "Генерация этикеток с телефона на складе",
  },
];

export function Roadmap() {
  return (
    <section className="section bg-warm-gray-50" id="roadmap">
      <div className="container mx-auto px-6">
        {/* Заголовок секции */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 bg-blue-100 text-blue-600 rounded-full text-sm font-medium mb-4">
            <Wrench className="w-4 h-4 inline mr-1" />
            Развитие продукта
          </span>
          <h2 className="heading-2 text-warm-gray-900 mb-4">
            Что мы <span className="gradient-text">уже сделали</span> и что{" "}
            <span className="gradient-text">планируем</span>
          </h2>
          <p className="text-warm-gray-500 max-w-2xl mx-auto text-lg">
            Наша команда постоянно работает над новыми функциями, чтобы упростить
            работу селлеров с маркировкой
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 max-w-6xl mx-auto">
          {/* Секция "Сделано" */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center">
                <Check className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-warm-gray-900">Сделано</h3>
                <p className="text-sm text-warm-gray-500">
                  {doneItems.length} функций в продакшене
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {doneItems.map((item, index) => {
                const Icon = item.icon;
                return (
                  <motion.div
                    key={item.title}
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.05, duration: 0.3 }}
                    className="sticker p-4 hover:shadow-md transition-shadow border-l-4 border-l-emerald-500"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                        <Icon className="w-4 h-4 text-emerald-600" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h4 className="font-semibold text-warm-gray-900 text-sm">
                          {item.title}
                        </h4>
                        <p className="text-warm-gray-500 text-xs mt-0.5">
                          {item.description}
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                          <Check className="w-3 h-3 mr-1" />
                          Готово
                        </span>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>

          {/* Секция "Планируется" */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-blue-500 flex items-center justify-center">
                <Clock className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-warm-gray-900">Планируется</h3>
                <p className="text-sm text-warm-gray-500">
                  {plannedItems.length} функции в разработке
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {plannedItems.map((item, index) => {
                const Icon = item.icon;
                return (
                  <motion.div
                    key={item.title}
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.05, duration: 0.3 }}
                    className="sticker p-4 hover:shadow-md transition-shadow border-l-4 border-l-blue-500"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                        <Icon className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h4 className="font-semibold text-warm-gray-900 text-sm">
                          {item.title}
                        </h4>
                        <p className="text-warm-gray-500 text-xs mt-0.5">
                          {item.description}
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                          2026
                        </span>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Дополнительный блок с призывом */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
              className="mt-6 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border border-blue-100"
            >
              <p className="text-sm text-warm-gray-600 text-center">
                Есть идея для новой функции?{" "}
                <a
                  href="https://vk.ru/kleykod"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 underline underline-offset-2 font-medium"
                >
                  Напишите нам
                </a>
              </p>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
