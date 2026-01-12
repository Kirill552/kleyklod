/**
 * API Route: Настройки генерации этикеток пользователя.
 *
 * GET - получить текущие настройки
 * PUT - обновить настройки
 */

import { NextRequest, NextResponse } from "next/server";
import { getAuthToken } from "@/lib/server-auth";

const API_URL = process.env.API_URL || "http://localhost:8000";

/**
 * GET /api/user/preferences
 * Получить настройки генерации этикеток.
 */
export async function GET() {
  const token = await getAuthToken();

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/users/me/preferences`, {
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
        { error: error.detail || "Ошибка загрузки настроек" },
        { status: response.status }
      );
    }

    const preferences = await response.json();
    return NextResponse.json(preferences);
  } catch (error) {
    console.error("Ошибка запроса настроек:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}

/**
 * PUT /api/user/preferences
 * Обновить настройки генерации этикеток.
 */
export async function PUT(request: NextRequest) {
  const token = await getAuthToken(request);

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const body = await request.json();

    const response = await fetch(`${API_URL}/api/v1/users/me/preferences`, {
      method: "PUT",
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
        { error: error.detail || "Ошибка обновления настроек" },
        { status: response.status }
      );
    }

    const preferences = await response.json();
    return NextResponse.json(preferences);
  } catch (error) {
    console.error("Ошибка обновления настроек:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
