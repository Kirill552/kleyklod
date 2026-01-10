/**
 * API Route: Количество непрочитанных сообщений поддержки.
 *
 * GET - получить количество непрочитанных сообщений
 *
 * Проксирует запрос к FastAPI /api/v1/support/unread
 */

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    // Для неавторизованных возвращаем 0, не ошибку
    return NextResponse.json({ count: 0 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/support/unread`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // При ошибке возвращаем 0
      return NextResponse.json({ count: 0 });
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка получения непрочитанных сообщений:", error);
    // При ошибке возвращаем 0, не ломаем UI
    return NextResponse.json({ count: 0 });
  }
}
