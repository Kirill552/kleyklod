import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * POST /api/auth/vk
 * Авторизация через VK Mini App.
 * Получает vk_user_id, отправляет на бэкенд, получает JWT и сохраняет в HttpOnly cookie.
 */
export async function POST(request: NextRequest) {
  try {
    // Читаем данные от VK Mini App
    const vkData = await request.json();

    // URL бэкенда из переменных окружения
    const apiUrl = process.env.API_URL || "http://localhost:8000";

    // Отправляем данные на бэкенд для авторизации
    const response = await fetch(`${apiUrl}/api/v1/auth/vk`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(vkData),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.detail || "Ошибка авторизации VK" },
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
      sameSite: "strict",
      path: "/",
      maxAge: 604800, // 7 дней
    });

    // Возвращаем только данные пользователя
    return NextResponse.json({ user });
  } catch (error) {
    console.error("Ошибка авторизации через VK:", error);
    return NextResponse.json(
      { error: "Внутренняя ошибка сервера" },
      { status: 500 }
    );
  }
}
