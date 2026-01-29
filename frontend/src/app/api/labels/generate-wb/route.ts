/**
 * API Route: Генерация этикеток WB-only.
 *
 * Проксирует запрос к FastAPI для генерации этикеток
 * только с штрихкодом Wildberries (без кодов ЧЗ).
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
    const body = await request.json();

    const response = await fetch(`${API_URL}/api/v1/labels/generate-wb`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
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
    console.error("Ошибка генерации WB этикеток:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
