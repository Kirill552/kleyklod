/**
 * Типы для авторизации через Telegram
 */

/**
 * Данные пользователя от Telegram Widget
 */
export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

/**
 * Пользователь в системе
 */
export interface User {
  id: number;
  telegram_id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  created_at: string;
  daily_limit: number;
  used_today: number;
}

/**
 * Ответ от API при авторизации
 */
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
