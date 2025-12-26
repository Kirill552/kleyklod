"use client";

/**
 * Компонент Telegram Login Widget.
 *
 * Использует redirect подход (data-auth-url) для надёжной работы во всех браузерах.
 * Документация: https://core.telegram.org/widgets/login
 */

import { useEffect, useRef } from "react";

interface TelegramLoginButtonProps {
  /** URL для redirect после авторизации (по умолчанию /api/auth/telegram/callback) */
  authUrl?: string;
  /** Имя бота без @ (по умолчанию из env) */
  botName?: string;
  /** Размер кнопки */
  buttonSize?: "large" | "medium" | "small";
  /** Радиус скругления углов в px */
  cornerRadius?: number;
  /** Показывать аватар пользователя */
  showAvatar?: boolean;
}

/**
 * Кнопка авторизации через Telegram (redirect подход).
 *
 * После авторизации Telegram перенаправит на authUrl с GET параметрами:
 * id, first_name, last_name, username, photo_url, auth_date, hash
 */
export function TelegramLoginButton({
  authUrl = "https://kleykod.ru/api/auth/telegram/callback",
  botName = process.env.NEXT_PUBLIC_TELEGRAM_BOT_NAME || "kleykod_bot",
  buttonSize = "large",
  cornerRadius = 12,
  showAvatar = true,
}: TelegramLoginButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

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
    // Используем redirect вместо callback - более надёжно
    script.setAttribute("data-auth-url", authUrl);

    containerRef.current.appendChild(script);
  }, [authUrl, botName, buttonSize, cornerRadius, showAvatar]);

  return (
    <div ref={containerRef} className="flex justify-center min-h-[40px]">
      {/* Telegram Widget будет вставлен сюда */}
      <div className="animate-pulse bg-warm-gray-200 rounded-xl h-10 w-48" />
    </div>
  );
}

/**
 * Обёртка с предустановленными настройками для KleyKod.
 * Использует redirect подход - после авторизации пользователь
 * будет перенаправлен на /api/auth/telegram/callback.
 */
export function KleyKodLoginButton() {
  return (
    <TelegramLoginButton
      buttonSize="large"
      cornerRadius={12}
      showAvatar={true}
    />
  );
}
