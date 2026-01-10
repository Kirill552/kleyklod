/**
 * API Route: Автоопределение типа файла (PDF или Excel).
 *
 * Проксирует запрос к FastAPI для определения типа загруженного файла.
 */

import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    // Получаем FormData из запроса
    const formData = await request.formData();

    // Пересылаем FormData на FastAPI
    const response = await fetch(`${API_URL}/api/v1/labels/detect-file`, {
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
        { error: error.detail || "Ошибка определения типа файла" },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка определения типа файла:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
