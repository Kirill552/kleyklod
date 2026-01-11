/**
 * Хелперы для VK Bridge.
 *
 * Используется npm пакет @vkontakte/vk-bridge (рекомендация VK).
 * VKWebAppInit вызывается СРАЗУ при импорте модуля для быстрой инициализации.
 */

import bridge from "@vkontakte/vk-bridge";

// Promise инициализации (singleton)
let initPromise: Promise<void> | null = null;

/**
 * Инициализация VK Bridge - вызывается автоматически при импорте.
 * VKWebAppInit должен быть вызван в первые 30 секунд!
 */
function initBridge(): Promise<void> {
  if (initPromise) return initPromise;

  initPromise = (async () => {
    if (typeof window === "undefined") return;

    try {
      await bridge.send("VKWebAppInit");
      console.log("[VK Bridge] VKWebAppInit success");
    } catch (err) {
      console.error("[VK Bridge] VKWebAppInit error:", err);
    }
  })();

  return initPromise;
}

// Вызываем инициализацию СРАЗУ при импорте модуля
if (typeof window !== "undefined") {
  initBridge();
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
 * Ожидание инициализации VK Bridge.
 * Вызывается автоматически при импорте, эта функция просто ждёт завершения.
 */
export async function initVKBridge(): Promise<void> {
  await initBridge();
}

/**
 * Получить данные текущего пользователя VK.
 */
export async function getVKUser(): Promise<VKUserInfo> {
  await initBridge();
  const result = await bridge.send("VKWebAppGetUserInfo");
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
  await initBridge();
  await bridge.send("VKWebAppDownloadFile", { url, filename });
}

/**
 * Закрыть Mini App.
 */
export async function closeApp(): Promise<void> {
  await initBridge();
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
    await initBridge();
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

  bridge.subscribe(handler);

  return () => {
    bridge.unsubscribe(handler);
  };
}

/**
 * Получить конфигурацию VK (appearance, insets).
 */
export async function getVKConfig(): Promise<{
  appearance?: "dark" | "light";
  insets?: SafeAreaInsets;
}> {
  try {
    await initBridge();
    const result = await bridge.send("VKWebAppGetConfig");
    return result as { appearance?: "dark" | "light"; insets?: SafeAreaInsets };
  } catch {
    return {};
  }
}

