"use client";

/**
 * Панель чата поддержки.
 *
 * Отображается при клике на floating bubble.
 * Загружает историю сообщений и позволяет отправлять новые.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { SupportMessage, type SupportMessageData } from "./support-message";

interface SupportChatProps {
  onClose: () => void;
  onNewMessage: () => void;
}

export function SupportChat({ onClose, onNewMessage }: SupportChatProps) {
  const [messages, setMessages] = useState<SupportMessageData[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom при новых сообщениях
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Загрузка истории сообщений
  const loadMessages = useCallback(async () => {
    try {
      const response = await fetch("/api/support/messages", {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setError(null);
      } else if (response.status === 401) {
        setError("Необходима авторизация");
      }
    } catch {
      setError("Ошибка загрузки сообщений");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Загружаем историю при монтировании
  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  // Scroll при загрузке и новых сообщениях
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Polling для новых сообщений (каждые 10 сек)
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const lastMessage = messages[messages.length - 1];
        const since = lastMessage?.created_at || "";

        const response = await fetch(
          `/api/support/messages?since=${encodeURIComponent(since)}`,
          { credentials: "include" }
        );

        if (response.ok) {
          const data = await response.json();
          if (data.messages && data.messages.length > 0) {
            setMessages((prev) => {
              // Фильтруем дубликаты по id
              const existingIds = new Set(prev.map((m) => m.id));
              const newMessages = data.messages.filter(
                (m: SupportMessageData) => !existingIds.has(m.id)
              );
              if (newMessages.length > 0) {
                onNewMessage();
                return [...prev, ...newMessages];
              }
              return prev;
            });
          }
        }
      } catch {
        // Тихо игнорируем ошибки polling
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [messages, onNewMessage]);

  // Отправка сообщения
  const handleSend = async () => {
    const text = inputText.trim();
    if (!text || isSending) return;

    setIsSending(true);
    setError(null);

    // Оптимистичное добавление сообщения
    const tempMessage: SupportMessageData = {
      id: `temp-${Date.now()}`,
      text,
      from: "user",
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempMessage]);
    setInputText("");

    try {
      const response = await fetch("/api/support/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ text }),
      });

      if (response.ok) {
        const data = await response.json();
        // Заменяем временное сообщение на реальное
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === tempMessage.id ? { ...msg, id: data.message_id } : msg
          )
        );
      } else {
        // Удаляем временное сообщение при ошибке
        setMessages((prev) => prev.filter((msg) => msg.id !== tempMessage.id));
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.error || "Ошибка отправки сообщения");
      }
    } catch {
      // Удаляем временное сообщение при ошибке
      setMessages((prev) => prev.filter((msg) => msg.id !== tempMessage.id));
      setError("Ошибка отправки сообщения");
    } finally {
      setIsSending(false);
      textareaRef.current?.focus();
    }
  };

  // Отправка по Enter (Shift+Enter для новой строки)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Автовысота textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  return (
    <div
      className={cn(
        "fixed bottom-24 right-6 z-50",
        "w-80 sm:w-96",
        "bg-white rounded-2xl shadow-2xl",
        "flex flex-col",
        "max-h-[70vh]",
        "border border-warm-gray-200"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-warm-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          <h3 className="font-semibold text-warm-gray-900">Поддержка</h3>
        </div>
        <button
          onClick={onClose}
          className="text-warm-gray-400 hover:text-warm-gray-600 transition-colors"
          aria-label="Закрыть чат"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px] max-h-[400px]">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-6 h-6 animate-spin text-warm-gray-400" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <p className="text-warm-gray-500 text-sm">
              Напишите ваш вопрос — мы ответим в ближайшее время
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <SupportMessage key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="px-4 py-2 bg-rose-50 text-rose-600 text-sm">
          {error}
        </div>
      )}

      {/* Input area */}
      <div className="p-3 border-t border-warm-gray-100">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Напишите сообщение..."
            rows={1}
            className={cn(
              "flex-1 resize-none",
              "px-3 py-2 rounded-xl",
              "bg-warm-gray-50 border border-warm-gray-200",
              "text-sm text-warm-gray-900 placeholder:text-warm-gray-400",
              "focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent",
              "transition-all"
            )}
            style={{ maxHeight: "120px" }}
          />
          <Button
            onClick={handleSend}
            disabled={!inputText.trim() || isSending}
            size="sm"
            className="h-10 w-10 p-0 rounded-xl"
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-warm-gray-400 mt-2 text-center">
          Enter — отправить, Shift+Enter — новая строка
        </p>
      </div>
    </div>
  );
}
