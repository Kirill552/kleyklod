"use client";

/**
 * React Context для управления состоянием авторизации.
 *
 * Предоставляет:
 * - Текущего пользователя
 * - Функции входа/выхода
 * - Состояние загрузки
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import type { User, TelegramAuthData } from "@/types/api";
import { loginWithTelegram, getCurrentUser, logout as authLogout } from "@/lib/auth";
import { analytics } from "@/lib/analytics";

/** Состояние контекста авторизации */
interface AuthContextState {
  /** Текущий пользователь (null если не авторизован) */
  user: User | null;
  /** Идёт загрузка данных пользователя */
  loading: boolean;
  /** Ошибка авторизации */
  error: string | null;
  /** Вход через Telegram */
  login: (data: TelegramAuthData) => Promise<void>;
  /** Выход из системы */
  logout: () => Promise<void>;
  /** Обновить данные пользователя */
  refresh: () => Promise<void>;
}

/** Контекст авторизации */
const AuthContext = createContext<AuthContextState | undefined>(undefined);

/** Props провайдера */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Провайдер контекста авторизации.
 *
 * Оборачивает приложение и предоставляет доступ к состоянию авторизации.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  /**
   * Загрузить данные текущего пользователя.
   */
  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      console.error("Ошибка загрузки пользователя:", err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Вход через Telegram Login Widget.
   */
  const login = useCallback(
    async (data: TelegramAuthData) => {
      console.log("[AUTH] login called with data:", JSON.stringify(data));
      try {
        setLoading(true);
        setError(null);

        console.log("[AUTH] calling loginWithTelegram...");
        const response = await loginWithTelegram(data);
        console.log("[AUTH] loginWithTelegram response:", JSON.stringify(response));
        setUser(response.user);

        // Трекинг регистрации/входа в Яндекс Метрику
        analytics.registration();

        // Редирект в личный кабинет
        console.log("[AUTH] redirecting to /app...");
        router.push("/app");
      } catch (err) {
        console.error("[AUTH] login error:", err);
        const message = err instanceof Error ? err.message : "Ошибка авторизации";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [router]
  );

  /**
   * Выход из системы.
   */
  const logout = useCallback(async () => {
    try {
      setLoading(true);
      await authLogout();
      setUser(null);

      // Редирект на страницу входа
      router.push("/login");
    } catch (err) {
      console.error("Ошибка выхода:", err);
    } finally {
      setLoading(false);
    }
  }, [router]);

  // Обработка transfer_token из URL (переход из VK Mini App / VK бота)
  useEffect(() => {
    async function handleTransferToken() {
      if (typeof window === "undefined") return;

      const params = new URLSearchParams(window.location.search);
      const transferToken = params.get("transfer_token");

      if (!transferToken) {
        // Нет токена — просто загружаем текущего пользователя
        refresh();
        return;
      }

      try {
        setLoading(true);

        // Обмениваем transfer_token на JWT
        const response = await fetch("/api/auth/transfer-token/exchange", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transfer_token: transferToken }),
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data.user);
          console.log("[AUTH] Transfer token exchanged successfully");
        } else {
          console.warn("[AUTH] Transfer token invalid or expired");
          // Токен невалиден — пробуем загрузить текущего пользователя
          await refresh();
        }
      } catch (err) {
        console.error("[AUTH] Error exchanging transfer token:", err);
        await refresh();
      } finally {
        setLoading(false);

        // Очищаем URL от transfer_token
        const url = new URL(window.location.href);
        url.searchParams.delete("transfer_token");
        window.history.replaceState({}, "", url.pathname + url.search);
      }
    }

    handleTransferToken();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const value: AuthContextState = {
    user,
    loading,
    error,
    login,
    logout,
    refresh,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Хук для доступа к контексту авторизации.
 *
 * @throws Error если используется вне AuthProvider
 */
export function useAuth(): AuthContextState {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth должен использоваться внутри AuthProvider");
  }

  return context;
}

/**
 * Хук для получения текущего пользователя.
 *
 * Возвращает null если не авторизован или идёт загрузка.
 */
export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

/**
 * Хук для проверки авторизации.
 *
 * @returns true если пользователь авторизован
 */
export function useIsAuthenticated(): boolean {
  const { user, loading } = useAuth();
  return !loading && user !== null;
}
