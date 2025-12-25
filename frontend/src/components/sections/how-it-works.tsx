"use client";

import { motion } from "framer-motion";
import { FileUp, Cpu, Download, ArrowRight } from "lucide-react";

const steps = [
  {
    number: "01",
    icon: FileUp,
    title: "Загрузите файлы",
    description: "Перетащите PDF со штрихкодами Wildberries и CSV с кодами маркировки Честного Знака",
    details: ["PDF этикетки WB", "CSV DataMatrix коды"],
  },
  {
    number: "02",
    icon: Cpu,
    title: "Генератор объединяет коды",
    description: "Система склеивает штрихкод WB и DataMatrix ЧЗ, проверяет качество для сканера",
    details: ["Объединение кодов", "Pre-flight проверка"],
  },
  {
    number: "03",
    icon: Download,
    title: "Печать этикеток 58x40",
    description: "Скачайте готовый PDF для термопринтера. Печатайте на Xprinter, TSC, Godex",
    details: ["Шаблон 58×40мм", "203 DPI для WB"],
  },
];

export function HowItWorks() {
  return (
    <section className="section section-alt" id="how-it-works">
      <div className="container mx-auto px-6">
        {/* Заголовок */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 bg-emerald-100 text-emerald-600 rounded-full text-sm font-medium mb-4">
            Как распечатать этикетку Честный Знак
          </span>
          <h2 className="heading-2 text-warm-gray-900 mb-4">
            Печать этикеток для Wildberries
          </h2>
          <p className="text-warm-gray-500 max-w-2xl mx-auto text-lg">
            Три шага: объединить штрихкод WB и код маркировки на одной этикетке 58x40
          </p>
        </motion.div>

        {/* Шаги */}
        <div className="relative">
          {/* Линия соединения */}
          <div className="hidden lg:block absolute top-24 left-[16.666%] right-[16.666%] h-0.5 bg-gradient-to-r from-emerald-200 via-emerald-300 to-emerald-200" />

          <div className="grid lg:grid-cols-3 gap-8">
            {steps.map((step, index) => {
              const Icon = step.icon;

              return (
                <motion.div
                  key={step.number}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ delay: index * 0.2, duration: 0.5 }}
                  className="relative"
                >
                  {/* Стрелка между шагами на мобильных */}
                  {index < steps.length - 1 && (
                    <div className="lg:hidden flex justify-center my-4">
                      <ArrowRight className="w-6 h-6 text-emerald-300 rotate-90" />
                    </div>
                  )}

                  <div className="sticker p-6 text-center relative">
                    {/* Номер шага */}
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg z-10">
                      {index + 1}
                    </div>

                    {/* Иконка */}
                    <div className="w-20 h-20 mx-auto mt-4 mb-6 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-2xl flex items-center justify-center">
                      <Icon className="w-10 h-10 text-emerald-600" />
                    </div>

                    {/* Контент */}
                    <h3 className="heading-3 text-warm-gray-800 mb-3">
                      {step.title}
                    </h3>
                    <p className="text-warm-gray-500 mb-4">
                      {step.description}
                    </p>

                    {/* Детали */}
                    <div className="flex justify-center gap-2 flex-wrap">
                      {step.details.map((detail) => (
                        <span
                          key={detail}
                          className="px-3 py-1 bg-warm-gray-100 text-warm-gray-600 rounded-full text-sm"
                        >
                          {detail}
                        </span>
                      ))}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Визуализация процесса */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="mt-16"
        >
          <div className="sticker p-8 bg-gradient-to-br from-warm-gray-50 to-white">
            <div className="flex flex-col md:flex-row items-center justify-center gap-8">
              {/* Входные файлы */}
              <div className="flex gap-4">
                {/* PDF WB */}
                <motion.div
                  whileHover={{ scale: 1.05, rotate: -2 }}
                  className="w-24 h-32 bg-white rounded-lg shadow-lg border-2 border-warm-gray-200 p-3 flex flex-col items-center justify-center"
                >
                  <div className="w-full h-16 bg-warm-gray-200 rounded mb-2" />
                  <span className="text-xs text-warm-gray-500 font-medium">PDF WB</span>
                </motion.div>

                {/* CSV ЧЗ */}
                <motion.div
                  whileHover={{ scale: 1.05, rotate: 2 }}
                  className="w-24 h-32 bg-white rounded-lg shadow-lg border-2 border-emerald-200 p-3 flex flex-col items-center justify-center"
                >
                  <div className="w-full h-16 bg-emerald-100 rounded mb-2 flex items-center justify-center">
                    <div className="space-y-1">
                      <div className="w-12 h-1 bg-emerald-300 rounded" />
                      <div className="w-10 h-1 bg-emerald-300 rounded" />
                      <div className="w-14 h-1 bg-emerald-300 rounded" />
                    </div>
                  </div>
                  <span className="text-xs text-emerald-600 font-medium">CSV ЧЗ</span>
                </motion.div>
              </div>

              {/* Стрелка */}
              <motion.div
                animate={{ x: [0, 10, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="flex items-center gap-2"
              >
                <div className="w-16 h-0.5 bg-gradient-to-r from-warm-gray-300 to-emerald-400" />
                <ArrowRight className="w-6 h-6 text-emerald-500" />
              </motion.div>

              {/* Результат */}
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="w-40 h-28 bg-white rounded-lg shadow-xl border-2 border-emerald-400 p-4 relative"
              >
                {/* Перфорация сверху */}
                <div className="absolute -top-1 left-2 right-2 h-2 flex justify-around">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="w-1 h-full bg-warm-gray-200 rounded-full" />
                  ))}
                </div>

                <div className="flex gap-3 h-full">
                  {/* WB код */}
                  <div className="flex-1 bg-warm-gray-100 rounded flex items-center justify-center">
                    <div className="w-full h-8 mx-1 bg-warm-gray-300 rounded" />
                  </div>
                  {/* DataMatrix */}
                  <div className="w-12 h-12 bg-emerald-200 rounded self-center" />
                </div>

                {/* Бейдж */}
                <div className="absolute -bottom-2 -right-2 px-2 py-0.5 bg-emerald-500 text-white text-xs font-bold rounded-full shadow">
                  58×40
                </div>
              </motion.div>
            </div>

            <p className="text-center text-warm-gray-500 mt-6 text-sm">
              Два файла на входе → Один готовый PDF на выходе
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
