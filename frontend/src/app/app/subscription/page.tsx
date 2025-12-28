"use client";

/**
 * Страница управления подпиской.
 *
 * Отображает:
 * - Текущий тариф пользователя
 * - Доступные планы с ценами в рублях
 * - Прямую оплату через ЮКассу
 */

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/auth-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Crown, Check, CreditCard, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import { createPayment, getPaymentHistory, PaymentHistoryItem } from "@/lib/api";
import { analytics } from "@/lib/analytics";

/** Тарифные планы */
const plans = [
  {
    id: "free",
    name: "Free",
    price: 0,
    period: "месяц",
    features: [
      "50 этикеток в день",
      "Pre-flight проверка",
      "Без сохранения истории",
    ],
    popular: false,
  },
  {
    id: "pro",
    name: "Pro",
    price: 490,
    period: "месяц",
    features: [
      "500 этикеток в день",
      "Pre-flight проверка",
      "История генераций 7 дней",
      "Пакетная обработка до 200 шт",
      "Email поддержка",
    ],
    popular: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: 1990,
    period: "месяц",
    features: [
      "Безлимит этикеток",
      "История генераций 30 дней",
      "API доступ",
      "Персональный менеджер",
      "SLA 99.9%",
    ],
    popular: false,
  },
];

/** Маппинг плана на отображаемое название */
const planNames: Record<string, string> = {
  free: "Free",
  pro: "Pro",
  enterprise: "Enterprise",
};

