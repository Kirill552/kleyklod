/**
 * API клиент для работы с бэкендом.
 *
 * Все запросы идут через Next.js API Routes, которые добавляют
 * Authorization header из HttpOnly cookie.
 */

import type {
  UserStats,
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
  // GTIN warning для микс-поставок
  gtin_warning?: boolean;
  gtin_count?: number;
}

// ============================================
// Типы для auto-detect и Excel генерации
// ============================================

/** Тип загруженного файла */
export type FileType = "pdf" | "excel" | "unknown";

/** Шаблон этикетки */
export type LabelLayout = "basic" | "professional";

/** Размер этикетки */
export type LabelSize = "58x40" | "58x30" | "58x60";

/** Элемент превью из Excel */
export interface ExcelSampleItem {
  barcode: string;
  article: string | null;
  size: string | null;
  color: string | null;
  name?: string | null;
  country?: string | null;
  composition?: string | null;
  row_number: number;
}

/** Ответ парсинга Excel */
export interface ExcelParseResponse {
  success: boolean;
  detected_column: string | null;
  all_columns: string[];
  barcode_candidates: string[];
  total_rows: number;
  sample_items: ExcelSampleItem[];
  message: string;
}

/** Результат автоопределения типа файла */
export interface FileDetectionResult {
  file_type: FileType;
  filename: string;
  size_bytes: number;
  // Для PDF
  pages_count?: number;
  // Для Excel
  rows_count?: number;
  columns?: string[];
  detected_barcode_column?: string;
  sample_items?: ExcelSampleItem[];
  error?: string;
}

/** Параметры генерации из Excel с полным дизайном этикетки */
export interface GenerateFromExcelParams {
  excelFile: File;
  codesFile?: File;
  codes?: string[];
  barcodeColumn?: string;
  layout: LabelLayout;
  labelSize: LabelSize;
  labelFormat: LabelFormat;
  // Данные организации
  organizationName?: string;
  inn?: string;
  organizationAddress?: string;
  productionCountry?: string;
  certificateNumber?: string;
  // Дополнительные поля для профессионального шаблона
  importer?: string;
  manufacturer?: string;
  productionDate?: string;
  // Флаги отображения полей (базовый шаблон)
  showArticle: boolean;
  showSizeColor: boolean;
  showName: boolean;
  showOrganization?: boolean;
  showInn?: boolean;
  showCountry?: boolean;
  showComposition?: boolean;
  // Флаги отображения полей (профессиональный шаблон)
  showBrand?: boolean;
  showImporter?: boolean;
  showManufacturer?: boolean;
  showAddress?: boolean;
  showProductionDate?: boolean;
  showCertificate?: boolean;
}

/** Ответ генерации из Excel */
export interface GenerateFromExcelResponse {
  success: boolean;
  labels_count: number;
  label_format: LabelFormat;
  preflight: PreflightResult | null;
  download_url: string | null;
  file_id: string | null;
  message: string;
  gtin_warning?: boolean;
  gtin_count?: number;
}

/**
 * Анализ Excel файла для получения превью колонок и данных.
 */
export async function parseExcel(file: File): Promise<ExcelParseResponse> {
  const formData = new FormData();
  formData.append("barcodes_excel", file);

  const response = await fetch("/api/labels/parse-excel", {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка анализа Excel");
  }

  return response.json();
}

/**
 * Автоопределение типа файла (PDF или Excel).
 */
export async function detectFile(file: File): Promise<FileDetectionResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/labels/detect-file", {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка определения типа файла");
  }

  return response.json();
}

/**
 * Генерация этикеток из Excel с полным дизайном.
 */
