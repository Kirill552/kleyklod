"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Sparkles } from "lucide-react";
import Link from "next/link";

const navLinks = [
  { href: "#features", label: "Возможности" },
  { href: "#how-it-works", label: "Как работает" },
  { href: "#comparison", label: "Сравнение" },
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
            ? "bg-white/80 backdrop-blur-lg shadow-sm"
            : "bg-transparent"
        }`}
      >
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between h-16 md:h-20">
            {/* Логотип */}
            <Link href="/" className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Sparkles className="w-5 h-5 text-white" />
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
                  className="text-warm-gray-600 hover:text-emerald-600 transition-colors text-sm font-medium"
                >
                  {link.label}
                </a>
              ))}
            </nav>

            {/* CTA — десктоп */}
            <div className="hidden md:flex items-center gap-4">
              <a
                href="/login"
                className="text-warm-gray-600 hover:text-warm-gray-800 text-sm font-medium"
              >
                Войти
              </a>
              <a href="/app" className="btn-primary text-sm py-2.5 px-5">
                Начать бесплатно
              </a>
            </div>

            {/* Бургер — мобильный */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 text-warm-gray-600"
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
                    className="block text-lg font-medium text-warm-gray-800 py-3 border-b border-warm-gray-100"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
              <div className="mt-8 space-y-4">
                <a
                  href="/login"
                  className="block text-center py-3 text-warm-gray-600 font-medium"
                >
                  Войти
                </a>
                <a href="/app" className="btn-primary w-full block text-center">
                  Начать бесплатно
                </a>
              </div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