export default function SubscriptionPage() {
  const { user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payments, setPayments] = useState<PaymentHistoryItem[]>([]);
  const [paymentsLoading, setPaymentsLoading] = useState(true);

  // Отслеживаем открытие страницы тарифов
  useEffect(() => {
    analytics.openPricing();
  }, []);

  // Загружаем историю платежей
  useEffect(() => {
    async function loadPayments() {
      try {
        setPaymentsLoading(true);
        const data = await getPaymentHistory();
        setPayments(data);
      } catch (err) {
        console.error("Ошибка загрузки истории платежей:", err);
        // Не показываем ошибку пользователю — просто пустая история
      } finally {
        setPaymentsLoading(false);
      }
    }

    if (!authLoading) {
      loadPayments();
    }
  }, [authLoading]);

  // Показываем загрузку авторизации
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-warm-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  const currentPlan = user?.plan || "free";
  const currentPlanName = planNames[currentPlan] || "Free";
  const planExpiresAt = user?.plan_expires_at;

  /**
   * Создает платеж через ЮКассу и перенаправляет на страницу оплаты.
   */
  const handleUpgrade = async (planId: string) => {
    if (planId === "free") return;

    // Отслеживаем клик по кнопке покупки Pro
    analytics.clickBuyPro();

    setLoading(true);
    setError(null);

    try {
      // Передаём telegram_id для привязки платежа к пользователю
      const result = await createPayment(
        planId as "pro" | "enterprise",
        user?.telegram_id
      );
      // Редирект на страницу ЮКассы
      window.location.href = result.confirmation_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка создания платежа");
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold text-warm-gray-900 mb-2">
          Управление подпиской
        </h1>
        <p className="text-warm-gray-600">
          Выберите тариф, который подходит вашему бизнесу
        </p>
      </div>

      {/* Ошибка оплаты */}
      {error && (
        <Card className="border-2 border-red-500 bg-red-50">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <CreditCard className="w-4 h-4 text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-red-900 mb-1">
                  Ошибка создания платежа
                </h3>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Текущий тариф */}
      <Card className="border-2 border-emerald-200 bg-gradient-to-br from-emerald-50 to-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Crown className="w-5 h-5 text-emerald-600" />
            Текущий тариф
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <p className="text-2xl font-bold text-warm-gray-900 mb-1">
                {currentPlanName}
              </p>
              {currentPlan === "free" ? (
                <p className="text-warm-gray-600">
                  Бесплатный доступ с ограничениями
                </p>
              ) : planExpiresAt ? (
                <p className="text-warm-gray-600">
                  Активна до:{" "}
                  <span className="font-medium">
                    {new Date(planExpiresAt).toLocaleDateString("ru-RU")}
                  </span>
                </p>
              ) : (
                <p className="text-warm-gray-600">Активная подписка</p>
              )}
            </div>
            {currentPlan === "free" && (
              <Button
                variant="primary"
                size="lg"
                onClick={() => handleUpgrade("pro")}
                disabled={loading}
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Crown className="w-5 h-5" />
                    Обновить до Pro
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Тарифные планы */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const isCurrentPlan = plan.id === currentPlan;
          const canUpgrade = !isCurrentPlan && plan.id !== "free";

          return (
            <Card
              key={plan.id}
              className={`relative ${
                plan.popular
                  ? "border-2 border-emerald-500 shadow-lg shadow-emerald-500/20"
                  : isCurrentPlan
                    ? "border-2 border-blue-500"
                    : ""
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-emerald-500 to-emerald-600 text-white px-4 py-1 rounded-full text-sm font-semibold shadow-lg">
                    Популярный
                  </span>
                </div>
              )}

              {isCurrentPlan && (
                <div className="absolute -top-4 right-4">
                  <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
                    Ваш план
                  </span>
                </div>
              )}

              <CardHeader className="pt-8">
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <div className="mt-4">
                  {plan.price === 0 ? (
                    <span className="text-4xl font-bold text-warm-gray-900">
                      Бесплатно
                    </span>
                  ) : (
                    <>
                      <span className="text-4xl font-bold text-warm-gray-900">
                        {plan.price} ₽
                      </span>
                      <span className="text-warm-gray-600 ml-2">
                        / {plan.period}
                      </span>
                    </>
                  )}
                </div>
              </CardHeader>

              <CardContent>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <Check className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-warm-gray-700">
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                {isCurrentPlan ? (
                  <Button
                    variant="secondary"
                    size="lg"
                    className="w-full"
                    disabled
                  >
                    Текущий тариф
                  </Button>
                ) : canUpgrade ? (
                  <Button
                    variant="primary"
                    size="lg"
                    className="w-full"
                    onClick={() => handleUpgrade(plan.id)}
                    disabled={loading}
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                    ) : (
                      <>
                        <CreditCard className="w-5 h-5" />
                        Оплатить {plan.price} руб.
                      </>
                    )}
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    size="lg"
                    className="w-full opacity-50"
                    disabled
                  >
                    Бесплатный план
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Информация об оплате */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <CardContent className="py-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <CreditCard className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-warm-gray-900 mb-1">
                Безопасная оплата через ЮКассу
              </h3>
              <p className="text-sm text-warm-gray-600">
                При нажатии на кнопку оплаты вы будете перенаправлены на
                защищенную страницу ЮKassа, где сможете безопасно оплатить
                подписку банковской картой. Подписка активируется автоматически
                сразу после успешной оплаты.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* История платежей */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-emerald-600" />
            История платежей
          </CardTitle>
        </CardHeader>
        <CardContent>
          {paymentsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
            </div>
          ) : payments.length === 0 ? (
            <div className="border-2 border-dashed border-warm-gray-300 rounded-lg p-12">
              <div className="text-center">
                <CreditCard className="w-12 h-12 text-warm-gray-400 mx-auto mb-4" />
                <p className="text-warm-gray-600">Платежей пока нет</p>
                <p className="text-sm text-warm-gray-500 mt-1">
                  История появится после первой покупки
                </p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-warm-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
                      Дата
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
                      Тариф
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
                      Сумма
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
                      Статус
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((payment) => (
                    <tr
                      key={payment.id}
                      className="border-b border-warm-gray-100 hover:bg-warm-gray-50 transition-colors"
                    >
                      <td className="py-4 px-4 text-sm text-warm-gray-600">
                        {new Date(payment.created_at).toLocaleDateString("ru-RU", {
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                      <td className="py-4 px-4 text-sm text-warm-gray-900 font-medium capitalize">
                        {payment.plan}
                      </td>
                      <td className="py-4 px-4 text-sm text-warm-gray-900 font-medium">
                        {payment.amount} {payment.currency === "RUB" ? "₽" : payment.currency}
                      </td>
                      <td className="py-4 px-4">
                        {payment.status === "completed" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                            <CheckCircle className="w-3 h-3" />
                            Оплачено
                          </span>
                        ) : payment.status === "pending" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                            <Clock className="w-3 h-3" />
                            Ожидает
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <XCircle className="w-3 h-3" />
                            Отменён
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
