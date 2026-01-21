import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND_URL = process.env.BACKEND_URL || "http://backend:8000";

/**
 * POST /api/products/max-serial
 *
 * Получить максимальный серийный номер по списку баркодов.
 * Используется для автоподстановки стартового номера в режиме "Продолжить с №".
 */
export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("token")?.value;

    if (!token) {
      return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
    }

    // Валидация JSON
    let body;
    try {
      body = await request.json();
    } catch {
      return NextResponse.json(
        { error: "Невалидный JSON" },
        { status: 400 }
      );
    }

    // Проверяем что это массив
    if (!Array.isArray(body)) {
      return NextResponse.json(
        { error: "Требуется массив баркодов" },
        { status: 400 }
      );
    }

    // Таймаут 10 секунд
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/products/max-serial`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "Ошибка получения данных" },
          { status: response.status }
        );
      }

      const data = await response.json();
      return NextResponse.json(data);
    } catch (fetchError) {
      clearTimeout(timeout);
      if (fetchError instanceof Error && fetchError.name === "AbortError") {
        return NextResponse.json(
          { error: "Таймаут запроса" },
          { status: 504 }
        );
      }
      throw fetchError;
    }
  } catch (error) {
    console.error("Ошибка получения max serial:", error);
    return NextResponse.json(
      { error: "Внутренняя ошибка сервера" },
      { status: 500 }
    );
  }
}
