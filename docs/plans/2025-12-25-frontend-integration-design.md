# Дизайн: Интеграция фронтенда с API + Оплата Stars

**Дата:** 2025-12-25
**Статус:** Утверждён
**Предыдущий план:** [2025-12-25-telegram-auth-design.md](./2025-12-25-telegram-auth-design.md)

---

## Обзор

Завершение интеграции личного кабинета: безопасная авторизация через HttpOnly cookies, защита роутов, рабочая генерация этикеток, оплата через Telegram Stars.

## Принятые решения

| Вопрос | Решение |
|--------|---------|
| Хранение auth state | React Context + HttpOnly cookies |
| Установка cookie | Next.js API Route как прокси |
| Защита роутов | Next.js Middleware |
| Ввод кодов маркировки | Textarea + CSV/Excel файл (комбинированный) |
| Оплата | Deeplink в бота → Telegram Stars |

---

## Часть 1: Архитектура авторизации

### Файловая структура

```
frontend/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── auth/
│   │   │       ├── telegram/route.ts    # Прокси к бэкенду
│   │   │       ├── me/route.ts          # Получить текущего юзера
│   │   │       └── logout/route.ts      # Выход
│   │   └── login/
│   │       └── page.tsx                 # Страница входа
│   ├── middleware.ts                    # Защита /app/* роутов
│   └── contexts/
│       └── auth-context.tsx             # React Context для auth
```

### Флоу авторизации

1. Пользователь на `/login` нажимает Telegram Widget
2. Telegram возвращает данные (id, hash, auth_date...)
3. Frontend вызывает `POST /api/auth/telegram` (Next.js API Route)
4. Next.js API Route:
   - Пересылает данные на FastAPI `/api/v1/auth/telegram`
   - Получает JWT токен
   - Устанавливает `Set-Cookie: token=JWT; HttpOnly; Secure; SameSite=Strict; Path=/`
   - Возвращает `{ user }` клиенту
5. Frontend обновляет Context, редирект на `/app`

