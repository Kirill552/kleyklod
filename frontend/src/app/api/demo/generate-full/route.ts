/**
 * Demo генерация из Excel (полный флоу) БЕЗ регистрации.
 *
 * Проксирует запрос на backend /api/v1/demo/generate-full
 */

import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    // Получаем FormData из запроса
    const formData = await request.formData();

    // Проксируем на backend
    const response = await fetch(`${API_URL}/api/v1/demo/generate-full`, {
      method: "POST",
      body: formData,
      headers: {
        // Передаём реальный IP клиента для rate limiting
        "X-Forwarded-For": request.headers.get("x-forwarded-for") || request.ip || "unknown",
        "X-Real-IP": request.headers.get("x-real-ip") || request.ip || "unknown",
      },
    });

    // Если это PDF файл - возвращаем бинарные данные
    const contentType = response.headers.get("content-type");

    if (contentType?.includes("application/json")) {
      const data = await response.json();
      return NextResponse.json(data, { status: response.status });
    }

    // Для других типов (например, PDF) возвращаем как есть
    const blob = await response.blob();
    return new NextResponse(blob, {
      status: response.status,
      headers: {
        "Content-Type": contentType || "application/octet-stream",
        "Content-Disposition": response.headers.get("content-disposition") || "",
      },
    });
  } catch (error) {
    console.error("Demo generate-full error:", error);
    return NextResponse.json(
      { success: false, message: "Ошибка сервера при demo генерации" },
      { status: 500 }
    );
  }
}
