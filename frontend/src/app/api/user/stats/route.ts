/**
 * API Route: Статистика пользователя.
 *
 * Проксирует запрос к FastAPI с токеном из cookie.
 */

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/users/me/stats`, {
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
        { error: error.detail || "Ошибка загрузки статистики" },
        { status: response.status }
      );
    }

    const stats = await response.json();
    return NextResponse.json(stats);
  } catch (error) {
    console.error("Ошибка запроса статистики:", error);
    return NextResponse.json(
      { error: "Ошибка сервера" },
      { status: 500 }
    );
  }
}
