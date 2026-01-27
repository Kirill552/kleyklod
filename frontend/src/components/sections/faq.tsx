"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const faqs = [
  {
    question: "Можно ли клеить код ЧЗ и штрихкод WB на одной этикетке?",
    answer: "Да, это полностью легально. Главное — DataMatrix и штрихкод не должны перекрываться, оба должны читаться сканером. KleyKod автоматически размещает коды с соблюдением всех требований.",
  },
  {
    question: "Какой размер этикетки поддерживается?",
    answer: "Основной размер — 58×40 мм (стандарт термопринтеров). Также поддерживаем 58×30 и 58×60 мм. Все этикетки генерируются с разрешением 203 DPI.",
  },
  {
    question: "Как это работает?",
    answer: "Загрузите Excel с баркодами из кабинета WB и PDF с кодами ЧЗ → KleyKod объединит их на одной этикетке → Скачайте готовый PDF для термопринтера.",
  },
  {
    question: "Какой штраф за отсутствие маркировки?",
    answer: "До 300 000 ₽ для ИП, до 1 000 000 ₽ для юрлиц. Товар без читаемого DataMatrix возвращается с FBS. KleyKod проверяет код до печати.",
  },
  {
    question: "Сколько этикеток можно сделать бесплатно?",
    answer: "50 этикеток в месяц — бесплатно навсегда. Для FBS селлеров с небольшими объёмами этого достаточно.",
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className="py-20 bg-cream" id="faq">
      <div className="container mx-auto px-6">
        {/* Заголовок */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-warm-gray-900">
            Частые вопросы
          </h2>
        </motion.div>

        {/* Аккордеон */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-2xl mx-auto bg-white border-2 border-warm-gray-200 rounded-xl shadow-[2px_2px_0px_#E7E5E4] overflow-hidden"
        >
          {faqs.map((faq, index) => (
            <div
              key={index}
              className={index < faqs.length - 1 ? "border-b-2 border-warm-gray-100" : ""}
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full px-6 py-4 text-left flex items-center justify-between gap-4 hover:bg-warm-gray-50 transition-colors"
              >
                <span className="font-semibold text-warm-gray-800">
                  {faq.question}
                </span>
                <span className="text-xl text-warm-gray-400 flex-shrink-0 w-6 text-center">
                  {openIndex === index ? "−" : "+"}
                </span>
              </button>

              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="px-6 pb-4 text-warm-gray-600">
                      {faq.answer}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
