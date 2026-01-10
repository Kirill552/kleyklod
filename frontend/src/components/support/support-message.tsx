"use client";

/**
 * Компонент отдельного сообщения в чате поддержки.
 */

import { cn } from "@/lib/utils";

export interface SupportMessageData {
  id: string;
  text: string;
  from: "user" | "support";
  created_at: string;
}

interface SupportMessageProps {
  message: SupportMessageData;
}

export function SupportMessage({ message }: SupportMessageProps) {
  const isUser = message.from === "user";

  // Форматирование времени
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2",
          isUser
            ? "bg-emerald-500 text-white rounded-br-md"
            : "bg-warm-gray-100 text-warm-gray-900 rounded-bl-md"
        )}
      >
        {/* Текст сообщения */}
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.text}
        </p>

        {/* Время */}
        <p
          className={cn(
            "text-xs mt-1",
            isUser ? "text-emerald-100" : "text-warm-gray-500"
          )}
        >
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}
