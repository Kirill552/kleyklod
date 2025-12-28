/**
 * API Route: История платежей.
 *
 * Проксирует запрос к FastAPI с получением telegram_id из токена.
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
  const token =
    cookieStore.get("token")?.value ||
    (isLocalhost(host) ? "dev-token-bypass" : null);

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    // Сначала получаем данные пользователя чтобы узнать telegram_id
    const userResponse = await fetch(`${API_URL}/api/v1/users/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!userResponse.ok) {
      if (userResponse.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      return NextResponse.json(
        { error: "Ошибка получения данных пользователя" },
        { status: userResponse.status }
      );
    }

    const user = await userResponse.json();
    const telegramId = user.telegram_id;

    if (!telegramId) {
      return NextResponse.json(
        { error: "Telegram ID не найден" },
        { status: 400 }
      );
    }

    // Получаем историю платежей
    const response = await fetch(
      `${API_URL}/api/v1/payments/${telegramId}/history`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        // Пользователь не найден или нет платежей - возвращаем пустой массив
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
