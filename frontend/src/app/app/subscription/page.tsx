"use client";

/**
 * Страница управления подпиской.
 *
 * Отображает:
 * - Текущий тариф пользователя
 * - Доступные планы с ценами в Telegram Stars
 * - Кнопки оплаты через deep link в боте
 */

import { useAuth } from "@/contexts/auth-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Crown, Check, Star, CreditCard, ExternalLink, Loader2 } from "lucide-react";

/** Имя бота для deep link */
const BOT_USERNAME = process.env.NEXT_PUBLIC_TELEGRAM_BOT_NAME || "KleyKodBot";

/** Тарифные планы */
const plans = [
  {
    id: "free",
    name: "Free",
    price: 0,
    priceStars: 0,
    priceRub: 0,
    limits: {
      daily: 50,
    },
    features: [
      "50 этикеток в день",
      "Базовая генерация",
      "История на 7 дней",
      "Email поддержка",
    ],
    popular: false,
  },
  {
    id: "pro",
    name: "Pro",
    priceStars: 377,
    priceRub: 490,
    limits: {
      daily: 500,
    },
    features: [
      "500 этикеток в день",
      "Расширенный Pre-flight Check",
      "Полная история",
      "Приоритетная поддержка",
      "Пакетная обработка",
    ],
    popular: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    priceStars: 1531,
    priceRub: 1990,
    limits: {
      daily: 10000,
    },
    features: [
      "10,000 этикеток в день",
      "API доступ",
      "SLA 99.9%",
      "Персональный менеджер",
      "Приоритетная поддержка",
      "Белый лейбл",
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

/**
 * Генерация deep link для оплаты в Telegram боте.
 */
function getPaymentDeepLink(planId: string): string {
  const paymentId = `web_${Date.now()}`;
  return `https://t.me/${BOT_USERNAME}?start=pay_${planId}_${paymentId}`;
}

export default function SubscriptionPage() {
  const { user, loading } = useAuth();

  // Показываем загрузку
  if (loading) {
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
   * Открывает deep link для оплаты в Telegram.
   */
  const handleUpgrade = (planId: string) => {
    const deepLink = getPaymentDeepLink(planId);
    window.open(deepLink, "_blank");
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
              >
                <Crown className="w-5 h-5" />
                Обновить до Pro
                <ExternalLink className="w-4 h-4" />
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
                  {plan.priceStars === 0 ? (
                    <span className="text-4xl font-bold text-warm-gray-900">
                      Бесплатно
                    </span>
                  ) : (
                    <>
                      <span className="text-4xl font-bold text-warm-gray-900">
                        {plan.priceStars}
                      </span>
                      <span className="text-warm-gray-600 ml-2">
                        <Star className="w-5 h-5 inline text-amber-500" /> /
                        месяц
                      </span>
                      <p className="text-sm text-warm-gray-500 mt-1">
                        ≈ {plan.priceRub} ₽
                      </p>
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
                  >
                    <CreditCard className="w-5 h-5" />
                    Оплатить {plan.priceStars}{" "}
                    <Star className="w-4 h-4 text-amber-400" />
                    <ExternalLink className="w-4 h-4 ml-1" />
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
              <Star className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-warm-gray-900 mb-1">
                Оплата через Telegram Stars
              </h3>
              <p className="text-sm text-warm-gray-600">
                При нажатии на кнопку оплаты вы будете перенаправлены в
                Telegram-бот KleyKod, где сможете безопасно оплатить подписку
                через Telegram Stars. Подписка активируется автоматически сразу
                после оплаты.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* История платежей - заглушка */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-emerald-600" />
            История платежей
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-warm-gray-300 rounded-lg p-12">
            <div className="text-center">
              <CreditCard className="w-12 h-12 text-warm-gray-400 mx-auto mb-4" />
              <p className="text-warm-gray-600">Платежей пока нет</p>
              <p className="text-sm text-warm-gray-500 mt-1">
                История появится после первой покупки
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
