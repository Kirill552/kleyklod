"use client";

import { motion } from "framer-motion";
import { FileSpreadsheet, Link2, FileSearch, Wrench, Calendar, Check } from "lucide-react";

type RoadmapStatus = "done" | "in_progress" | "planned";

interface RoadmapItem {
  icon: React.ElementType;
  title: string;
  description: string;
  status: RoadmapStatus;
  quarter?: string;
}

const roadmapItems: RoadmapItem[] = [
  {
    icon: Check,
    title: "Генератор этикеток 58x40",
    description: "Объединение WB штрихкодов и DataMatrix Честного Знака",
    status: "done",
  },
  {
    icon: FileSpreadsheet,
    title: "Генерация из Excel",
    description: "Загружайте Excel с баркодами напрямую из WB",
    status: "done",
  },
  {
    icon: Link2,
    title: "Интеграция с WB API",
    description: "Автоматическое получение баркодов из личного кабинета",
    status: "planned",
    quarter: "Q1 2026",
  },
  {
    icon: FileSearch,
    title: "Трекер статуса УПД",
    description: "Отслеживание документов в Честном Знаке",
    status: "planned",
    quarter: "Q2 2026",
  },
];

const statusConfig: Record<RoadmapStatus, { label: string; color: string; bg: string }> = {
  done: {
    label: "Готово",
    color: "text-emerald-700",
    bg: "bg-emerald-100",
  },
  in_progress: {
    label: "В разработке",
    color: "text-amber-700",
    bg: "bg-amber-100",
  },
  planned: {
    label: "Планируется",
    color: "text-blue-700",
    bg: "bg-blue-100",
  },
};

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
            Что мы <span className="gradient-text">делаем дальше</span>
          </h2>
          <p className="text-warm-gray-500 max-w-2xl mx-auto text-lg">
            Наша команда постоянно работает над новыми функциями, чтобы упростить
            работу селлеров с маркировкой
          </p>
        </motion.div>

        {/* Таймлайн */}
        <div className="max-w-3xl mx-auto">
          <div className="relative">
            {/* Вертикальная линия */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-warm-gray-200" />

            {/* Элементы roadmap */}
            {roadmapItems.map((item, index) => {
              const Icon = item.icon;
              const config = statusConfig[item.status];

              return (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ delay: index * 0.1, duration: 0.4 }}
                  className="relative pl-20 pb-10 last:pb-0"
                >
                  {/* Иконка на линии */}
                  <div
                    className={`absolute left-4 w-8 h-8 rounded-full flex items-center justify-center ${
                      item.status === "done"
                        ? "bg-emerald-500"
                        : item.status === "in_progress"
                          ? "bg-amber-500"
                          : "bg-blue-500"
                    }`}
                  >
                    <Icon className="w-4 h-4 text-white" />
                  </div>

                  {/* Карточка */}
                  <div className="sticker p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-warm-gray-900 text-lg mb-1">
                          {item.title}
                        </h3>
                        <p className="text-warm-gray-600">
                          {item.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {item.quarter && (
                          <span className="flex items-center gap-1 text-sm text-warm-gray-500">
                            <Calendar className="w-4 h-4" />
                            {item.quarter}
                          </span>
                        )}
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color}`}
                        >
                          {config.label}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
          className="text-center mt-12"
        >
          <p className="text-warm-gray-500">
            Есть идея для новой функции?{" "}
            <a
              href="https://t.me/kleykod_support"
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-600 hover:text-emerald-700 underline underline-offset-2"
            >
              Напишите нам в Telegram
            </a>
          </p>
        </motion.div>
      </div>
    </section>
  );
}
