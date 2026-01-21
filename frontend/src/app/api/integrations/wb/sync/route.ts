/**
 * Синхронизация товаров WB
 */

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function POST() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  const response = await fetch(`${API_URL}/api/v1/integrations/wb/sync`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    return NextResponse.json(
      { error: data.detail || "Ошибка синхронизации" },
      { status: response.status }
    );
  }

  return NextResponse.json(data);
}
