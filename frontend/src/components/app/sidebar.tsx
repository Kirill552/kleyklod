"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Sparkles,
  FileStack,
  History,
  Crown,
  Settings,
  Package,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  {
    href: "/app",
    label: "Дашборд",
    icon: LayoutDashboard,
  },
  {
    href: "/app/generate",
    label: "Генерация",
    icon: Sparkles,
  },
  {
    href: "/app/products",
    label: "Карточки",
    icon: Package,
  },
  {
    href: "/app/history",
    label: "История",
    icon: History,
  },
  {
    href: "/app/subscription",
    label: "Подписка",
    icon: Crown,
  },
  {
    href: "/app/settings",
    label: "Настройки",
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-white border-r border-warm-gray-200 h-screen sticky top-0">
      {/* Логотип */}
      <div className="p-6 border-b border-warm-gray-200">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <FileStack className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-xl text-warm-gray-800">
            KleyKod
          </span>
        </Link>
      </div>

      {/* Навигация */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium text-sm",
                    isActive
                      ? "bg-emerald-50 text-emerald-700 shadow-sm"
                      : "text-warm-gray-600 hover:bg-warm-gray-50 hover:text-warm-gray-900"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Информация о версии */}
      <div className="p-4 border-t border-warm-gray-200">
        <p className="text-xs text-warm-gray-400 text-center">
          KleyKod v1.0.0
        </p>
      </div>
    </aside>
  );
}
