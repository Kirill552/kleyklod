import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

/**
 * GET /api/auth/telegram/callback
 * Обработка redirect от Telegram Login Widget.
 *
 * Telegram перенаправляет сюда с GET параметрами:
 * id, first_name, last_name?, username?, photo_url?, auth_date, hash
 *
 * Мы валидируем их на бэкенде и устанавливаем JWT в HttpOnly cookie.
 */
export async function GET(request: NextRequest) {
  // Базовый URL для редиректов (внутри Docker request.url = 0.0.0.0:3000)
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://kleykod.ru';

  try {
    const { searchParams } = new URL(request.url);

    // Собираем данные из query параметров
    const id = searchParams.get('id');
    const firstName = searchParams.get('first_name');
    const lastName = searchParams.get('last_name');
    const username = searchParams.get('username');
    const photoUrl = searchParams.get('photo_url');
    const authDate = searchParams.get('auth_date');
    const hash = searchParams.get('hash');

    // Проверяем обязательные поля
    if (!id || !firstName || !authDate || !hash) {
      console.error('[CALLBACK] Отсутствуют обязательные параметры:', {
        id: !!id,
        firstName: !!firstName,
        authDate: !!authDate,
        hash: !!hash,
      });
      return NextResponse.redirect(new URL('/login?error=missing_params', baseUrl));
    }

    // Формируем объект для отправки на бэкенд
    const telegramData: Record<string, string | number> = {
      id: parseInt(id, 10),
      first_name: firstName,
      auth_date: parseInt(authDate, 10),
      hash: hash,
    };

    // Добавляем опциональные поля
    if (lastName) telegramData.last_name = lastName;
    if (username) telegramData.username = username;
    if (photoUrl) telegramData.photo_url = photoUrl;

    console.log('[CALLBACK] Telegram data:', JSON.stringify(telegramData));

    // URL бэкенда
    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    // Отправляем на бэкенд для валидации
    const response = await fetch(`${apiUrl}/api/v1/auth/telegram`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(telegramData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('[CALLBACK] Backend error:', response.status, error);
      return NextResponse.redirect(
        new URL(`/login?error=${encodeURIComponent(error.detail || 'auth_failed')}`, baseUrl)
      );
    }

    const data = await response.json();
    const { access_token } = data;

    console.log('[CALLBACK] Auth successful, setting cookie...');

    // Устанавливаем HttpOnly cookie с JWT токеном
    const cookieStore = await cookies();
    cookieStore.set('token', access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax', // lax для работы с redirect
      path: '/',
      maxAge: 604800, // 7 дней
    });

    // Редиректим в личный кабинет
    console.log('[CALLBACK] Redirecting to /app...');
    return NextResponse.redirect(new URL('/app', baseUrl));

  } catch (error) {
    console.error('[CALLBACK] Error:', error);
    return NextResponse.redirect(new URL('/login?error=internal_error', 'https://kleykod.ru'));
  }
}
