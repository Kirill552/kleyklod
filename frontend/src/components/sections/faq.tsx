"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, MessageCircle } from "lucide-react";

const faqs = [
  {
    question: "Можно ли клеить код Честного Знака и штрихкод WB на одной этикетке?",
    answer: "Да, это полностью легально и соответствует требованиям Wildberries. Главное условие — DataMatrix и штрихкод не должны перекрываться, оба должны читаться сканером. KleyKod автоматически размещает коды маркировки с соблюдением всех требований.",
  },
  {
    question: "Какой размер этикетки для Честного Знака поддерживается?",
    answer: "Основной размер этикетки — 58×40 мм (стандарт термопринтеров для WB и Ozon). Также поддерживаем шаблоны 58×30 мм и 58×60 мм. Все этикетки генерируются с разрешением 203 DPI — требование для сканирования DataMatrix.",
  },
  {
    question: "Как распечатать этикетку Честный Знак?",
    answer: "Загрузите PDF от Wildberries и CSV с кодами маркировки → KleyKod объединит их на одной этикетке 58x40 → Скачайте готовый PDF для термопринтера (Xprinter, TSC, Godex). Печать 1000 этикеток занимает 5 секунд.",
  },
  {
    question: "Чем KleyKod лучше wbarcode и wbcon?",
    answer: "KleyKod — бесплатная альтернатива wbarcode с прозрачными ценами. В отличие от wbcon, мы проверяем качество DataMatrix до печати (Pre-flight проверка). Генератор этикеток работает онлайн, без установки программ.",
  },
  {
    question: "Какой штраф за отсутствие маркировки Честный Знак?",
    answer: "Штраф за нарушение маркировки: до 300,000₽ для ИП, до 1,000,000₽ для юрлиц. Товар без читаемого DataMatrix возвращается с FBS. KleyKod проверяет код маркировки до печати — гарантируем прохождение сканера WB.",
  },
  {
    question: "Можно ли создать этикетку для маркетплейса бесплатно?",
    answer: "Да! Бесплатный тариф — 50 этикеток в день навсегда. Генератор этикеток для Wildberries и Ozon работает онлайн. Для FBS селлеров с небольшими объёмами этого достаточно.",
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className="section" id="faq">
      <div className="container mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Левая часть — заголовок */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="lg:sticky lg:top-24"
          >
            <span className="inline-block px-4 py-1.5 bg-emerald-100 text-emerald-600 rounded-full text-sm font-medium mb-4">
              FAQ
            </span>
            <h2 className="heading-2 text-warm-gray-900 mb-4">
              Вопросы о маркировке WB и Честный Знак
            </h2>
            <p className="text-warm-gray-500 text-lg mb-8">
              Ответы на частые вопросы селлеров о печати этикеток и кодах маркировки
            </p>

            <a
              href="https://t.me/kleykod_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#0088cc] hover:bg-[#007bb5] text-white rounded-xl font-medium transition-colors"
            >
              <MessageCircle className="w-5 h-5" />
              Написать в Telegram
            </a>
          </motion.div>

          {/* Правая часть — аккордеон */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="space-y-4"
          >
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                className="sticker overflow-hidden"
              >
                <button
                  onClick={() => setOpenIndex(openIndex === index ? null : index)}
                  className="w-full p-5 text-left flex items-center justify-between gap-4"
                >
                  <span className="font-medium text-warm-gray-800">
                    {faq.question}
                  </span>
                  <motion.div
                    animate={{ rotate: openIndex === index ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex-shrink-0"
                  >
                    <ChevronDown className="w-5 h-5 text-warm-gray-400" />
                  </motion.div>
                </button>

                <AnimatePresence>
                  {openIndex === index && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="px-5 pb-5 text-warm-gray-600">
                        {faq.answer}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
