/**
 * API клиент для работы с бэкендом.
 *
 * Все запросы идут через Next.js API Routes, которые добавляют
 * Authorization header из HttpOnly cookie.
 */

import type {
  UserStats,
  Generation,
  GenerationsResponse,
  ApiKeyInfo,
  ApiKeyCreatedResponse,
  LabelFormat,
} from "@/types/api";

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
  label_format?: LabelFormat;
}

/** Результат Pre-flight проверки */
export interface PreflightCheck {
  check_name: string;
  status: "ok" | "warning" | "error";
  message: string;
  details?: Record<string, unknown>;
}

export interface PreflightResult {
  overall_status: "ok" | "warning" | "error";
  checks: PreflightCheck[];
  can_proceed: boolean;
}

export interface GenerateLabelsResponse {
  success: boolean;
  labels_count: number;
  pages_count: number;
  label_format: LabelFormat;
  preflight: PreflightResult | null;
  download_url: string | null;
  file_id: string | null;
  message: string;
}

export async function generateLabels(
  wbPdf: File,
  codes: string[],
  labelFormat: LabelFormat = "combined"
): Promise<GenerateLabelsResponse> {
  const formData = new FormData();
  formData.append("wb_pdf", wbPdf);
  formData.append("codes", JSON.stringify(codes));
  formData.append("label_format", labelFormat);

  return apiPostFormData<GenerateLabelsResponse>("/api/labels/generate", formData);
}

// ============================================
// API ключи (только для Enterprise)
// ============================================

/**
 * Получить информацию о текущем API ключе.
 */
export async function getApiKeyInfo(): Promise<ApiKeyInfo> {
  return apiGet<ApiKeyInfo>("/api/keys");
}

/**
 * Создать новый API ключ.
 */
export async function createApiKey(): Promise<ApiKeyCreatedResponse> {
  const response = await apiFetch("/api/keys", {
    method: "POST",
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Не авторизован");
    }
    if (response.status === 403) {
      throw new Error("API ключи доступны только для Enterprise подписки");
    }
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка создания ключа");
  }

  return response.json();
}

/**
 * Отозвать API ключ.
 */
export async function revokeApiKey(): Promise<{ message: string }> {
  const response = await apiFetch("/api/keys", {
    method: "DELETE",
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("API ключ не найден");
    }
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка отзыва ключа");
  }

  return response.json();
}

// ============================================
// Платежи ЮКасса
// ============================================

/**
 * Запрос создания платежа.
 */
export interface CreatePaymentRequest {
  plan: "pro" | "enterprise";
  telegram_id?: number;
}

/**
 * Ответ с данными платежа.
 */
export interface CreatePaymentResponse {
  payment_id: string;
  confirmation_url: string;
  amount: number;
  currency: string;
}

/**
 * Создать платеж через ЮКассу.
 */
export async function createPayment(
  plan: "pro" | "enterprise",
  telegram_id?: number
): Promise<CreatePaymentResponse> {
  return apiPost<CreatePaymentRequest, CreatePaymentResponse>(
    "/api/payments/create",
    { plan, telegram_id }
  );
}

// ============================================
// Обратная связь
// ============================================

/**
 * Ответ на запрос отправки обратной связи.
 */
export interface FeedbackResponse {
  success: boolean;
  message: string;
}

/**
 * Статус обратной связи пользователя.
 */
export interface FeedbackStatusResponse {
  feedback_submitted: boolean;
  generations_count: number;
}

/**
 * Отправить обратную связь.
 */
export async function submitFeedback(
  text: string,
  source: "web" | "bot" = "web"
): Promise<FeedbackResponse> {
  return apiPost<{ text: string; source: string }, FeedbackResponse>(
    "/api/feedback",
    { text, source }
  );
}

/**
 * Получить статус обратной связи пользователя.
 */
export async function getFeedbackStatus(): Promise<FeedbackStatusResponse> {
  return apiGet<FeedbackStatusResponse>("/api/feedback/status");
}
