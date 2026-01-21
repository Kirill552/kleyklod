/**
 * Прокси для /api/v1/integrations
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

  const response = await fetch(`${API_URL}/api/v1/integrations/`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    return NextResponse.json(
      { error: error.detail || "Ошибка загрузки интеграций" },
      { status: response.status }
    );
  }

  return NextResponse.json(await response.json());
}
