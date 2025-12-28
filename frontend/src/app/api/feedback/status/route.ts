/**
 * API Route: Статус обратной связи.
 *
 * GET - получение статуса (был ли отправлен отзыв, количество генераций)
 * Проксирует запрос к FastAPI /api/v1/feedback/status
 */

import { cookies, headers } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

// Проверка localhost для dev mode
function isLocalhost(host: string | null): boolean {
  return host?.includes("localhost") || host?.includes("127.0.0.1") || false;
}

export async function GET() {
  const cookieStore = await cookies();
  const headersList = await headers();
  const host = headersList.get("host");

  // На localhost используем dev-token-bypass
  const token = cookieStore.get("token")?.value ||
    (isLocalhost(host) ? "dev-token-bypass" : null);

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/feedback/status`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка получения статуса" },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка получения статуса обратной связи:", error);
    return NextResponse.json(
      { error: "Ошибка сервера" },
      { status: 500 }
    );
  }
}
