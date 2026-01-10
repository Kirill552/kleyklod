"use client";

/**
 * Баннер подписки для VK Mini App.
 *
 * Показывает текущий тариф, использование и кнопку апгрейда.
 * При клике на "Оформить подписку" открывает страницу оплаты
 * через VKWebAppOpenLink с передачей vk_user_id.
 */

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Crown, Zap, CheckCircle2 } from "lucide-react";
import { openExternalLink } from "@/lib/vk-bridge";
import type { User, UserStats } from "@/types/api";

interface SubscriptionBannerProps {
  user: User | null;
  stats: UserStats | null;
  vkUserId: number | null;
}

/** Дневные лимиты по планам */
const dailyLimits: Record<string, number> = {
  free: 50,
  pro: 500,
  enterprise: 10000,
};

/** Преимущества PRO плана */
const proFeatures = [
  "500 этикеток в день",
  "История 7 дней",
  "База товаров (100 шт)",
];

export function SubscriptionBanner({
  user,
  stats,
  vkUserId,
}: SubscriptionBannerProps) {
  const plan = user?.plan || "free";
  const dailyLimit = dailyLimits[plan] || 50;
  const usedToday = stats?.today_used || 0;
  const remaining = Math.max(0, dailyLimit - usedToday);
  const usagePercent = Math.min(100, (usedToday / dailyLimit) * 100);

  /**
   * Открыть страницу оплаты с vk_user_id для связывания аккаунта.
   */
  const handleUpgrade = (targetPlan: "pro" | "enterprise") => {
    const baseUrl = "https://kleykod.ru/app/subscription";
    const params = new URLSearchParams({
      plan: targetPlan,
      source: "vk_mini_app",
    });

    // Передаём vk_user_id для связывания платежа с VK аккаунтом
    if (vkUserId) {
      params.set("vk_user_id", vkUserId.toString());
    }

    openExternalLink(`${baseUrl}?${params.toString()}`);
  };

  // Для PRO/Enterprise показываем компактную версию
  if (plan !== "free") {
    return (
      <Card className="mb-6 bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-primary/20 p-2">
                <Crown className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-semibold">{plan.toUpperCase()}</p>
                <p className="text-sm text-muted-foreground">
                  {usedToday} / {dailyLimit} сегодня
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">{remaining}</p>
              <p className="text-xs text-muted-foreground">осталось</p>
            </div>
          </div>
          <Progress value={usagePercent} className="mt-3 h-2" />
        </CardContent>
      </Card>
    );
  }

  // Для FREE показываем полный баннер с призывом к апгрейду
  return (
    <Card className="mb-6 overflow-hidden">
      <CardContent className="p-0">
        {/* Статистика использования */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">
              Использовано сегодня
            </span>
            <span className="font-medium">
              {usedToday} / {dailyLimit}
            </span>
          </div>
          <Progress value={usagePercent} className="h-2" />
          {remaining <= 10 && remaining > 0 && (
            <p className="text-xs text-amber-600 mt-2">
              Осталось всего {remaining} этикеток
            </p>
          )}
          {remaining === 0 && (
            <p className="text-xs text-destructive mt-2">
              Лимит исчерпан. Обновите тариф для продолжения.
            </p>
          )}
        </div>

        {/* Предложение PRO */}
        <div className="p-4 bg-gradient-to-br from-primary/5 to-primary/10">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="h-5 w-5 text-primary" />
            <span className="font-semibold">PRO — 490 руб/мес</span>
          </div>

          <ul className="space-y-2 mb-4">
            {proFeatures.map((feature) => (
              <li key={feature} className="flex items-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>

          <div className="flex gap-2">
            <Button
              onClick={() => handleUpgrade("pro")}
              className="flex-1"
              size="sm"
            >
              <Crown className="mr-2 h-4 w-4" />
              Оформить PRO
            </Button>
            <Button
              onClick={() => handleUpgrade("enterprise")}
              variant="secondary"
              size="sm"
            >
              Enterprise
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
