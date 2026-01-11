"use client";

/**
 * VK One Tap кнопка авторизации.
 *
 * Использует VK ID SDK для отображения кнопки "Продолжить как [Имя]".
 * После успешной авторизации отправляет code на наш backend для обмена на JWT.
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
      // Инициализируем VK ID SDK
      VKID.Config.init({
        app: VK_APP_ID,
        redirectUrl: VK_REDIRECT_URL,
        responseMode: VKID.ConfigResponseMode.Callback,
        source: VKID.ConfigSource.LOWCODE,
        scope: "",
      });

      // Создаём и рендерим кнопку One Tap
      const oneTap = new VKID.OneTap();
      oneTap
        .render({
          container: containerRef.current,
          showAlternativeLogin: true,
          scheme: VKID.Scheme.LIGHT,
          lang: VKID.Languages.RUS,
        })
        .on(VKID.OneTapInternalEvents.LOGIN_SUCCESS, handleSuccess)
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

    if (!code || !device_id) {
      setError("Не получены данные авторизации от VK");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Отправляем code на наш backend для обмена на JWT
      const res = await fetch("/api/auth/vk/callback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code,
          device_id,
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
