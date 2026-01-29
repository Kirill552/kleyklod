/**
 * API Route: Генерация этикеток ЧЗ-only.
 *
 * Проксирует запрос к FastAPI для генерации этикеток
 * только с DataMatrix кода маркировки (без штрихкода WB).
 */

import { NextRequest, NextResponse } from "next/server";
import { getAuthToken } from "@/lib/server-auth";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  const token = await getAuthToken(request);

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    // Получаем FormData из запроса
    const formData = await request.formData();

    // Пересылаем FormData на FastAPI
    const response = await fetch(`${API_URL}/api/v1/labels/generate-chz`, {
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

      if (response.status === 429) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "Превышен лимит генераций" },
          { status: 429 }
        );
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка генерации этикеток" },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка генерации ЧЗ этикеток:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
