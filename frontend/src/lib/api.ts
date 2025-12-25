/**
 * API клиент для работы с бэкендом.
 *
 * Все запросы идут через Next.js API Routes, которые добавляют
 * Authorization header из HttpOnly cookie.
 */

import type { UserStats, Generation, GenerationsResponse } from "@/types/api";

/**
 * Базовый fetch с credentials для отправки cookies.
 */
async function apiFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  return fetch(url, {
    ...options,
    credentials: "include", // Отправляем cookies
  });
}

/**
 * Типизированный GET запрос через Next.js API.
 */
export async function apiGet<T>(url: string): Promise<T> {
  const response = await apiFetch(url);

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Не авторизован");
    }
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || "Ошибка запроса");
  }

  return response.json();
}

/**
 * Типизированный POST запрос через Next.js API.
 */
export async function apiPost<T, R = T>(url: string, data: T): Promise<R> {
  const response = await apiFetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Не авторизован");
    }
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || "Ошибка запроса");
  }

  return response.json();
}

/**
 * POST запрос с FormData (для загрузки файлов).
 */
export async function apiPostFormData<R>(
  url: string,
  formData: FormData
): Promise<R> {
  const response = await apiFetch(url, {
    method: "POST",
    body: formData,
    // НЕ устанавливаем Content-Type — браузер сам добавит с boundary
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Не авторизован");
    }
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || "Ошибка запроса");
  }

  return response.json();
}

// ============================================
// API функции для конкретных эндпоинтов
// ============================================

/**
 * Получить статистику использования пользователя.
 */
export async function getUserStats(): Promise<UserStats> {
  return apiGet<UserStats>("/api/user/stats");
}

/**
 * Получить историю генераций.
 */
export async function getGenerations(
  page: number = 1,
  limit: number = 10
): Promise<GenerationsResponse> {
  return apiGet<GenerationsResponse>(
    `/api/generations?page=${page}&limit=${limit}`
  );
}

/**
 * Скачать файл генерации.
 */
export async function downloadGeneration(generationId: string): Promise<Blob> {
  const response = await apiFetch(`/api/generations/${generationId}/download`);

  if (!response.ok) {
    throw new Error("Ошибка скачивания файла");
  }

  return response.blob();
}

/**
 * Генерация этикеток.
 */
export interface GenerateLabelsRequest {
  codes: string[];
}

export interface GenerateLabelsResponse {
  generation_id: string;
  labels_count: number;
  preflight_passed: boolean;
  warnings: string[];
}

export async function generateLabels(
  wbPdf: File,
  codes: string[]
): Promise<GenerateLabelsResponse> {
  const formData = new FormData();
  formData.append("wb_pdf", wbPdf);
  formData.append("codes", JSON.stringify(codes));

  return apiPostFormData<GenerateLabelsResponse>("/api/labels/generate", formData);
}
