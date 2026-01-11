import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * POST /api/auth/transfer-token
 * Создать одноразовый токен для передачи авторизации на сайт.
 * Требует авторизации (JWT в cookie).
 */
export async function POST(request: NextRequest) {
  try {
    // Получаем токен из cookie
    const cookieStore = await cookies();
    const token = cookieStore.get("token")?.value;

    if (!token) {
      return NextResponse.json(
        { error: "Не авторизован" },
        { status: 401 }
      );
    }

    // URL бэкенда
    const apiUrl = process.env.API_URL || "http://localhost:8000";

    // Запрашиваем transfer token с бэкенда
    const response = await fetch(`${apiUrl}/api/v1/auth/transfer-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({}),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.detail || "Ошибка создания токена" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Ошибка создания transfer token:", error);
    return NextResponse.json(
      { error: "Внутренняя ошибка сервера" },
      { status: 500 }
    );
  }
}
