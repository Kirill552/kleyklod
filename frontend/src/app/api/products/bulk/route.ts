/**
 * API Route: Массовый UPSERT карточек товаров.
 *
 * Проксирует запросы к FastAPI /api/v1/products/bulk с токеном из cookie.
 * POST - создать/обновить несколько карточек
 */

import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

/**
 * POST /api/products/bulk - Массовый upsert карточек товаров
 *
 * Body: ProductCardCreate[]
 * Response: { created: number, updated: number, skipped: number }
 */
export async function POST(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const body = await request.json();

    const response = await fetch(`${API_URL}/api/v1/products/bulk`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      if (response.status === 403) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "База карточек недоступна для вашего тарифа" },
          { status: 403 }
        );
      }
      if (response.status === 422) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "Ошибка валидации данных" },
          { status: 422 }
        );
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка сохранения карточек" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Ошибка bulk upsert карточек:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
