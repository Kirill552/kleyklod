/**
 * API Route: Скачивание результата фоновой задачи.
 *
 * Проксирует запрос к FastAPI с токеном из cookie.
 * Возвращает PDF файл с этикетками.
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
    const response = await fetch(`${API_URL}/api/v1/tasks/${taskId}/download`, {
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
        return NextResponse.json({ error: "Файл не найден" }, { status: 404 });
      }

      if (response.status === 400) {
        return NextResponse.json(
          { error: "Задача ещё не завершена" },
          { status: 400 }
        );
      }

      return NextResponse.json(
        { error: "Ошибка скачивания файла" },
        { status: response.status }
      );
    }

    // Получаем PDF как ArrayBuffer и возвращаем
    const pdfBuffer = await response.arrayBuffer();

    return new NextResponse(pdfBuffer, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="labels_${taskId}.pdf"`,
      },
    });
  } catch (error) {
    console.error("Ошибка скачивания результата задачи:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
