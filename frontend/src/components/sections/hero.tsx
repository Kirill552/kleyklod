"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, Sparkles, ArrowRight, Check } from "lucide-react";

export function Hero() {
  const [files, setFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(acceptedFiles);
    setIsProcessing(true);

    // Имитация обработки
    setTimeout(() => {
      setIsProcessing(false);
      setIsComplete(true);
    }, 2000);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
    },
    maxFiles: 1,
  });

  const resetDemo = () => {
    setFiles([]);
    setIsProcessing(false);
    setIsComplete(false);
  };

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
                Печать для термопринтера за 5 секунд.
              </span>
            </p>

            {/* Преимущества */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              {[
                "Печать 1000 этикеток за 5 сек",
                "Pre-flight проверка DataMatrix",
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
              <button className="btn-primary flex items-center justify-center gap-2 text-lg">
                Попробовать бесплатно
                <ArrowRight className="w-5 h-5" />
              </button>
              <button className="btn-secondary flex items-center justify-center gap-2">
                Смотреть демо
              </button>
            </motion.div>
          </motion.div>

          {/* Правая часть — интерактивная демо-зона */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="relative"
          >
            {/* Карточка демо */}
            <div className="sticker p-8 relative">
              {/* Заголовок демо */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-semibold text-warm-gray-700">
                  Попробуй прямо сейчас
                </h3>
                {isComplete && (
                  <button
                    onClick={resetDemo}
                    className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                  >
                    Сбросить
                  </button>
                )}
              </div>

              {/* Dropzone */}
              <AnimatePresence mode="wait">
                {!isComplete ? (
                  <motion.div
                    key="dropzone"
                    initial={{ opacity: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                  >
                    <div
                      {...getRootProps()}
                      className={`
                        dropzone p-8 cursor-pointer text-center
                        ${isDragActive ? "dropzone-active" : ""}
                      `}
                    >
                      <input {...getInputProps()} />

                      {isProcessing ? (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="flex flex-col items-center"
                        >
                          <div className="w-16 h-16 border-4 border-emerald-200 border-t-emerald-500 rounded-full animate-spin mb-4" />
                          <p className="text-warm-gray-600 font-medium">
                            Обрабатываем...
                          </p>
                          <p className="text-sm text-warm-gray-400 mt-1">
                            Проверяем DPI и контрастность
                          </p>
                        </motion.div>
                      ) : (
                        <>
                          <motion.div
                            animate={isDragActive ? { scale: 1.1 } : { scale: 1 }}
                            className="w-16 h-16 mx-auto mb-4 bg-emerald-100 rounded-2xl flex items-center justify-center"
                          >
                            <Upload className="w-8 h-8 text-emerald-600" />
                          </motion.div>
                          <p className="text-warm-gray-700 font-medium mb-2">
                            {isDragActive
                              ? "Отпустите файл"
                              : "Перетащите PDF от Wildberries"}
                          </p>
                          <p className="text-sm text-warm-gray-400">
                            или нажмите для выбора файла
                          </p>
                        </>
                      )}
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="result"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-emerald-50 rounded-2xl p-8 text-center"
                  >
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                      className="w-16 h-16 mx-auto mb-4 bg-emerald-500 rounded-full flex items-center justify-center"
                    >
                      <Check className="w-8 h-8 text-white" />
                    </motion.div>
                    <h4 className="text-lg font-semibold text-warm-gray-800 mb-2">
                      Готово!
                    </h4>
                    <p className="text-warm-gray-600 mb-4">
                      Этикетки объединены и проверены
                    </p>
                    <button className="btn-primary">
                      Скачать PDF
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Индикатор безопасности */}
              <div className="mt-6 flex items-center justify-center gap-2 text-sm text-warm-gray-400">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                Pre-flight проверка включена
              </div>
            </div>

            {/* Плавающие стикеры-этикетки */}
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -top-4 -right-4 w-24 h-16 bg-white rounded-lg shadow-lg border-2 border-dashed border-warm-gray-200 flex items-center justify-center"
            >
              <div className="text-center">
                <div className="w-8 h-8 mx-auto bg-warm-gray-200 rounded" />
                <p className="text-[8px] text-warm-gray-400 mt-1">WB</p>
              </div>
            </motion.div>

            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
              className="absolute -bottom-4 -left-4 w-24 h-16 bg-white rounded-lg shadow-lg border-2 border-dashed border-warm-gray-200 flex items-center justify-center"
            >
              <div className="text-center">
                <div className="w-8 h-8 mx-auto bg-emerald-200 rounded" />
                <p className="text-[8px] text-emerald-600 mt-1">ЧЗ</p>
              </div>
            </motion.div>
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
            { value: "5 сек", label: "Печать 1000 этикеток 58x40" },
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
