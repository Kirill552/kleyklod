"use client";

/**
 * Компонент Telegram Login Widget.
 *
 * Загружает официальный виджет Telegram и вызывает callback при авторизации.
 * Документация: https://core.telegram.org/widgets/login
 */

import { useEffect, useRef } from "react";
import type { TelegramAuthData } from "@/types/api";

interface TelegramLoginButtonProps {
  /** Callback при успешной авторизации */
  onAuth: (data: TelegramAuthData) => void;
  /** Имя бота без @ (по умолчанию из env) */
  botName?: string;
  /** Размер кнопки */
  buttonSize?: "large" | "medium" | "small";
  /** Радиус скругления углов в px */
  cornerRadius?: number;
  /** Показывать аватар пользователя */
  showAvatar?: boolean;
}

// Типизация глобального callback для Telegram Widget
declare global {
  interface Window {
    [key: string]: ((user: TelegramAuthData) => void) | undefined;
  }
}

/**
 * Кнопка авторизации через Telegram.
 *
 * @example
 * ```tsx
 * function LoginPage() {
 *   const { login } = useAuth();
 *   return <TelegramLoginButton onAuth={login} />;
 * }
 * ```
 */
export function TelegramLoginButton({
  onAuth,
  botName = process.env.NEXT_PUBLIC_TELEGRAM_BOT_NAME || "kleykod_bot",
  buttonSize = "large",
  cornerRadius = 12,
  showAvatar = true,
}: TelegramLoginButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const callbackNameRef = useRef<string>("");

  useEffect(() => {
    if (!containerRef.current) return;

    // Создаём уникальное имя callback функции
    const callbackName = `onTelegramAuth_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    callbackNameRef.current = callbackName;

    // Регистрируем глобальный callback
    window[callbackName] = onAuth;

    // Очищаем контейнер
    containerRef.current.innerHTML = "";

    // Создаём script элемент для виджета
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", botName);
    script.setAttribute("data-size", buttonSize);
    script.setAttribute("data-radius", cornerRadius.toString());
    script.setAttribute("data-userpic", showAvatar.toString());
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-onauth", callbackName);

    containerRef.current.appendChild(script);

    // Очистка при размонтировании
    return () => {
      delete window[callbackNameRef.current];
    };
  }, [botName, onAuth, buttonSize, cornerRadius, showAvatar]);

  return (
    <div ref={containerRef} className="flex justify-center min-h-[40px]">
      {/* Telegram Widget будет вставлен сюда */}
      <div className="animate-pulse bg-warm-gray-200 rounded-xl h-10 w-48" />
    </div>
  );
}

/**
 * Обёртка с предустановленными настройками для KleyKod.
 */
export function KleyKodLoginButton({
  onAuth,
}: {
  onAuth: (data: TelegramAuthData) => void;
}) {
  return (
    <TelegramLoginButton
      onAuth={onAuth}
      buttonSize="large"
      cornerRadius={12}
      showAvatar={true}
    />
  );
}