### Middleware защита

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')

  // Защищаем все /app/* роуты
  if (request.nextUrl.pathname.startsWith('/app') && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Если авторизован и на /login — редирект в /app
  if (request.nextUrl.pathname === '/login' && token) {
    return NextResponse.redirect(new URL('/app', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/app/:path*', '/login'],
}
```

### Cookie параметры

```typescript
// Безопасные настройки cookie
const cookieOptions = {
  httpOnly: true,        // Недоступна из JavaScript (защита от XSS)
  secure: true,          // Только HTTPS
  sameSite: 'strict',    // Защита от CSRF
  path: '/',
  maxAge: 60 * 60 * 24 * 7, // 7 дней
}
```

---

## Часть 2: Генерация этикеток

### Компоненты

```
frontend/src/
├── app/app/generate/
│   └── page.tsx                    # Страница генерации
├── components/app/
│   ├── pdf-dropzone.tsx            # Drag-n-drop для PDF
│   ├── codes-input.tsx             # Textarea + загрузка CSV
│   ├── generation-preview.tsx      # Превью результата
│   └── preflight-alerts.tsx        # Pre-flight предупреждения
└── hooks/
    └── use-generate.ts             # Хук для логики генерации
```

### Флоу генерации

1. Пользователь загружает PDF в dropzone
2. Показываем: "Найдено X этикеток"
3. Пользователь вводит коды (textarea или CSV файл)
4. Валидация: количество кодов = количество страниц PDF
5. Кнопка "Сгенерировать" → `POST /api/v1/labels/merge`
6. Показываем Pre-flight результаты (warnings если есть)
7. Скачивание готового PDF

### Хук генерации

```typescript
// hooks/use-generate.ts
import { useState } from 'react'

type GenerateState = 'idle' | 'pdf_loaded' | 'ready' | 'generating' | 'success' | 'error'

interface PreflightResult {
  status: 'ok' | 'warning' | 'error'
  message: string
  details?: Record<string, unknown>
}

interface GenerateResult {
  blob: Blob
  preflight: PreflightResult[]
}

export function useGenerate() {
  const [state, setState] = useState<GenerateState>('idle')
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [pageCount, setPageCount] = useState(0)
  const [codes, setCodes] = useState<string[]>([])
  const [result, setResult] = useState<GenerateResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function uploadPdf(file: File) {
    setPdfFile(file)
    // Получаем количество страниц через API или локально
    setState('pdf_loaded')
  }

  async function generate() {
    if (!pdfFile || codes.length === 0) return

    setState('generating')
    setError(null)

    try {
      const formData = new FormData()
      formData.append('pdf_file', pdfFile)
      formData.append('codes', codes.join('\n'))

      const response = await fetch('/api/v1/labels/merge', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Ошибка генерации')
      }

      const blob = await response.blob()
      setResult({ blob, preflight: [] })
      setState('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка')
      setState('error')
    }
  }

  function reset() {
    setState('idle')
    setPdfFile(null)
    setPageCount(0)
    setCodes([])
    setResult(null)
    setError(null)
  }

  return {
    state,
    pdfFile,
    pageCount,
    codes,
    result,
    error,
    uploadPdf,
    setCodes,
    generate,
    reset,
  }
}
```

### Состояния UI

| Состояние | Что показываем |
|-----------|----------------|
| `idle` | Пустой dropzone |
| `pdf_loaded` | PDF загружен, ждём коды |
| `ready` | Всё готово, кнопка активна |
| `generating` | Спиннер, прогресс |
| `success` | Кнопка скачать + Pre-flight отчёт |
| `error` | Сообщение об ошибке |

---

## Часть 3: Оплата через Telegram Stars

### Флоу оплаты

```
Сайт /app/subscription
    ↓
Кнопка "Оплатить Pro (350 ⭐)"
    ↓
window.open(`https://t.me/KleyKodBot?start=pay_pro_${uniquePaymentId}`)
    ↓
Бот парсит deep_link: "pay_pro_abc123"
    ↓
Бот отправляет Invoice (Telegram Stars)
    ↓
Пользователь оплачивает
    ↓
Бот получает successful_payment
    ↓
Бот обновляет user.plan = "pro", user.plan_expires_at = +30 дней
    ↓
Бот шлёт сообщение: "Подписка Pro активирована до DD.MM.YYYY"
```

### Обработка в боте

```python
# bot/handlers/payment.py

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
from datetime import datetime, timedelta

router = Router()

@router.message(CommandStart(deep_link=True))
async def handle_deep_link(message: Message):
    """Обработка deep link для оплаты."""
    args = message.text.split()[1] if len(message.text.split()) > 1 else ""

    if args.startswith("pay_pro_"):
        payment_id = args.replace("pay_pro_", "")

        await message.answer_invoice(
            title="Подписка Pro",
            description="Безлимит этикеток + Pre-flight проверка на 30 дней",
            payload=f"pro_subscription_{payment_id}",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label="Pro подписка", amount=350)],
        )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    """Подтверждение перед оплатой."""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    """Обработка успешной оплаты."""
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id

    # Активируем подписку Pro на 30 дней
    expires_at = datetime.now() + timedelta(days=30)

    # Обновляем в БД через API
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"{API_URL}/api/v1/payments/activate",
            json={
                "telegram_id": user_id,
                "plan": "pro",
                "expires_at": expires_at.isoformat(),
                "payment_id": payload,
                "amount_stars": 350,
            }
        )

    await message.answer(
        f"✅ Подписка Pro активирована!\n\n"
        f"Действует до: {expires_at.strftime('%d.%m.%Y')}\n\n"
        f"Теперь вам доступно:\n"
        f"• Безлимит этикеток\n"
        f"• Pre-flight проверка качества\n"
        f"• Приоритетная поддержка"
    )
```

### Страница подписки

```typescript
// app/app/subscription/page.tsx

function SubscriptionPage() {
  const { user } = useUser()

  const handleUpgrade = () => {
    // Генерируем уникальный ID для отслеживания платежа
    const paymentId = crypto.randomUUID().slice(0, 8)
    window.open(`https://t.me/KleyKodBot?start=pay_pro_${paymentId}`, '_blank')
  }

  return (
    <div>
      <h1>Подписка</h1>

      {user?.plan === 'pro' ? (
        <Card>
          <p>Тариф: Pro</p>
          <p>Действует до: {formatDate(user.plan_expires_at)}</p>
        </Card>
      ) : (
        <Card>
          <p>Тариф: Free (50 этикеток/день)</p>
          <Button onClick={handleUpgrade}>
            Оплатить Pro (350 ⭐)
          </Button>
        </Card>
      )}
    </div>
  )
}
```

---

## Часть 4: Интеграция с API

### API клиент

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

export async function api<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      window.location.href = '/login'
      throw new ApiError(401, 'Unauthorized')
    }
    throw new ApiError(response.status, 'API Error')
  }

  return response.json()
}
```

