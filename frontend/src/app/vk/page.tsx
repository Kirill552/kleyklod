"use client";

/**
 * Точка входа VK Mini App.
 *
 * Автоматически:
 * - Инициализирует VK Bridge
 * - Авторизует пользователя
 * - Показывает генератор этикеток
 */

import { VKAuthProvider, useVKAuth } from "@/contexts/vk-auth-context";
import { Loader2, ExternalLink, AlertCircle } from "lucide-react";
import dynamic from "next/dynamic";

// Динамический импорт генератора (тяжёлый компонент)
const VKGeneratePage = dynamic(
  () => import("@/components/vk/vk-generate-page"),
  {
    loading: () => (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    ),
  }
);

/**
 * Контент VK Mini App.
 */
function VKAppContent() {
  const { loading, error, isAuthenticated, user, groupId } = useVKAuth();

  // Загрузка
  if (loading) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 p-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-muted-foreground">Загрузка...</p>
      </div>
    );
  }

  // Ошибка авторизации
  if (error) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 p-4 text-center">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <h1 className="text-xl font-bold">Ошибка</h1>
        <p className="text-muted-foreground">{error}</p>
        <a
          href="https://kleykod.ru"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all px-6 py-3 btn-secondary"
        >
          <ExternalLink className="h-4 w-4" />
          Открыть сайт
        </a>
      </div>
    );
  }

  // Не авторизован
  if (!isAuthenticated) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 p-4 text-center">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <h1 className="text-xl font-bold">Не удалось авторизоваться</h1>
        <p className="text-muted-foreground">
          Попробуйте открыть приложение заново
        </p>
      </div>
    );
  }

  // Если запущено не из сообщества — показать инструкцию
  if (!groupId) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 p-4 text-center">
        <div className="rounded-full bg-primary/10 p-4">
          <ExternalLink className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-xl font-bold">KleyKod</h1>
        <p className="text-muted-foreground max-w-sm">
          Откройте приложение из сообщества{" "}
          <span className="font-medium">КлейКод</span>
        </p>
        <a
          href="https://vk.com/club235274662"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all px-6 py-3 mt-2 btn-primary"
        >
          Перейти в сообщество
        </a>
      </div>
    );
  }

  // Основной интерфейс
  return <VKGeneratePage user={user} />;
}

/**
 * Страница VK Mini App.
 */
export default function VKPage() {
  return (
    <VKAuthProvider>
      <div className="min-h-screen bg-background">
        <VKAppContent />
      </div>
    </VKAuthProvider>
  );
}
