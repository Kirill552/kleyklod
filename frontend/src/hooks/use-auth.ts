"use client";

/**
 * Хук для работы с авторизацией
 */

import { useState, useEffect, useCallback } from "react";
import type { User, TelegramUser } from "@/types/auth";
import {
  loginWithTelegram,
  getToken,
  setToken,
  removeToken,
} from "@/lib/auth";
import { getMe } from "@/lib/api";

interface UseAuthReturn {
  /** Данные пользователя или null если не авторизован */
  user: User | null;
  /** Идет ли загрузка данных пользователя */
  isLoading: boolean;
  /** Авторизация через Telegram */
  login: (data: TelegramUser) => Promise<void>;
  /** Выход из аккаунта */
  logout: () => void;
}

/**
 * Хук для управления авторизацией
 *
 * При монтировании проверяет наличие токена и загружает данные пользователя.
 * Предоставляет функции для входа и выхода.
 *
 * @example
 * ```tsx
 * function App() {
 *   const { user, isLoading, login, logout } = useAuth();
 *
 *   if (isLoading) return <div>Загрузка...</div>;
 *   if (!user) return <TelegramLoginButton onAuth={login} />;
 *   return <div>Привет, {user.first_name}!</div>;
 * }
 * ```
 */
export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Загрузка данных пользователя при монтировании
  useEffect(() => {
    async function loadUser() {
      const token = getToken();
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const userData = await getMe();
        setUser(userData);
      } catch (error) {
        console.error("Ошибка загрузки пользователя:", error);
        // Токен невалиден - очищаем
        removeToken();
      } finally {
        setIsLoading(false);
      }
    }

    loadUser();
  }, []);

  // Авторизация через Telegram
  const login = useCallback(async (data: TelegramUser) => {
    setIsLoading(true);
    try {
      const response = await loginWithTelegram(data);
      setToken(response.access_token);
      setUser(response.user);
    } catch (error) {
      console.error("Ошибка авторизации:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Выход из аккаунта
  const logout = useCallback(() => {
    removeToken();
    setUser(null);
  }, []);

  return {
    user,
    isLoading,
    login,
    logout,
  };
}
