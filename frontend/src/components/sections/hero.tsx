"use client";

import { useCallback } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Check } from "lucide-react";
import { DemoDropzone } from "@/components/landing";

export function Hero() {
  const handleLoginClick = useCallback(() => {
    window.location.href = "/login";
  }, []);

  return (
    <section className="min-h-screen flex items-center py-16 md:py-20">
      <div className="container mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Левая часть — текст */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* Заголовок */}
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-warm-gray-900 mb-6 leading-tight">
              Этикетка WB + Честный Знак
              <span className="block text-emerald-700">в одной наклейке</span>
            </h1>

            {/* Подзаголовок */}
            <p className="text-lg md:text-xl text-warm-gray-600 mb-8 max-w-lg">
              Загрузите Excel из кабинета Wildberries и PDF с кодами маркировки —
              получите готовый файл для печати на термопринтере 58×40 мм
            </p>

            {/* Преимущества */}
            <div className="flex flex-col gap-3 mb-8">
              {[
                "Автоматический матчинг по штрихкоду",
                "Проверка качества DataMatrix",
                "50 этикеток бесплатно каждый месяц",
              ].map((text, i) => (
                <motion.div
                  key={text}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.1 }}
                  className="flex items-center gap-3 text-warm-gray-700"
                >
                  <div className="w-5 h-5 rounded bg-emerald-100 border border-emerald-600 flex items-center justify-center flex-shrink-0">
                    <Check className="w-3 h-3 text-emerald-600" />
                  </div>
                  <span className="font-medium">{text}</span>
                </motion.div>
              ))}
            </div>

            {/* Кнопка */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
            >
              <a
                href="/app"
                className="inline-flex items-center gap-2 px-8 py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-lg rounded-lg border-2 border-emerald-800 shadow-[3px_3px_0px_#065F46] hover:shadow-[1px_1px_0px_#065F46] hover:translate-x-[2px] hover:translate-y-[2px] transition-all duration-150"
              >
                Попробовать бесплатно
                <ArrowRight className="w-5 h-5" />
              </a>
            </motion.div>
          </motion.div>

          {/* Правая часть — визуальная трансформация + демо */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="relative"
          >
            {/* Визуализация трансформации */}
            <div className="mb-6">
              <div className="flex items-center justify-center gap-4 mb-4">
                {/* WB этикетка */}
                <div className="relative">
                  <div className="w-20 h-28 bg-white border-2 border-warm-gray-300 rounded-lg shadow-[2px_2px_0px_#D6D3D1] p-2 flex flex-col items-center justify-center">
                    <div className="w-12 h-12 bg-warm-gray-200 rounded mb-1" />
                    <div className="w-10 h-1.5 bg-warm-gray-300 rounded mb-1" />
                    <div className="w-8 h-1 bg-warm-gray-200 rounded" />
                  </div>
                  <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-warm-gray-500 whitespace-nowrap">
                    WB этикетка
                  </span>
                </div>

                {/* Плюс */}
                <span className="text-2xl font-bold text-warm-gray-400 mb-6">+</span>

                {/* ЧЗ код */}
                <div className="relative">
                  <div className="w-20 h-28 bg-white border-2 border-warm-gray-300 rounded-lg shadow-[2px_2px_0px_#D6D3D1] p-2 flex flex-col items-center justify-center">
                    <div className="w-12 h-12 bg-emerald-100 rounded mb-1 flex items-center justify-center">
                      <div className="w-8 h-8 bg-emerald-200 rounded-sm" />
                    </div>
                    <div className="w-10 h-1 bg-warm-gray-200 rounded" />
                  </div>
                  <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-warm-gray-500 whitespace-nowrap">
                    Код ЧЗ
                  </span>
                </div>

                {/* Стрелка */}
                <span className="text-2xl font-bold text-emerald-600 mb-6">→</span>

                {/* Готовая наклейка */}
                <div className="relative">
                  <div className="w-24 h-32 bg-white border-2 border-emerald-600 rounded-lg shadow-[3px_3px_0px_#047857] p-2 flex flex-col items-center justify-center">
                    {/* Перфорация */}
                    <div className="absolute top-0 left-3 right-3 border-t-2 border-dashed border-warm-gray-300" />
                    <div className="w-10 h-10 bg-warm-gray-200 rounded mb-1" />
                    <div className="w-8 h-8 bg-emerald-200 rounded-sm mb-1" />
                    <div className="w-12 h-1.5 bg-warm-gray-300 rounded" />
                  </div>
                  <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-semibold text-emerald-700 whitespace-nowrap">
                    58×40 мм
                  </span>
                </div>
              </div>
            </div>

            {/* Демо-зона */}
            <div className="mt-10">
              <DemoDropzone onLoginClick={handleLoginClick} />
            </div>
          </motion.div>
        </div>

        {/* Статистика внизу */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="mt-16 grid grid-cols-3 gap-8 max-w-2xl mx-auto"
        >
          {[
            { value: "7 000+", label: "селлеров" },
            { value: "99.9%", label: "кодов проходят сканер" },
            { value: "50 шт", label: "бесплатно в месяц" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-warm-gray-800">
                {stat.value}
              </div>
              <div className="text-sm text-warm-gray-500">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
