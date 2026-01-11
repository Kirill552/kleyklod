"use client";

/**
 * VK One Tap кнопка авторизации.
 *
 * Использует VK ID SDK для отображения кнопки "Продолжить как [Имя]".
 * После успешной авторизации отправляет code на наш backend для обмена на JWT.
 */

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

const VK_APP_ID = 54418365;
const VK_REDIRECT_URL = "https://kleykod.ru/api/auth/vk/callback";

// Типы для VK ID SDK
interface VKOneTapWidget {
  render: (options: {
    container: HTMLElement;
    showAlternativeLogin: boolean;
  }) => VKOneTapWidget;
  on: (event: unknown, handler: (payload: unknown) => void) => VKOneTapWidget;
}

declare global {
  interface Window {
    VKIDSDK?: {
      Config: {
        init: (config: {
          app: number;
          redirectUrl: string;
          responseMode: unknown;
          source: unknown;
          scope: string;
        }) => void;
      };
      ConfigResponseMode: {
        Callback: unknown;
      };
      ConfigSource: {
        LOWCODE: unknown;
      };
      OneTap: new () => VKOneTapWidget;
      OneTapInternalEvents: {
        LOGIN_SUCCESS: unknown;
      };
      WidgetEvents: {
        ERROR: unknown;
      };
    };
  }
}

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
  const sdkLoadedRef = useRef(false);

  useEffect(() => {
    // Предотвращаем повторную загрузку SDK
    if (sdkLoadedRef.current) return;

    // Проверяем, не загружен ли уже SDK
    if (window.VKIDSDK) {
      initVKID();
      return;
    }

    // Загружаем VK ID SDK
    const script = document.createElement("script");
    script.src = "https://unpkg.com/@vkid/sdk@2.6.2/dist-sdk/umd/index.js";
    script.async = true;
    script.onload = () => {
      sdkLoadedRef.current = true;
      initVKID();
    };
    script.onerror = () => {
      setError("Не удалось загрузить VK SDK");
    };
    document.body.appendChild(script);

    return () => {
      // Не удаляем скрипт при размонтировании — он нужен для повторного рендера
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const initVKID = () => {
    const VKID = window.VKIDSDK;
    if (!VKID || !containerRef.current) return;

    try {
      VKID.Config.init({
        app: VK_APP_ID,
        redirectUrl: VK_REDIRECT_URL,
        responseMode: VKID.ConfigResponseMode.Callback,
        source: VKID.ConfigSource.LOWCODE,
        scope: "",
      });

      const oneTap = new VKID.OneTap();
      oneTap
        .render({
          container: containerRef.current,
          showAlternativeLogin: true,
        })
        .on(VKID.OneTapInternalEvents.LOGIN_SUCCESS, handleSuccess)
        .on(VKID.WidgetEvents.ERROR, handleError);
    } catch (err) {
      console.error("VK SDK init error:", err);
      setError("Ошибка инициализации VK SDK");
    }
  };

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

  if (error) {
    return (
      <div className="text-center">
        <p className="text-red-500 text-sm mb-2">{error}</p>
        <button
          onClick={() => {
            setError(null);
            initVKID();
          }}
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
