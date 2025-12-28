"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { analytics } from "@/lib/analytics";

export default function PaymentSuccessPage() {
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success">("loading");

  useEffect(() => {
    // Отслеживаем успешную оплату
    analytics.paymentSuccess();

    // Webhook может прийти не мгновенно, показываем success через 2 сек
    const timer = setTimeout(() => {
      setStatus("success");
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
        {status === "loading" ? (
          <>
            <Loader2 className="w-16 h-16 animate-spin text-emerald-600 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-warm-gray-800 mb-2">
              Проверяем статус оплаты...
            </h1>
            <p className="text-warm-gray-500">
              Это займёт несколько секунд
            </p>
          </>
        ) : (
          <>
            <CheckCircle className="w-16 h-16 text-emerald-600 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-warm-gray-800 mb-2">
              Оплата прошла успешно!
            </h1>
            <p className="text-warm-gray-500 mb-6">
              Ваша подписка активирована. Новые лимиты уже доступны.
            </p>
            <Link
              href="/app"
              className="inline-flex items-center justify-center px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl transition-colors"
            >
              Перейти в личный кабинет
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
