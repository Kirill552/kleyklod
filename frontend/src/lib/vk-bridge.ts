/**
 * Хелперы для VK Bridge.
 *
 * Используются для взаимодействия с VK Mini App API:
 * - Инициализация приложения
 * - Получение данных пользователя
 * - Параметры запуска
 * - Safe Area Insets для Android
 */

import bridge from "@vkontakte/vk-bridge";

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
 * Вызывать при старте Mini App.
 */
export async function initVKBridge(): Promise<void> {
  await bridge.send("VKWebAppInit");
}

/**
 * Получить данные текущего пользователя VK.
 */
export async function getVKUser(): Promise<VKUserInfo> {
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
  await bridge.send("VKWebAppDownloadFile", { url, filename });
}

/**
 * Открыть внешнюю ссылку (для оплаты через YooKassa).
 * VK Mini Apps поддерживают window.open() - VK перехватывает и открывает в системном браузере.
 */
export function openExternalLink(url: string): void {
  window.open(url, "_blank");
}

/**
 * Закрыть Mini App.
 */
export async function closeApp(): Promise<void> {
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
  return () => bridge.unsubscribe(handler);
}
