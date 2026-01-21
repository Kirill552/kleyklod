/**
 * API Route: Статус фоновой задачи.
 *
 * Проксирует запрос к FastAPI с токеном из cookie.
 * Используется для polling прогресса генерации этикеток.
 */

import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ taskId: string }> }
) {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  const { taskId } = await params;

  try {
    const response = await fetch(`${API_URL}/api/v1/tasks/${taskId}`, {
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
        return NextResponse.json({ error: "Задача не найдена" }, { status: 404 });
      }

      if (response.status === 403) {
        return NextResponse.json({ error: "Нет доступа к задаче" }, { status: 403 });
      }

      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || "Ошибка получения статуса" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Ошибка получения статуса задачи:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
