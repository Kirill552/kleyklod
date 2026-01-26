"use client";

/**
 * Баннер подписки для VK Mini App.
 *
 * Показывает текущий тариф, использование и кнопку апгрейда.
 * При клике на "Оформить подписку" открывает страницу оплаты
 * через обычную ссылку <a target="_blank"> с передачей vk_user_id.
 */

import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Crown, Zap, CheckCircle2 } from "lucide-react";
import type { User, UserStats } from "@/types/api";

interface SubscriptionBannerProps {
  user: User | null;
  stats: UserStats | null;
  vkUserId: number | null;
}

/** Месячные лимиты по планам */
const monthlyLimits: Record<string, number> = {
  free: 50,
  pro: 2000,
  enterprise: 999999,
};

/** Названия тарифов */
const planNames: Record<string, string> = {
  free: "Старт",
  pro: "Про",
  enterprise: "Бизнес",
};

/** Преимущества Про плана */
const proFeatures = [
  "2000 этикеток в месяц",
  "Накопление до 10 000 шт",
  "История 7 дней",
];

export function SubscriptionBanner({
  user,
  stats,
  vkUserId,
}: SubscriptionBannerProps) {
  const plan = user?.plan || "free";
  const planName = planNames[plan] || "Старт";
  const monthlyLimit = monthlyLimits[plan] || 50;
  const usedThisMonth = stats?.this_month || 0;
  const labelBalance = user?.label_balance || 0;
  // Для Про показываем баланс, для Старт — использование в месяце
  const remaining = plan === "pro" ? labelBalance : Math.max(0, monthlyLimit - usedThisMonth);
  const usagePercent = plan === "pro"
    ? Math.min(100, (labelBalance / 10000) * 100)
    : Math.min(100, (usedThisMonth / monthlyLimit) * 100);

  /**
   * Генерация URL для страницы оплаты с vk_user_id.
   */
  const getUpgradeUrl = (targetPlan: "pro" | "enterprise") => {
    const baseUrl = "https://kleykod.ru/app/subscription";
    const params = new URLSearchParams({
      plan: targetPlan,
      source: "vk_mini_app",
    });

    // Передаём vk_user_id для связывания платежа с VK аккаунтом
    if (vkUserId) {
      params.set("vk_user_id", vkUserId.toString());
    }

    return `${baseUrl}?${params.toString()}`;
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
                <p className="font-semibold">{planName}</p>
                <p className="text-sm text-muted-foreground">
                  {plan === "enterprise" ? "Безлимит" : `Баланс: ${remaining}`}
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
              В этом месяце
            </span>
            <span className="font-medium">
              {usedThisMonth} / {monthlyLimit}
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
            <span className="font-semibold">Про — 490 руб/мес</span>
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
            <a
              href={getUpgradeUrl("pro")}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all px-4 py-2 text-sm btn-primary"
            >
              <Crown className="mr-2 h-4 w-4" />
              Оформить Про
            </a>
            <a
              href={getUpgradeUrl("enterprise")}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all px-4 py-2 text-sm btn-secondary"
            >
              Бизнес
            </a>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
