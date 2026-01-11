import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * POST /api/auth/vk/callback
 *
 * Получает code + device_id от VK One Tap,
 * отправляет на backend для обмена на JWT.
 */
export async function POST(request: NextRequest) {
  try {
    const { code, device_id } = await request.json();

    if (!code || !device_id) {
      return NextResponse.json(
        { error: "Отсутствует code или device_id" },
        { status: 400 }
      );
    }

    const apiUrl = process.env.API_URL || "http://localhost:8000";

    // Отправляем на backend для обмена code -> JWT
    const response = await fetch(`${apiUrl}/api/v1/auth/vk/callback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, device_id }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error("[VK Callback] Backend error:", error);
      return NextResponse.json(
        { error: error.detail || "Ошибка авторизации VK" },
        { status: response.status }
      );
    }

    const data = await response.json();
    const { access_token, user } = data;

    // Сохраняем JWT в HttpOnly cookie
    const cookieStore = await cookies();
    cookieStore.set("token", access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax", // lax для работы редиректов
      path: "/",
      maxAge: 604800, // 7 дней
    });

    return NextResponse.json({ user });
  } catch (error) {
    console.error("[VK Callback] Error:", error);
    return NextResponse.json(
      { error: "Внутренняя ошибка сервера" },
      { status: 500 }
    );
  }
}
