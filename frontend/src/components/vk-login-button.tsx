"use client";

/**
 * VK авторизация через виджет 3в1 (VK ID, Mail.ru, OK.ru).
 *
 * Использует VK ID SDK OAuthList для отображения кнопок авторизации.
 * PKCE: code_verifier генерируется на фронте, обмен кода на бэкенде.
 */

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import * as VKID from "@vkid/sdk";

const VK_APP_ID = 54418365;
const VK_REDIRECT_URL = "https://kleykod.ru/api/auth/vk/callback";

interface VKLoginPayload {
  code: string;
  device_id: string;
}

/**
 * Генерация code_verifier для PKCE (43-128 символов).
 */
function generateCodeVerifier(): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
  const array = new Uint8Array(64);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => chars[byte % chars.length]).join("");
}

// Храним code_verifier в модуле (не в state, чтобы не потерять при ререндере)
let currentCodeVerifier: string | null = null;

export function VKLoginButton() {
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/app";
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (isInitialized || !containerRef.current) return;

    try {
      // Генерируем code_verifier для PKCE
      currentCodeVerifier = generateCodeVerifier();

      // Инициализируем VK ID SDK с code_verifier
      VKID.Config.init({
        app: VK_APP_ID,
        redirectUrl: VK_REDIRECT_URL,
        responseMode: VKID.ConfigResponseMode.Callback,
        source: VKID.ConfigSource.LOWCODE,
        scope: "",
        codeVerifier: currentCodeVerifier,
      });

      // Создаём виджет 3в1 (VK, Mail.ru, OK.ru)
      const oAuth = new VKID.OAuthList();
      oAuth
        .render({
          container: containerRef.current,
          styles: { height: 46 },
          oauthList: ["vkid", "mail_ru", "ok_ru"],
        })
        .on(VKID.OAuthListInternalEvents.LOGIN_SUCCESS, handleSuccess)
        .on(VKID.WidgetEvents.ERROR, handleError);

      setIsInitialized(true);
    } catch (err) {
      console.error("VK SDK init error:", err);
      setError("Ошибка инициализации VK SDK");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSuccess = async (payload: unknown) => {
    const { code, device_id } = payload as VKLoginPayload;

    if (!code || !device_id || !currentCodeVerifier) {
      setError("Не получены данные авторизации от VK");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Отправляем code + device_id + code_verifier на backend для обмена
      const res = await fetch("/api/auth/vk/callback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code,
          device_id,
          code_verifier: currentCodeVerifier,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Ошибка авторизации");
      }

      // Успешная авторизация — редирект
      router.push(callbackUrl);
      router.refresh();
    } catch (err) {
      console.error("VK auth error:", err);
      setError(err instanceof Error ? err.message : "Ошибка авторизации VK");
      setIsLoading(false);
    }
  };

  const handleError = (err: unknown) => {
    console.error("VK SDK error:", err);
    // Не показываем ошибку если пользователь просто закрыл окно
  };

  const retry = () => {
    setError(null);
    setIsInitialized(false);
  };

  if (error) {
    return (
      <div className="text-center">
        <p className="text-red-500 text-sm mb-2">{error}</p>
        <button
          onClick={retry}
          className="text-sm text-emerald-600 hover:underline"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-12">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex justify-center min-h-[44px]"
      data-testid="vk-login-button"
    />
  );
}
