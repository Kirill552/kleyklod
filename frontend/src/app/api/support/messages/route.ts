/**
 * API Route: История сообщений поддержки.
 *
 * GET - получить историю сообщений
 * ?since=<timestamp> - только новые сообщения после указанного времени
 *
 * Проксирует запрос к FastAPI /api/v1/support/messages
 */

import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    // Получаем параметр since для polling
    const { searchParams } = new URL(request.url);
    const since = searchParams.get("since") || "";

    const url = since
      ? `${API_URL}/api/v1/support/messages?since=${encodeURIComponent(since)}`
      : `${API_URL}/api/v1/support/messages`;

    const response = await fetch(url, {
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
        { error: error.detail || "Ошибка получения сообщений" },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка получения сообщений поддержки:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
