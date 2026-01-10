/**
 * API Route: Операции с карточкой товара по баркоду.
 *
 * Проксирует запросы к FastAPI с токеном из cookie.
 * GET - получить карточку
 * PUT - создать или обновить карточку
 * DELETE - удалить карточку
 */

import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

interface RouteParams {
  params: Promise<{ barcode: string }>;
}

/**
 * GET /api/products/[barcode] - Получить карточку товара
 */
export async function GET(request: NextRequest, { params }: RouteParams) {
  const cookieStore = await cookies();
  const { barcode } = await params;
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/products/${barcode}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      if (response.status === 403) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "Доступ запрещён" },
          { status: 403 }
        );
      }
      if (response.status === 404) {
        return NextResponse.json(
          { error: "Карточка не найдена" },
          { status: 404 }
        );
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка загрузки карточки" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Ошибка запроса карточки:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}

/**
 * PUT /api/products/[barcode] - Создать или обновить карточку
 */
export async function PUT(request: NextRequest, { params }: RouteParams) {
  const cookieStore = await cookies();
  const { barcode } = await params;
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const body = await request.json();

    const response = await fetch(`${API_URL}/api/v1/products/${barcode}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      if (response.status === 403) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "Доступ запрещён" },
          { status: 403 }
        );
      }
      if (response.status === 422) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "Невалидные данные" },
          { status: 422 }
        );
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка сохранения карточки" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Ошибка сохранения карточки:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}

/**
 * DELETE /api/products/[barcode] - Удалить карточку
 */
export async function DELETE(request: NextRequest, { params }: RouteParams) {
  const cookieStore = await cookies();
  const { barcode } = await params;
  const token = cookieStore.get("token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/products/${barcode}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return NextResponse.json({ error: "Не авторизован" }, { status: 401 });
      }
      if (response.status === 403) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { error: error.detail || "Доступ запрещён" },
          { status: 403 }
        );
      }
      if (response.status === 404) {
        return NextResponse.json(
          { error: "Карточка не найдена" },
          { status: 404 }
        );
      }

      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || "Ошибка удаления карточки" },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Ошибка удаления карточки:", error);
    return NextResponse.json({ error: "Ошибка сервера" }, { status: 500 });
  }
}
