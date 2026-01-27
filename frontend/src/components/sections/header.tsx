"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";
import Link from "next/link";

const navLinks = [
  { href: "#features", label: "Возможности" },
  { href: "#pricing", label: "Тарифы" },
  { href: "#faq", label: "FAQ" },
];

export function Header() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? "bg-white/95 backdrop-blur-sm border-b-2 border-warm-gray-100"
            : "bg-transparent"
        }`}
      >
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between h-16 md:h-20">
            {/* Логотип */}
            <Link href="/" className="flex items-center gap-2">
              <div className="w-10 h-10 bg-emerald-600 rounded-lg border-2 border-emerald-800 flex items-center justify-center shadow-[2px_2px_0px_#065F46]">
                <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <span className="font-bold text-xl text-warm-gray-800">
                KleyKod
              </span>
            </Link>

            {/* Навигация — десктоп */}
            <nav className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-warm-gray-600 hover:text-emerald-700 transition-colors text-sm font-medium"
                >
                  {link.label}
                </a>
              ))}
            </nav>

            {/* CTA — десктоп */}
            <div className="hidden md:flex items-center gap-4">
              <Link
                href="/login"
                className="text-warm-gray-600 hover:text-warm-gray-800 text-sm font-medium"
              >
                Войти
              </Link>
              <Link
                href="/app"
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg border-2 border-emerald-800 shadow-[2px_2px_0px_#065F46] hover:shadow-[1px_1px_0px_#065F46] hover:translate-x-[1px] hover:translate-y-[1px] transition-all duration-150"
              >
                Начать бесплатно
              </Link>
            </div>

            {/* Бургер — мобильный */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 text-warm-gray-600"
              aria-label={isMobileMenuOpen ? "Закрыть меню" : "Открыть меню"}
              aria-expanded={isMobileMenuOpen}
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </motion.header>

      {/* Мобильное меню */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed inset-0 z-40 bg-white pt-20"
          >
            <nav className="container mx-auto px-6 py-8">
              <div className="space-y-4">
                {navLinks.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="block text-lg font-medium text-warm-gray-800 py-3 border-b-2 border-warm-gray-100"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
              <div className="mt-8 space-y-4">
                <Link
                  href="/login"
                  className="block text-center py-3 text-warm-gray-600 font-medium"
                >
                  Войти
                </Link>
                <Link
                  href="/app"
                  className="block text-center py-3 bg-emerald-600 text-white font-semibold rounded-lg border-2 border-emerald-800 shadow-[2px_2px_0px_#065F46]"
                >
                  Начать бесплатно
                </Link>
              </div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
