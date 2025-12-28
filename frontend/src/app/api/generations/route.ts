/**
 * API Route: История генераций.
 *
 * Проксирует запрос к FastAPI с токеном из cookie.
 */

import { cookies, headers } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

// Проверка localhost для dev mode
function isLocalhost(host: string | null): boolean {
  return host?.includes("localhost") || host?.includes("127.0.0.1") || false;
}

export async function GET(request: NextRequest) {
  const cookieStore = await cookies();
  const headersList = await headers();
  const host = headersList.get("host");

  // На localhost используем dev-token-bypass
  const token = cookieStore.get("token")?.value ||
    (isLocalhost(host) ? "dev-token-bypass" : null);

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
