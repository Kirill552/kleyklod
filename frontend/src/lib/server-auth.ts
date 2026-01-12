/**
 * Серверные утилиты авторизации для API routes.
 *
 * Поддерживает два способа передачи токена:
 * 1. HttpOnly cookie "token" (основной, для обычных браузеров)
 * 2. Header "X-VK-Token" (для VK Mini App на iOS, где cookies блокируются)
 */

import { cookies, headers } from "next/headers";
import { NextRequest } from "next/server";

/**
 * Получить токен авторизации из запроса.
 * Приоритет: cookie > X-VK-Token header
 *
 * @param request - NextRequest объект (опционально для POST/PUT)
 */
export async function getAuthToken(request?: NextRequest): Promise<string | null> {
  // Сначала пробуем cookie (работает в обычных браузерах)
  const cookieStore = await cookies();
  const cookieToken = cookieStore.get("token")?.value;

  if (cookieToken) {
    return cookieToken;
  }

  // Fallback: X-VK-Token header (для iOS VK Mini App)
  // Получаем header из request или из headers()
  let headerToken: string | null = null;

  if (request) {
    headerToken = request.headers.get("X-VK-Token");
  } else {
    const headerStore = await headers();
    headerToken = headerStore.get("X-VK-Token");
  }

  return headerToken;
}
