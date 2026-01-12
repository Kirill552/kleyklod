"use client";

import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Send, MessageCircle } from "lucide-react";
import Link from "next/link";
import { analytics } from "@/lib/analytics";

export function Footer() {
  return (
    <footer className="section-alt border-t border-warm-gray-100">
      {/* CTA секция */}
      <div className="container mx-auto px-6 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-3xl p-8 md:p-12 bg-gradient-to-br from-emerald-600 to-teal-700 text-white text-center relative overflow-hidden shadow-2xl shadow-emerald-500/30"
        >
          {/* Декоративные элементы */}
          <div className="absolute top-0 left-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-400/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2" />

          <div className="relative z-10">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Создать этикетку онлайн бесплатно
            </h2>
            <p className="text-white/90 text-lg mb-8 max-w-xl mx-auto">
              Присоединяйтесь к 7,000+ селлерам Wildberries. Генератор этикеток 58x40 с кодом Честного Знака.
              Первые 50 этикеток каждый день — бесплатно навсегда.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/app" className="bg-white text-emerald-600 hover:bg-emerald-50 font-semibold py-3 px-8 rounded-xl transition-colors flex items-center gap-2">
                Начать бесплатно
                <ArrowRight className="w-5 h-5" />
              </Link>
              <a
                href="https://t.me/kleykod_bot"
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => analytics.botClick()}
                className="text-white/80 hover:text-white font-medium flex items-center gap-2 transition-colors"
              >
                <Send className="w-5 h-5" />
                Попробовать в Telegram
              </a>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Основной футер */}
      <div className="container mx-auto px-6 py-12 border-t border-warm-gray-100">
        <div className="grid md:grid-cols-4 gap-12">
          {/* Логотип и описание */}
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl text-warm-gray-800">
                KleyKod
              </span>
            </Link>
            <p className="text-warm-gray-500 mb-6 max-w-sm">
              Генератор этикеток для маркетплейсов. Печать этикеток 58x40 с кодом маркировки Честного Знака для Wildberries и Ozon.
            </p>
            <div className="flex items-center gap-4">
              <a
                href="https://t.me/kleykod_bot"
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => analytics.botClick()}
                className="w-10 h-10 bg-warm-gray-100 hover:bg-[#0088cc] hover:text-white rounded-lg flex items-center justify-center text-warm-gray-500 transition-colors"
              >
                <Send className="w-5 h-5" />
              </a>
              <a
                href="https://vk.ru/kleykod"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 bg-warm-gray-100 hover:bg-emerald-500 hover:text-white rounded-lg flex items-center justify-center text-warm-gray-500 transition-colors"
              >
                <MessageCircle className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Продукт */}
          <div>
            <h4 className="font-semibold text-warm-gray-800 mb-4">Продукт</h4>
            <ul className="space-y-3">
              {[
                { label: "Возможности", href: "#features" },
                { label: "Тарифы", href: "#pricing" },
                { label: "FAQ", href: "#faq" },
                { label: "Статьи", href: "/articles" },
                { label: "API документация", href: "/docs" },
              ].map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-warm-gray-500 hover:text-emerald-600 transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Компания */}
          <div>
            <h4 className="font-semibold text-warm-gray-800 mb-4">Компания</h4>
            <ul className="space-y-3">
              <li>
                <Link
                  href="/privacy"
                  className="text-warm-gray-500 hover:text-emerald-600 transition-colors"
                >
                  Политика конфиденциальности
                </Link>
              </li>
              <li>
                <Link
                  href="/terms"
                  className="text-warm-gray-500 hover:text-emerald-600 transition-colors"
                >
                  Условия использования
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Копирайт */}
        <div className="mt-12 pt-8 border-t border-warm-gray-100 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-warm-gray-400">
          <p>© {new Date().getFullYear()} KleyKod. Все права защищены.</p>
          <p>
            Сделано с ❤️ для селлеров Wildberries и Ozon
          </p>
        </div>
      </div>
    </footer>
  );
}
