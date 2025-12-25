/**
 * API Route: Управление API ключами.
 *
 * Проксирует запросы к FastAPI с токеном из cookie.
 * Только для Enterprise пользователей.
 *
 * GET - Получить информацию о ключе
 * POST - Создать новый ключ
 * DELETE - Отозвать ключ
 */

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * Получить информацию о текущем API ключе.
 */
export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/keys/info`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка получения информации о ключе" },
        { status: response.status }
      );
    }

    const keyInfo = await response.json();
    return NextResponse.json(keyInfo);
  } catch (error) {
    console.error("Ошибка запроса информации о ключе:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}

/**
 * Создать новый API ключ.
 */
export async function POST() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/keys/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      if (response.status === 403) {
        return NextResponse.json(
          { error: "API ключи доступны только для Enterprise подписки" },
          { status: 403 }
        );
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка создания ключа" },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка создания API ключа:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}

/**
 * Отозвать API ключ.
 */
export async function DELETE() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/keys/`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      if (response.status === 404) {
        return NextResponse.json(
          { error: "API ключ не найден" },
          { status: 404 }
        );
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка отзыва ключа" },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Ошибка отзыва API ключа:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
