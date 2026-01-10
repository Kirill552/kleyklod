/**
 * API Route: История платежей.
 *
 * Проксирует запрос к FastAPI /api/v1/payments/history с JWT авторизацией.
 */

import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function GET(_request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    // Получаем историю платежей напрямую с JWT авторизацией
    const response = await fetch(`${API_URL}/api/v1/payments/history`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      if (response.status === 404) {
        // Нет платежей - возвращаем пустой массив
        return NextResponse.json([]);
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка загрузки истории платежей" },
        { status: response.status }
      );
    }

    const payments = await response.json();
    return NextResponse.json(payments);
  } catch (error) {
    console.error("Ошибка загрузки истории платежей:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
