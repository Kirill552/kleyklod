"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/app/sidebar";
import { Header } from "@/components/app/header";
import { ToastProvider } from "@/components/ui/toast";
import { SupportBubble } from "@/components/support";

// Временная проверка авторизации
// TODO: Заменить на реальную проверку через store/API
const isAuthenticated = () => {
  // Пока всегда возвращаем true для разработки
  // В продакшене здесь будет проверка токена/сессии
  return true;
};

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  useEffect(() => {
    // Проверка авторизации при монтировании
    if (!isAuthenticated()) {
      router.push("/");
    }
  }, [router]);

  return (
    <ToastProvider>
      <div className="flex min-h-screen bg-cream">
        {/* Боковая навигация - только на десктопе */}
        <Sidebar />

        {/* Основной контент */}
        <div className="flex-1 flex flex-col">
          {/* Header с адаптивным меню */}
          <Header />

          {/* Контент страницы */}
          <main className="flex-1 p-4 lg:p-8">
            <div className="max-w-7xl mx-auto">{children}</div>
          </main>
        </div>

        {/* Виджет чата поддержки */}
        <SupportBubble />
      </div>
    </ToastProvider>
  );
}
