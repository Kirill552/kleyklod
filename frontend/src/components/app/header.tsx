"use client";

import { useState, useEffect } from "react";
import { Menu, LogOut, X, TrendingUp } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/auth-context";
import { getUserStats } from "@/lib/api";
import type { UserStats } from "@/types/api";

const navItems = [
  { href: "/app", label: "Дашборд" },
  { href: "/app/generate", label: "Генерация" },
  { href: "/app/products", label: "Карточки" },
  { href: "/app/history", label: "История" },
  { href: "/app/subscription", label: "Подписка" },
  { href: "/app/settings", label: "Настройки" },
];

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [stats, setStats] = useState<UserStats | null>(null);
  const pathname = usePathname();
  const { user, logout } = useAuth();

  // Загружаем статистику пользователя
  useEffect(() => {
    async function loadStats() {
      try {
        const data = await getUserStats();
        setStats(data);
      } catch {
        // Игнорируем ошибку — статистика не критична
      }
    }
    if (user) {
      loadStats();
    }
  }, [user]);

  // Формируем данные для отображения
  const displayName = user?.first_name || "Пользователь";
  const username = user?.username ? `@${user.username}` : "";
  const avatarUrl = user?.photo_url || undefined;
  const initials = displayName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase();

  const handleLogout = () => {
    logout();
  };

  return (
    <>
      <header className="sticky top-0 z-40 bg-white border-b border-warm-gray-200 backdrop-blur-lg bg-white/80">
        <div className="flex items-center justify-between px-4 lg:px-8 h-16">
          {/* Мобильное меню - кнопка */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-2 text-warm-gray-600 hover:bg-warm-gray-50 rounded-lg"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>

          {/* Заголовок - скрыт на больших экранах */}
          <h1 className="lg:hidden text-lg font-semibold text-warm-gray-800">
            KleyKod
          </h1>

          {/* Пустой div для выравнивания на десктопе */}
          <div className="hidden lg:block" />

          {/* Счетчик экономии + Профиль пользователя */}
          <div className="flex items-center gap-4">
            {/* Статистика и экономия */}
            {stats && stats.total_generated > 0 && (
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-emerald-50 rounded-lg border border-emerald-200">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                <div className="text-sm">
                  <span className="text-warm-gray-700">
                    {stats.total_generated} этикеток
                  </span>
                  <span className="text-emerald-600 font-medium ml-1">
                    ~{Math.round(stats.total_generated * 1.5)}&#8381; экономии
                  </span>
                  <span className="text-warm-gray-400 text-xs ml-1">(vs конкуренты)</span>
                </div>
              </div>
            )}

            {/* Профиль */}
            <div className="hidden sm:block text-right">
              <p className="text-sm font-medium text-warm-gray-800">
                {displayName}
              </p>
              {username && (
                <p className="text-xs text-warm-gray-500">{username}</p>
              )}
            </div>
            <Avatar className="w-10 h-10">
              {avatarUrl ? (
                <AvatarImage src={avatarUrl} alt={displayName} />
              ) : (
                <AvatarFallback>{initials}</AvatarFallback>
              )}
            </Avatar>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="hidden sm:flex"
            >
              <LogOut className="w-4 h-4" />
              Выйти
            </Button>
          </div>
        </div>
      </header>

      {/* Мобильное меню */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-30 bg-white">
          <nav className="pt-20 px-4">
            <ul className="space-y-2">
              {navItems.map((item) => {
                const isActive = pathname === item.href;

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={cn(
                        "block px-4 py-3 rounded-xl transition-all font-medium text-sm",
                        isActive
                          ? "bg-emerald-50 text-emerald-700 shadow-sm"
                          : "text-warm-gray-600 hover:bg-warm-gray-50 hover:text-warm-gray-900"
                      )}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>

            {/* Профиль и выход в мобильном меню */}
            <div className="mt-8 pt-8 border-t border-warm-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <Avatar className="w-12 h-12">
                  {avatarUrl ? (
                    <AvatarImage src={avatarUrl} alt={displayName} />
                  ) : (
                    <AvatarFallback>{initials}</AvatarFallback>
                  )}
                </Avatar>
                <div>
                  <p className="font-medium text-warm-gray-800">
                    {displayName}
                  </p>
                  {username && (
                    <p className="text-sm text-warm-gray-500">{username}</p>
                  )}
                </div>
              </div>
              <Button
                variant="secondary"
                size="md"
                onClick={handleLogout}
                className="w-full"
              >
                <LogOut className="w-4 h-4" />
                Выйти
              </Button>
            </div>
          </nav>
        </div>
      )}
    </>
  );
}
