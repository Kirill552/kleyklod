/**
 * Утилиты для авторизации через HttpOnly cookies.
 *
 * Токен хранится в HttpOnly cookie (устанавливается через /api/auth/telegram).
 * Клиентский код не имеет доступа к токену напрямую — это защита от XSS.
 */

import type { User, TelegramAuthData, AuthResponse } from "@/types/api";

/**
 * Авторизация через Telegram Login Widget.
 *
 * Отправляет данные на Next.js API Route, который:
 * 1. Пересылает на FastAPI для валидации
 * 2. Получает JWT токен
 * 3. Устанавливает HttpOnly cookie
 * 4. Возвращает данные пользователя (без токена)
 *
 * @param data - Данные от Telegram Widget
 * @returns Данные пользователя
 */
export async function loginWithTelegram(
  data: TelegramAuthData
): Promise<AuthResponse> {
  const response = await fetch("/api/auth/telegram", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
    credentials: "include", // Важно для установки cookie
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || "Ошибка авторизации");
  }

  return response.json();
}

/**
 * Получить данные текущего пользователя.
 *
 * Отправляет запрос на Next.js API Route, который:
 * 1. Читает токен из HttpOnly cookie
 * 2. Запрашивает данные у FastAPI
 * 3. Возвращает профиль пользователя
 *
 * @returns Данные пользователя или null если не авторизован
 */
export async function getCurrentUser(): Promise<User | null> {
  try {
    const response = await fetch("/api/auth/me", {
      method: "GET",
      credentials: "include",
    });

    if (!response.ok) {
      if (response.status === 401) {
        return null; // Не авторизован
      }
      throw new Error("Ошибка получения профиля");
    }

    const data = await response.json();
    return data.user;
  } catch {
    return null;
  }
}

/**
 * Выход из системы.
 *
 * Удаляет HttpOnly cookie с токеном.
 */
export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
  });
}

/**
 * Проверить, авторизован ли пользователь.
 *
 * Делает запрос к /api/auth/me и проверяет ответ.
 * Используется для клиентской проверки (middleware делает серверную).
 *
 * @returns true если авторизован
 */
export async function checkAuth(): Promise<boolean> {
  const user = await getCurrentUser();
  return user !== null;
}
