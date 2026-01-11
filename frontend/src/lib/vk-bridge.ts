/**
 * Хелперы для VK Bridge.
 *
 * Используются для взаимодействия с VK Mini App API:
 * - Инициализация приложения
 * - Получение данных пользователя
 * - Параметры запуска
 * - Safe Area Insets для Android
 *
 * ВАЖНО: VKWebAppInit вызывается через inline script в layout.tsx
 * ДО загрузки React, чтобы успеть до таймаута VK.
 */

// Типы для глобального vkBridge (загружается через CDN в layout)
interface VKBridge {
  send: <T = unknown>(method: string, params?: Record<string, unknown>) => Promise<T>;
  subscribe: (handler: (event: { detail: { type: string; data: unknown } }) => void) => void;
  unsubscribe: (handler: (event: { detail: { type: string; data: unknown } }) => void) => void;
}

declare global {
  interface Window {
    vkBridge?: VKBridge;
    __vkBridgeReady?: Promise<void>;
  }
}

/**
 * Получить VK Bridge (глобальный или npm fallback).
 */
async function getBridge(): Promise<VKBridge> {
  // Ждём загрузки bridge из CDN (layout.tsx)
  if (typeof window !== "undefined" && window.__vkBridgeReady) {
    await window.__vkBridgeReady;
  }

  // Используем глобальный vkBridge если есть
  if (typeof window !== "undefined" && window.vkBridge) {
    return window.vkBridge;
  }

  // Fallback на npm пакет
  const { default: bridge } = await import("@vkontakte/vk-bridge");
  return bridge as unknown as VKBridge;
}

/** Safe Area Insets для Android */
export interface SafeAreaInsets {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

/** Данные пользователя VK */
export interface VKUserInfo {
  id: number;
  first_name: string;
  last_name: string;
  photo_100: string;
}

/**
 * Инициализация VK Bridge.
 * ПРИМЕЧАНИЕ: VKWebAppInit уже вызван в layout.tsx через CDN,
 * эта функция ждёт готовности bridge.
 */
export async function initVKBridge(): Promise<void> {
  await getBridge();
}

/**
 * Получить данные текущего пользователя VK.
 */
export async function getVKUser(): Promise<VKUserInfo> {
  const bridge = await getBridge();
  const result = await bridge.send<{
    id: number;
    first_name: string;
    last_name: string;
    photo_100: string;
  }>("VKWebAppGetUserInfo");
  return {
    id: result.id,
    first_name: result.first_name,
    last_name: result.last_name,
    photo_100: result.photo_100,
  };
}

/**
 * Получить параметры запуска Mini App.
 */
export function getLaunchParams(): URLSearchParams {
  if (typeof window === "undefined") {
    return new URLSearchParams();
  }
  return new URLSearchParams(window.location.search);
}

/**
 * Получить ID сообщества (если запущено как плагин).
 */
export function getGroupId(): number | null {
  const params = getLaunchParams();
  const groupId = params.get("vk_group_id");
  return groupId ? parseInt(groupId, 10) : null;
}

/**
 * Получить VK user ID из параметров запуска.
 */
export function getVKUserId(): number | null {
  const params = getLaunchParams();
  const userId = params.get("vk_user_id");
  return userId ? parseInt(userId, 10) : null;
}

/**
 * Скачать файл (для PDF).
 */
export async function downloadFile(url: string, filename: string): Promise<void> {
  const bridge = await getBridge();
  await bridge.send("VKWebAppDownloadFile", { url, filename });
}

/**
 * Закрыть Mini App.
 */
export async function closeApp(): Promise<void> {
  const bridge = await getBridge();
  await bridge.send("VKWebAppClose", { status: "success" });
}

/**
 * Проверить, запущено ли приложение внутри VK.
 */
export function isVKEnvironment(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const params = getLaunchParams();
  return params.has("vk_user_id") || params.has("vk_app_id");
}

/**
 * Получить платформу запуска (android, ios, desktop).
 */
export function getVKPlatform(): string | null {
  const params = getLaunchParams();
  return params.get("vk_platform");
}

/**
 * Проверить, запущено ли на мобильном устройстве.
 */
export function isVKMobile(): boolean {
  const platform = getVKPlatform();
  return platform === "mobile_android" || platform === "mobile_iphone";
}

/**
 * Включить/выключить нативный свайп назад.
 * Вызывать при навигации между экранами.
 */
export async function setSwipeBack(enabled: boolean): Promise<void> {
  try {
    const bridge = await getBridge();
    await bridge.send("VKWebAppSetSwipeSettings", { history: enabled });
  } catch {
    // Игнорируем ошибки на desktop
  }
}

/**
 * Подписаться на события VK Bridge (insets, appearance).
 */
export function subscribeVKBridge(
  callback: (event: { type: string; data: unknown }) => void
): () => void {
  const handler = (event: { detail: { type: string; data: unknown } }) => {
    callback(event.detail);
  };

  // Подписываемся асинхронно
  getBridge().then((bridge) => {
    bridge.subscribe(handler);
  });

  return () => {
    getBridge().then((bridge) => {
      bridge.unsubscribe(handler);
    });
  };
}
