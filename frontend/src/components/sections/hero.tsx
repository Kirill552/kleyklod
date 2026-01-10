"use client";

import { useCallback } from "react";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Check } from "lucide-react";
import { DemoDropzone } from "@/components/landing";

export function Hero() {
  // Открытие Telegram Login
  const handleLoginClick = useCallback(() => {
    // Переход на страницу входа
    window.location.href = "/login";
  }, []);

  return (
    <section className="min-h-screen flex items-center py-20 relative overflow-hidden">
      {/* Декоративные элементы */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-emerald-200/30 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-amber-200/20 rounded-full blur-3xl" />

      <div className="container mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Левая часть — текст */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            {/* Бейдж */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium mb-6"
            >
              <Sparkles className="w-4 h-4" />
              Генератор этикеток для селлеров — 50 шт/день бесплатно
            </motion.div>

            {/* Заголовок */}
            <h1 className="heading-1 text-warm-gray-900 mb-6">
              <span className="block text-lg font-medium text-warm-gray-500 mb-2">Проблема 2 стикеров на товаре?</span>
              Две этикетки —{" "}
              <span className="gradient-text">один стикер</span>
            </h1>

            {/* Подзаголовок */}
            <p className="text-xl text-warm-gray-600 mb-8 max-w-lg text-balance">
              Объедините штрихкод Wildberries и DataMatrix Честного Знака на одной этикетке 58x40.{" "}
              <span className="font-semibold text-warm-gray-700">
                В 50 раз быстрее ручной работы.
              </span>
            </p>

            {/* Преимущества */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              {[
                "В 50× быстрее ручной работы",
                "Проверка качества DataMatrix",
                "Бесплатно для FBS селлеров",
              ].map((text, i) => (
                <motion.div
                  key={text}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + i * 0.1 }}
                  className="flex items-center gap-2 text-warm-gray-600"
                >
                  <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center">
                    <Check className="w-3 h-3 text-emerald-600" />
                  </div>
                  <span className="text-sm font-medium">{text}</span>
                </motion.div>
              ))}
            </div>

            {/* Кнопки */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="flex flex-col sm:flex-row gap-4"
            >
              <a href="/app" className="btn-primary flex items-center justify-center gap-2 text-lg">
                Попробовать бесплатно
                <ArrowRight className="w-5 h-5" />
              </a>
            </motion.div>
          </motion.div>

          {/* Правая часть — интерактивная демо-зона */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="relative"
            id="demo"
          >
            {/* Плавающие стикеры-этикетки */}
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -top-4 -right-4 w-24 h-16 bg-white rounded-lg shadow-lg border-2 border-dashed border-warm-gray-200 flex items-center justify-center z-10"
            >
              <div className="text-center">
                <div className="w-8 h-8 mx-auto bg-warm-gray-200 rounded" />
                <p className="text-[8px] text-warm-gray-400 mt-1">WB</p>
              </div>
            </motion.div>

            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
              className="absolute -bottom-4 -left-4 w-24 h-16 bg-white rounded-lg shadow-lg border-2 border-dashed border-warm-gray-200 flex items-center justify-center z-10"
            >
              <div className="text-center">
                <div className="w-8 h-8 mx-auto bg-emerald-200 rounded" />
                <p className="text-[8px] text-emerald-600 mt-1">ЧЗ</p>
              </div>
            </motion.div>

            {/* Демо-зона с анимацией */}
            <DemoDropzone onLoginClick={handleLoginClick} />
          </motion.div>
        </div>

        {/* Статистика внизу */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8"
        >
          {[
            { value: "7 000+", label: "Селлеров Wildberries" },
            { value: "50×", label: "Быстрее ручной работы" },
            { value: "99.9%", label: "Кодов проходят сканер WB" },
            { value: "0 ₽", label: "Бесплатно 50 шт/день" },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.1 + i * 0.1 }}
              className="text-center"
            >
              <div className="text-3xl font-bold text-warm-gray-800 mb-1">
                {stat.value}
              </div>
              <div className="text-sm text-warm-gray-500">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
