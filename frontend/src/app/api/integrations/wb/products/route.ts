/**
 * Получить товары из WB API (синхронизированные).
 */

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  // Получаем товары из карточек пользователя (они синхронизированы с WB)
  const response = await fetch(`${API_URL}/api/v1/products/?limit=1000`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    return NextResponse.json(
      { error: error.detail || "Ошибка загрузки товаров" },
      { status: response.status }
    );
  }

  return NextResponse.json(await response.json());
}