export async function generateFromExcel(
  params: GenerateFromExcelParams
): Promise<GenerateFromExcelResponse> {
  const formData = new FormData();

  // Файлы
  formData.append("barcodes_excel", params.excelFile);
  if (params.codesFile) {
    formData.append("codes_file", params.codesFile);
  }

  // Коды (если переданы напрямую)
  if (params.codes && params.codes.length > 0) {
    formData.append("codes", JSON.stringify(params.codes));
  }

  // Параметры
  if (params.barcodeColumn) {
    formData.append("barcode_column", params.barcodeColumn);
  }
  formData.append("layout", params.layout);
  formData.append("label_size", params.labelSize);
  formData.append("label_format", params.labelFormat);

  // Данные организации
  if (params.organizationName) {
    formData.append("organization_name", params.organizationName);
  }
  if (params.inn) {
    formData.append("inn", params.inn);
  }
  if (params.organizationAddress) {
    formData.append("organization_address", params.organizationAddress);
  }
  if (params.productionCountry) {
    formData.append("production_country", params.productionCountry);
  }
  if (params.certificateNumber) {
    formData.append("certificate_number", params.certificateNumber);
  }

  // Дополнительные поля для профессионального шаблона
  if (params.importer) {
    formData.append("importer", params.importer);
  }
  if (params.manufacturer) {
    formData.append("manufacturer", params.manufacturer);
  }
  if (params.productionDate) {
    formData.append("production_date", params.productionDate);
  }

  // Флаги отображения полей (базовый шаблон)
  formData.append("show_article", String(params.showArticle));
  formData.append("show_size_color", String(params.showSizeColor));
  formData.append("show_name", String(params.showName));
  formData.append("show_organization", String(params.showOrganization ?? true));
  formData.append("show_inn", String(params.showInn ?? false));
  formData.append("show_country", String(params.showCountry ?? false));
  formData.append("show_composition", String(params.showComposition ?? false));

  // Флаги отображения полей (профессиональный шаблон)
  formData.append("show_brand", String(params.showBrand ?? false));
  formData.append("show_importer", String(params.showImporter ?? false));
  formData.append("show_manufacturer", String(params.showManufacturer ?? false));
  formData.append("show_address", String(params.showAddress ?? false));
  formData.append("show_production_date", String(params.showProductionDate ?? false));
  formData.append("show_certificate", String(params.showCertificate ?? false));

  const response = await fetch("/api/labels/generate-from-excel", {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Не авторизован");
    }
    if (response.status === 429) {
      throw new Error("Превышен лимит генераций");
    }
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Ошибка генерации этикеток");
  }

  return response.json();
}

/** Параметры генерации этикеток */
export interface GenerateLabelsParams {
  wbPdf?: File;
  barcodesExcel?: File;
  barcodeColumn?: string;
  codesFile?: File;
  codes?: string[];
  template?: string;
  labelFormat?: LabelFormat;
}

/**
 * Генерация этикеток с поддержкой PDF или Excel источника баркодов.
 */
export async function generateLabels(
  wbPdfOrParams: File | GenerateLabelsParams,
  codes?: string[],
  labelFormat: LabelFormat = "combined"
): Promise<GenerateLabelsResponse> {
  const formData = new FormData();

  // Обратная совместимость со старым API
  if (wbPdfOrParams instanceof File) {
    formData.append("wb_pdf", wbPdfOrParams);
    if (codes) {
      formData.append("codes", JSON.stringify(codes));
    }
    formData.append("label_format", labelFormat);
  } else {
    // Новый API с объектом параметров
    const params = wbPdfOrParams;

    if (params.wbPdf) {
      formData.append("wb_pdf", params.wbPdf);
    }
    if (params.barcodesExcel) {
      formData.append("barcodes_excel", params.barcodesExcel);
    }
    if (params.barcodeColumn) {
      formData.append("barcode_column", params.barcodeColumn);
    }
    if (params.codesFile) {
      formData.append("codes_file", params.codesFile);
    }
    if (params.codes && params.codes.length > 0) {
      formData.append("codes", JSON.stringify(params.codes));
    }
    if (params.template) {
      formData.append("template", params.template);
    }
    formData.append("label_format", params.labelFormat || "combined");
  }

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

/**
 * Элемент истории платежей.
 */
export interface PaymentHistoryItem {
  id: string;
  plan: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}

/**
 * Получить историю платежей.
 */
export async function getPaymentHistory(): Promise<PaymentHistoryItem[]> {
  return apiGet<PaymentHistoryItem[]>("/api/payments/history");
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

// ============================================
// Настройки генерации этикеток
// ============================================

/**
 * Настройки генерации этикеток пользователя.
 */
export interface UserLabelPreferences {
  organization_name: string | null;
  inn: string | null;
  organization_address: string | null;
  production_country: string | null;
  certificate_number: string | null;
  preferred_layout: LabelLayout;
  preferred_label_size: LabelSize;
  preferred_format: LabelFormat;
  show_article: boolean;
  show_size_color: boolean;
  show_name: boolean;
}

/**
 * Обновление настроек (partial).
 */
export interface UserLabelPreferencesUpdate {
  organization_name?: string | null;
  inn?: string | null;
  organization_address?: string | null;
  production_country?: string | null;
  certificate_number?: string | null;
  preferred_layout?: LabelLayout;
  preferred_label_size?: LabelSize;
  preferred_format?: LabelFormat;
  show_article?: boolean;
  show_size_color?: boolean;
  show_name?: boolean;
}

/**
 * Получить настройки генерации этикеток пользователя.
 */
export async function getUserPreferences(): Promise<UserLabelPreferences> {
  return apiGet<UserLabelPreferences>("/api/user/preferences");
}

/**
 * Обновить настройки генерации этикеток.
 */
export async function updateUserPreferences(
  data: UserLabelPreferencesUpdate
): Promise<UserLabelPreferences> {
  const response = await apiFetch("/api/user/preferences", {
    method: "PUT",
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
    throw new Error(error.detail || error.error || "Ошибка обновления настроек");
  }

  return response.json();
}
