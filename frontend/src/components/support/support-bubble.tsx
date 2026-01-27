"use client";

/**
 * Floating bubble для чата поддержки.
 *
 * Отображается в правом нижнем углу на страницах /app/*.
 * При клике открывает панель чата.
 */

import { useState, useEffect } from "react";
import { MessageCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/auth-context";
import { SupportChat } from "./support-chat";

export function SupportBubble() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Polling для проверки новых сообщений (каждые 30 сек)
  useEffect(() => {
    if (!user) return;

    const checkUnread = async () => {
      try {
        const response = await fetch("/api/support/unread", {
          credentials: "include",
        });
        if (response.ok) {
          const data = await response.json();
          setUnreadCount(data.count || 0);
        }
      } catch {
        // Тихо игнорируем ошибки polling
      }
    };

    // Проверяем сразу и потом каждые 30 секунд
    checkUnread();
    const interval = setInterval(checkUnread, 30000);

    return () => clearInterval(interval);
  }, [user]);

  // Сбрасываем счётчик при открытии чата
  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0);
    }
  }, [isOpen]);

  // Не показываем если пользователь не авторизован
  if (!user) {
    return null;
  }

  return (
    <>
      {/* Floating bubble */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "fixed bottom-6 right-6 z-50",
          "w-14 h-14 rounded-full",
          "bg-emerald-500 hover:bg-emerald-600",
          "text-white shadow-[3px_3px_0px_#059669]",
          "transition-all duration-200",
          "flex items-center justify-center",
          "focus:outline-none focus:border-2 focus:border-emerald-700"
        )}
        aria-label={isOpen ? "Закрыть чат" : "Открыть чат поддержки"}
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <>
            <MessageCircle className="w-6 h-6" />
            {/* Badge с количеством непрочитанных */}
            {unreadCount > 0 && (
              <span
                className={cn(
                  "absolute -top-1 -right-1",
                  "min-w-5 h-5 px-1.5",
                  "bg-rose-500 text-white",
                  "text-xs font-bold",
                  "rounded-full",
                  "flex items-center justify-center"
                )}
              >
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </>
        )}
      </button>

      {/* Панель чата */}
      {isOpen && (
        <SupportChat
          onClose={() => setIsOpen(false)}
          onNewMessage={() => setUnreadCount(0)}
        />
      )}
    </>
  );
}
