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
import { Button } from "@/components/ui/button";
import { openExternalLink } from "@/lib/vk-bridge";
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
        <Button
          onClick={() => openExternalLink("https://kleykod.ru")}
          variant="secondary"
        >
          <ExternalLink className="mr-2 h-4 w-4" />
          Открыть сайт
        </Button>
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
          <span className="font-medium">vk.com/kleykod</span>
        </p>
        <Button
          onClick={() => openExternalLink("https://vk.com/kleykod")}
          className="mt-2"
        >
          Перейти в сообщество
        </Button>
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
