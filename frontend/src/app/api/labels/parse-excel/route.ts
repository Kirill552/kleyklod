/**
 * API Route: Анализ Excel файла с баркодами.
 *
 * Проксирует запрос к FastAPI для получения превью данных.
 * Реализует Human-in-the-loop паттерн — пользователь проверяет
 * автоматически определённую колонку перед генерацией.
 */

import { cookies, headers } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

// Проверка localhost для dev mode
function isLocalhost(host: string | null): boolean {
  return host?.includes("localhost") || host?.includes("127.0.0.1") || false;
}

export async function POST(request: NextRequest) {
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
    // Получаем FormData из запроса
    const formData = await request.formData();

    // Пересылаем FormData на FastAPI
    const response = await fetch(`${API_URL}/api/v1/labels/parse-excel`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка анализа Excel" },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка анализа Excel:", error);
    return NextResponse.json(
      { error: "Ошибка сервера" },
      { status: 500 }
    );
  }
}
