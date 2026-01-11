"use client";

/**
 * Страница авторизации через Telegram.
 *
 * Использует Telegram Login Widget для входа.
 * После успешной авторизации редиректит в /app.
 */

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { FileStack } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { TelegramLoginButton } from "@/components/telegram-login";
import { VKLoginButton } from "@/components/vk-login-button";

function LoginContent() {
  const { user, loading, error: authError } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL для редиректа после логина (из middleware)
  const callbackUrl = searchParams.get("callbackUrl") || "/app";

  // Ошибка из callback (если redirect не удался)
  const callbackError = searchParams.get("error");
  const error = callbackError || authError;

  // Если уже авторизован — редирект
  useEffect(() => {
    if (user && !loading) {
      router.push(callbackUrl);
    }
  }, [user, loading, router, callbackUrl]);

  // Показываем loader пока проверяем авторизацию
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4" />
          <p className="text-warm-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-white p-4">
      <div className="max-w-md w-full">
        {/* Карточка входа */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-warm-gray-100">
          {/* Логотип */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-flex items-center gap-2 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <FileStack className="w-6 h-6 text-white" />
              </div>
              <span className="font-bold text-2xl text-warm-gray-800">
                KleyKod
              </span>
            </Link>

            <h1 className="text-2xl font-bold text-warm-gray-900 mb-2">
              Вход в личный кабинет
            </h1>
            <p className="text-warm-gray-600">
              Войдите через Telegram или VK, чтобы начать создавать этикетки
            </p>
          </div>

          {/* Ошибка авторизации */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Кнопка Telegram Login */}
          <div className="flex justify-center mb-4">
            <TelegramLoginButton />
          </div>

          {/* Разделитель */}
          <div className="relative mb-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-warm-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-warm-gray-500">или</span>
            </div>
          </div>

          {/* Кнопка VK Login */}
          <div className="flex justify-center mb-8">
            <Suspense fallback={<div className="h-12" />}>
              <VKLoginButton />
            </Suspense>
          </div>

          {/* Преимущества */}
          <div className="space-y-3 text-sm text-warm-gray-600">
            <div className="flex items-start gap-2">
              <span className="text-emerald-500 mt-0.5">✓</span>
              <span>Безопасная авторизация через Telegram или VK</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-emerald-500 mt-0.5">✓</span>
              <span>Не требуется email и пароль</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-emerald-500 mt-0.5">✓</span>
              <span>50 бесплатных этикеток каждый день</span>
            </div>
          </div>
        </div>

        {/* Условия использования */}
        <p className="text-center text-sm text-warm-gray-500 mt-6">
          Входя в систему, вы соглашаетесь с{" "}
          <Link href="/terms" className="text-emerald-600 hover:underline">
            условиями использования
          </Link>{" "}
          и{" "}
          <Link href="/privacy" className="text-emerald-600 hover:underline">
            политикой конфиденциальности
          </Link>
        </p>

        {/* Ссылка на главную */}
        <p className="text-center mt-4">
          <Link
            href="/"
            className="text-sm text-warm-gray-500 hover:text-warm-gray-700"
          >
            ← Вернуться на главную
          </Link>
        </p>
      </div>
    </div>
  );
}

function LoginFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-white">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4" />
        <p className="text-warm-gray-600">Загрузка...</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginContent />
    </Suspense>
  );
}
