/**
 * API Route: Список карточек товаров.
 *
 * Проксирует запросы к FastAPI с токеном из cookie.
 * GET - получить список карточек
 */

import { cookies, headers } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

// Проверка localhost для dev mode
function isLocalhost(host: string | null): boolean {
  return host?.includes("localhost") || host?.includes("127.0.0.1") || false;
}

/**
 * GET /api/products - Получить список карточек товаров
 */
export async function GET(request: NextRequest) {
  const cookieStore = await cookies();
  const headersList = await headers();
  const host = headersList.get("host");

  // На localhost используем dev-token-bypass
  const token =
    cookieStore.get("token")?.value ||
    (isLocalhost(host) ? "dev-token-bypass" : null);

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  // Получаем query параметры
  const { searchParams } = new URL(request.url);
  const search = searchParams.get("search") || "";
  const limit = searchParams.get("limit") || "20";
  const offset = searchParams.get("offset") || "0";

  try {
    const url = new URL(`${API_URL}/api/v1/products`);
    if (search) url.searchParams.set("search", search);
    url.searchParams.set("limit", limit);
    url.searchParams.set("offset", offset);

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      if (response.status === 403) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "Доступ запрещён" },
          { status: 403 }
        );
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка загрузки карточек" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Ошибка запроса карточек:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
