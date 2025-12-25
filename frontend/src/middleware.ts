/**
 * Next.js Middleware для защиты роутов.
 *
 * Проверяет наличие auth cookie перед доступом к /app/* страницам.
 * Редиректит неавторизованных пользователей на /login.
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware выполняется на каждый запрос к защищённым роутам.
 * Проверка происходит на сервере ДО рендеринга страницы.
 */
export function middleware(request: NextRequest) {
  const token = request.cookies.get("token");
  const { pathname } = request.nextUrl;

  // Защищаем все /app/* роуты
  if (pathname.startsWith("/app")) {
    if (!token) {
      // Нет токена — редирект на страницу входа
      const loginUrl = new URL("/login", request.url);
      // Сохраняем куда хотел попасть пользователь для редиректа после логина
      loginUrl.searchParams.set("callbackUrl", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // Если авторизован и на /login — редирект в /app
  if (pathname === "/login" && token) {
    return NextResponse.redirect(new URL("/app", request.url));
  }

  return NextResponse.next();
}

/**
 * Конфигурация: на каких путях срабатывает middleware.
 */
export const config = {
  matcher: [
    // Защищённые роуты личного кабинета
    "/app/:path*",
    // Страница входа (для редиректа авторизованных)
    "/login",
  ],
};
