/**
 * GET /api/integrations/wb/products
 * Получить все товары из синхронизированной базы WB.
 */

import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Не авторизован" },
      { status: 401 }
    );
  }

  try {
    // Получаем товары из бэкенда
    // BACKEND_URL для Docker, API_BASE_URL для legacy, localhost для dev
    const backendUrl = process.env.BACKEND_URL || process.env.API_BASE_URL || "http://localhost:8000";

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 секунд таймаут

    const response = await fetch(`${backendUrl}/api/v1/products?limit=1000`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка загрузки товаров" },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Преобразуем формат для frontend
    // API возвращает список ProductCard
    const products = (Array.isArray(data) ? data : data.items || []).map((item: Record<string, unknown>) => ({
      id: item.id,
      barcode: item.barcode,
      name: item.name,
      article: item.article,
      size: item.size,
      color: item.color,
      brand: item.brand,
    }));

    return NextResponse.json({ products });
  } catch (error) {
    console.error("Ошибка получения товаров WB:", error);
    return NextResponse.json(
      { error: "Внутренняя ошибка сервера" },
      { status: 500 }
    );
  }
}