/**
 * API Route: Количество карточек товаров.
 *
 * Проксирует запросы к FastAPI с токеном из cookie.
 * GET - получить количество карточек (0 для FREE, реальное для PRO/ENTERPRISE)
 */

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

/**
 * GET /api/products/count - Получить количество карточек товаров
 */
export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const url = `${API_URL}/api/v1/products/count`;

    const response = await fetch(url, {
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
        { error: error.detail || "Ошибка получения количества карточек" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Ошибка запроса количества карточек:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
