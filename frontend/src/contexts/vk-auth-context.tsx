"use client";

/**
 * React Context для авторизации через VK Mini App.
 *
 * Автоматически:
 * - Инициализирует VK Bridge
 * - Получает данные пользователя VK
 * - Авторизует в backend через /api/v1/auth/vk
 * - Получает Safe Area Insets для Android
 * - Синхронизирует тему с VK
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type { User } from "@/types/api";
import {
  initVKBridge,
  getVKUser,
  getGroupId,
  setSwipeBack,
  subscribeVKBridge,
  getVKConfig,
  type VKUserInfo,
  type SafeAreaInsets,
} from "@/lib/vk-bridge";

/** Состояние контекста VK авторизации */
interface VKAuthContextState {
  /** Данные пользователя VK */
  vkUser: VKUserInfo | null;
  /** Пользователь из backend */
  user: User | null;
  /** ID сообщества (если плагин) */
  groupId: number | null;
  /** Идёт загрузка */
  loading: boolean;
  /** Ошибка */
  error: string | null;
  /** Авторизован ли пользователь */
  isAuthenticated: boolean;
  /** Safe Area Insets для Android */
  insets: SafeAreaInsets;
  /** Цветовая схема VK (dark/light) */
  colorScheme: "dark" | "light";
  /** Обновить данные */
  refresh: () => Promise<void>;
}

const VKAuthContext = createContext<VKAuthContextState | undefined>(undefined);

interface VKAuthProviderProps {
  children: ReactNode;
}

/** Дефолтные insets */
const defaultInsets: SafeAreaInsets = { top: 0, bottom: 0, left: 0, right: 0 };

/**
 * Провайдер VK авторизации.
 */
export function VKAuthProvider({ children }: VKAuthProviderProps) {
  const [vkUser, setVkUser] = useState<VKUserInfo | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [groupId, setGroupId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [insets, setInsets] = useState<SafeAreaInsets>(defaultInsets);
  const [colorScheme, setColorScheme] = useState<"dark" | "light">("light");

  /**
   * Авторизация в backend через VK ID.
   */
  const authWithBackend = useCallback(async (vkUserInfo: VKUserInfo) => {
    const response = await fetch("/api/auth/vk", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        vk_user_id: vkUserInfo.id,
        first_name: vkUserInfo.first_name,
        last_name: vkUserInfo.last_name,
      }),
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Ошибка авторизации VK");
    }

    const data = await response.json();
    return data.user as User;
  }, []);

  /**
   * Инициализация VK Bridge и авторизация.
   */
  const init = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Инициализация VK Bridge
      await initVKBridge();

      // Получаем ID сообщества (если плагин)
      const gId = getGroupId();
      setGroupId(gId);

      // Включаем свайп назад для выхода из Mini App
      await setSwipeBack(true);

      // Получаем данные пользователя VK
      const vkUserInfo = await getVKUser();
      setVkUser(vkUserInfo);

      // Авторизуемся в backend
      const backendUser = await authWithBackend(vkUserInfo);
      setUser(backendUser);
    } catch (err) {
      console.error("VK Auth error:", err);
      setError(err instanceof Error ? err.message : "Ошибка авторизации VK");
    } finally {
      setLoading(false);
    }
  }, [authWithBackend]);

  /**
   * Обновить данные пользователя.
   */
  const refresh = useCallback(async () => {
    if (vkUser) {
      try {
        const backendUser = await authWithBackend(vkUser);
        setUser(backendUser);
      } catch (err) {
        console.error("VK refresh error:", err);
      }
    }
  }, [vkUser, authWithBackend]);

  useEffect(() => {
    init();

    // Подписка на обновления конфига VK (insets, appearance)
    const unsubscribe = subscribeVKBridge((event) => {
      if (event.type === "VKWebAppUpdateConfig") {
        const data = event.data as {
          appearance?: "dark" | "light";
          insets?: SafeAreaInsets;
        };
        if (data.appearance) {
          setColorScheme(data.appearance);
        }
        if (data.insets) {
          setInsets(data.insets);
        }
      }
    });

    // Получаем начальный конфиг
    getVKConfig().then((config) => {
      if (config.appearance) {
        setColorScheme(config.appearance);
      }
      if (config.insets) {
        setInsets(config.insets);
      }
    });

    return unsubscribe;
  }, [init]);

  return (
    <VKAuthContext.Provider
      value={{
        vkUser,
        user,
        groupId,
        loading,
        error,
        isAuthenticated: !!user,
        insets,
        colorScheme,
        refresh,
      }}
    >
      {children}
    </VKAuthContext.Provider>
  );
}

/**
 * Хук для доступа к VK авторизации.
 */
export function useVKAuth() {
  const context = useContext(VKAuthContext);
  if (context === undefined) {
    throw new Error("useVKAuth must be used within a VKAuthProvider");
  }
  return context;
}
