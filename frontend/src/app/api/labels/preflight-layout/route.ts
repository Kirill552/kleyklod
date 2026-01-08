/**
 * API Route: Pre-flight проверка данных этикетки ПЕРЕД генерацией.
 *
 * Проксирует запрос к FastAPI для проверки полей:
 * - Количество активных полей vs лимит шаблона
 * - Ширина текста — поместится ли при минимальном шрифте
 * - Совместимость layout и размера этикетки
 */

import { cookies, headers } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

function isLocalhost(host: string | null): boolean {
  return host?.includes("localhost") || host?.includes("127.0.0.1") || false;
}

export async function POST(request: NextRequest) {
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

  try {
    // Получаем JSON из запроса
    const body = await request.json();

    // Пересылаем на FastAPI
    const response = await fetch(`${API_URL}/api/v1/labels/preflight-layout`, {
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

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка проверки данных" },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка preflight проверки:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
