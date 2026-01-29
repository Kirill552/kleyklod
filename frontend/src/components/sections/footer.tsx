"use client";

import Link from "next/link";
import Image from "next/image";
import { Send } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-emerald-700">
      <div className="container mx-auto px-6 pb-10" style={{ paddingTop: '64px' }}>
        {/* Верхняя строка: лого слева, соцсети справа */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <Link href="/" className="text-white font-bold text-lg">
              KleyKod
            </Link>
            <p className="text-emerald-200 text-sm mt-1">
              Этикетки WB + Честный Знак
            </p>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="https://t.me/kleykod_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="w-9 h-9 bg-emerald-600 hover:bg-emerald-500 rounded-lg border-2 border-emerald-500 hover:border-emerald-400 flex items-center justify-center text-emerald-200 hover:text-white transition-all"
              aria-label="Telegram"
            >
              <Send className="w-4 h-4" />
            </a>
            <a
              href="https://vk.ru/kleykod"
              target="_blank"
              rel="noopener noreferrer"
              className="w-9 h-9 bg-emerald-600 hover:bg-emerald-500 rounded-lg border-2 border-emerald-500 hover:border-emerald-400 flex items-center justify-center text-emerald-200 hover:text-white transition-all"
              aria-label="VK"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M15.07 2H8.93C3.33 2 2 3.33 2 8.93v6.14C2 20.67 3.33 22 8.93 22h6.14c5.6 0 6.93-1.33 6.93-6.93V8.93C22 3.33 20.67 2 15.07 2zm3.08 14.27h-1.46c-.55 0-.72-.44-1.71-1.45-1-.95-1.37-1.07-1.6-1.07-.33 0-.42.09-.42.53v1.32c0 .38-.12.6-1.1.6-1.62 0-3.42-.98-4.69-2.81-1.9-2.67-2.42-4.67-2.42-5.08 0-.23.09-.44.53-.44h1.46c.4 0 .55.18.7.6.77 2.23 2.06 4.18 2.59 4.18.2 0 .29-.09.29-.59v-2.3c-.06-1.07-.62-1.16-.62-1.54 0-.19.15-.38.4-.38h2.3c.33 0 .45.18.45.56v3.1c0 .33.15.45.24.45.2 0 .36-.12.72-.48 1.12-1.25 1.92-3.18 1.92-3.18.1-.23.28-.44.68-.44h1.46c.44 0 .53.23.44.56-.18.82-1.9 3.26-1.9 3.26-.15.24-.21.35 0 .62.15.2.64.62 1 1 .65.71 1.15 1.3 1.28 1.71.15.42-.07.64-.49.64z"/>
              </svg>
            </a>
          </div>
        </div>

        {/* Ссылки по центру */}
        <nav className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm">
          <Link href="/wb-labels" className="text-emerald-200 hover:text-white transition-colors">
            Этикетки WB
          </Link>
          <Link href="/chz-labels" className="text-emerald-200 hover:text-white transition-colors">
            Этикетки ЧЗ
          </Link>
          <a href="#pricing" className="text-emerald-200 hover:text-white transition-colors">
            Тарифы
          </a>
          <a href="#faq" className="text-emerald-200 hover:text-white transition-colors">
            FAQ
          </a>
          <Link href="/articles" className="text-emerald-200 hover:text-white transition-colors">
            Статьи
          </Link>
          <Link href="/privacy" className="text-emerald-200 hover:text-white transition-colors">
            Политика
          </Link>
          <Link href="/terms" className="text-emerald-200 hover:text-white transition-colors">
            Условия
          </Link>
        </nav>

        {/* Партнёры */}
        <div className="mt-6 pt-6 border-t border-emerald-600">
          <div className="flex items-center justify-center gap-2 text-sm text-emerald-300">
            <span>Партнёр:</span>
            <a
              href="https://pi-data.ru/?utm_source=kleykod&utm_medium=partner&utm_campaign=footer"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
            >
              <Image
                src="/partners/pi-data.png"
                alt="Pi-Data"
                width={80}
                height={20}
                className="h-5 w-auto"
              />
            </a>
          </div>
        </div>

        {/* Копирайт */}
        <div className="mt-4 text-center text-sm text-emerald-300">
          © {new Date().getFullYear()} KleyKod
        </div>
      </div>
    </footer>
  );
}
