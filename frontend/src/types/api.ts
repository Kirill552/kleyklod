/**
 * TypeScript типы для API.
 *
 * Описывают структуру данных, возвращаемых бэкендом.
 */

// ============================================
// Пользователь
// ============================================

/** Тарифный план пользователя */
export type UserPlan = "free" | "pro" | "enterprise";

/** Данные пользователя */
export interface User {
  id: string;
  telegram_id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  photo_url: string | null;
  plan: UserPlan;
  plan_expires_at: string | null;
  created_at: string;
}

/** Статистика использования */
export interface UserStats {
  today_used: number;
  today_limit: number;
  total_generated: number;
  this_month: number;
}

// ============================================
// Авторизация
// ============================================

/** Данные от Telegram Login Widget */
export interface TelegramAuthData {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

/** Ответ на авторизацию (без токена — он в cookie) */
export interface AuthResponse {
  user: User;
}

// ============================================
// Генерация этикеток
// ============================================

/** Формат размещения этикеток */
export type LabelFormat = "combined" | "separate";

/** Статус Pre-flight проверки */
export type PreflightStatus = "ok" | "warning" | "error";

/** Результат Pre-flight проверки */
export interface PreflightResult {
  status: PreflightStatus;
  check_name: string;
  message: string;
  details?: Record<string, unknown>;
}

/** Запись о генерации */
export interface Generation {
  id: string;
  labels_count: number;
  preflight_passed: boolean;
  created_at: string;
  file_path: string | null;
}

/** Ответ на запрос списка генераций */
export interface GenerationsResponse {
  items: Generation[];
  total: number;
}

// ============================================
// Платежи
// ============================================

/** Статус платежа */
export type PaymentStatus = "pending" | "completed" | "failed" | "refunded";

/** Запись о платеже */
export interface Payment {
  id: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  created_at: string;
}

/** Тарифный план для отображения */
export interface PricingPlan {
  id: string;
  name: string;
  price_rub: number;
  features: string[];
  is_popular: boolean;
}

// ============================================
// API ключи
// ============================================

/** Информация об API ключе */
export interface ApiKeyInfo {
  prefix: string | null;
  created_at: string | null;
  last_used_at: string | null;
}

/** Ответ при создании API ключа */
export interface ApiKeyCreatedResponse {
  api_key: string;
  warning: string;
}

// ============================================
// API ошибки
// ============================================

/** Стандартная ошибка API */
export interface ApiErrorResponse {
  detail: string;
  code?: string;
}