### Хуки для данных

```typescript
// hooks/use-user.ts
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface User {
  id: string
  telegram_id: number
  username: string | null
  first_name: string
  plan: 'free' | 'pro'
  plan_expires_at: string | null
  created_at: string
}

interface UserStats {
  today_used: number
  today_limit: number
  total_generated: number
  this_month: number
}

export function useUser() {
  const [user, setUser] = useState<User | null>(null)
  const [stats, setStats] = useState<UserStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api<User>('/api/v1/users/me'),
      api<UserStats>('/api/v1/users/me/stats'),
    ])
      .then(([userData, statsData]) => {
        setUser(userData)
        setStats(statsData)
      })
      .catch(() => {
        // Ошибка обработается в api() — редирект на /login
      })
      .finally(() => setLoading(false))
  }, [])

  const refresh = async () => {
    const [userData, statsData] = await Promise.all([
      api<User>('/api/v1/users/me'),
      api<UserStats>('/api/v1/users/me/stats'),
    ])
    setUser(userData)
    setStats(statsData)
  }

  return { user, stats, loading, refresh }
}
```

### Страницы и их endpoints

| Страница | Endpoint |
|----------|----------|
| `/app` (дашборд) | `GET /api/v1/users/me` + `GET /api/v1/users/me/stats` |
| `/app/history` | `GET /api/v1/generations` |
| `/app/subscription` | `GET /api/v1/users/me` (plan, plan_expires_at) |
| `/app/settings` | `GET /api/v1/users/me`, `PUT /api/v1/users/me` |

---

## Часть 5: План реализации

### Порядок задач

| # | Задача | Зависит от |
|---|--------|------------|
| 1 | Next.js API Routes для auth | — |
| 2 | Middleware защита роутов | 1 |
| 3 | Auth Context | 1, 2 |
| 4 | Страница /login | 1, 3 |
| 5 | Интеграция дашборда с API | 3 |
| 6 | Генерация этикеток (dropzone + codes) | 3 |
| 7 | Оплата Stars в боте | — |
| 8 | Страница /app/subscription | 5, 7 |
| 9 | История генераций | 5 |
| 10 | Страница настроек | 5 |

### Новые файлы

**Frontend:**
- `src/app/api/auth/telegram/route.ts`
- `src/app/api/auth/me/route.ts`
- `src/app/api/auth/logout/route.ts`
- `src/middleware.ts`
- `src/contexts/auth-context.tsx`
- `src/app/login/page.tsx`
- `src/lib/api.ts`
- `src/hooks/use-user.ts`
- `src/hooks/use-stats.ts`
- `src/hooks/use-generate.ts`
- `src/components/app/pdf-dropzone.tsx`
- `src/components/app/codes-input.tsx`
- `src/types/api.ts`

### Изменения в существующих файлах

**Frontend:**
- `src/app/app/page.tsx` — реальные данные вместо mockData
- `src/app/app/generate/page.tsx` — рабочая генерация
- `src/app/app/subscription/page.tsx` — deeplink + статус
- `src/app/app/history/page.tsx` — реальные данные

**Bot:**
- `bot/handlers/payment.py` — deep link + Stars invoice

---

## Безопасность

### Реализованные меры

1. **HttpOnly cookies** — токен недоступен из JavaScript, защита от XSS
2. **SameSite=Strict** — защита от CSRF атак
3. **Secure flag** — cookie только через HTTPS
4. **Middleware проверка** — серверная проверка до рендеринга
5. **Проверка подписи Telegram** — HMAC-SHA256 валидация на бэкенде
6. **JWT с истечением** — токены живут 7 дней

### Рекомендации для production

- Использовать HTTPS везде
- Настроить CSP (Content Security Policy)
- Rate limiting на API endpoints
- Логирование подозрительных запросов
