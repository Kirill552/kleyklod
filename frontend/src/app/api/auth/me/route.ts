import { NextRequest, NextResponse } from 'next/server';
import { cookies, headers } from 'next/headers';

// Проверка localhost для dev mode
function isLocalhost(host: string | null): boolean {
  return host?.includes("localhost") || host?.includes("127.0.0.1") || false;
}

/**
 * GET /api/auth/me
 * Получение данных текущего пользователя
 * Читает JWT из cookie и отправляет запрос на бэкенд
 */
export async function GET(request: NextRequest) {
  try {
    // Читаем токен из cookie
    const cookieStore = await cookies();
    const headersList = await headers();
    const host = headersList.get("host");

    // На localhost используем dev-token-bypass
    const token = cookieStore.get('token')?.value ||
      (isLocalhost(host) ? "dev-token-bypass" : null);

    if (!token) {
      return NextResponse.json(
        { error: 'Не авторизован' },
        { status: 401 }
      );
    }

    // URL бэкенда из переменных окружения
    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    // Запрос данных пользователя с токеном в заголовке
    const response = await fetch(`${apiUrl}/api/v1/users/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // Если токен невалидный - удаляем cookie
      if (response.status === 401) {
        cookieStore.delete('token');
      }

      const error = await response.json();
      return NextResponse.json(
        { error: error.detail || 'Ошибка получения данных пользователя' },
        { status: response.status }
      );
    }

    const user = await response.json();
    return NextResponse.json({ user });

  } catch (error) {
    console.error('Ошибка получения данных пользователя:', error);
    return NextResponse.json(
      { error: 'Внутренняя ошибка сервера' },
      { status: 500 }
    );
  }
}
