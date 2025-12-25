/**
 * API Route: История генераций.
 *
 * Проксирует запрос к FastAPI с токеном из cookie.
 */

import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  // Получаем параметры пагинации
  const searchParams = request.nextUrl.searchParams;
  const page = searchParams.get("page") || "1";
  const limit = searchParams.get("limit") || "10";

  try {
    const response = await fetch(
      `${API_URL}/api/v1/generations?page=${page}&limit=${limit}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка загрузки истории" },
        { status: response.status }
      );
    }

    const generations = await response.json();
    return NextResponse.json(generations);
  } catch (error) {
    console.error("Ошибка загрузки истории:", error);
    return NextResponse.json(
      { error: "Ошибка сервера" },
      { status: 500 }
    );
  }
}
