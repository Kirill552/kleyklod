import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * POST /api/auth/transfer-token/exchange
 * Обменять transfer token на JWT.
 * Используется при переходе из VK Mini App / VK бота на сайт.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { transfer_token } = body;

    if (!transfer_token) {
      return NextResponse.json(
        { error: "Токен не указан" },
        { status: 400 }
      );
    }

    // URL бэкенда
    const apiUrl = process.env.API_URL || "http://localhost:8000";

    // Обмениваем токен на JWT
    const response = await fetch(`${apiUrl}/api/v1/auth/transfer-token/exchange`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ transfer_token }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.detail || "Недействительный токен" },
        { status: response.status }
      );
    }

    const data = await response.json();
    const { access_token, user } = data;

    // Устанавливаем HttpOnly cookie с JWT токеном
    const cookieStore = await cookies();
    cookieStore.set("token", access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 604800, // 7 дней
    });

    // Возвращаем данные пользователя
    return NextResponse.json({ user, success: true });
  } catch (error) {
    console.error("Ошибка обмена transfer token:", error);
    return NextResponse.json(
      { error: "Внутренняя ошибка сервера" },
      { status: 500 }
    );
  }
}
