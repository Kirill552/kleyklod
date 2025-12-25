"use client";

import { useState } from "react";
import { Menu, LogOut, User, X } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

// Временные данные пользователя (позже будут из store/API)
const mockUser = {
  name: "Иван Иванов",
  username: "@ivanov",
  avatar: undefined,
};

const navItems = [
  { href: "/app", label: "Дашборд" },
  { href: "/app/generate", label: "Генерация" },
  { href: "/app/history", label: "История" },
  { href: "/app/subscription", label: "Подписка" },
  { href: "/app/settings", label: "Настройки" },
];

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  const handleLogout = () => {
    // TODO: Реализовать логику выхода
    alert("Выход из аккаунта");
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

          {/* Профиль пользователя */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-medium text-warm-gray-800">
                {mockUser.name}
              </p>
              <p className="text-xs text-warm-gray-500">{mockUser.username}</p>
            </div>
            <Avatar className="w-10 h-10">
              {mockUser.avatar ? (
                <AvatarImage src={mockUser.avatar} alt={mockUser.name} />
              ) : (
                <AvatarFallback>
                  {mockUser.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </AvatarFallback>
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
                  <AvatarFallback>
                    {mockUser.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-warm-gray-800">
                    {mockUser.name}
                  </p>
                  <p className="text-sm text-warm-gray-500">
                    {mockUser.username}
                  </p>
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
