"use client";

/**
 * Страница дашборда личного кабинета.
 *
 * Отображает:
 * - Приветствие пользователя
 * - Статистику использования
 * - Текущий тариф
 * - Быстрые действия
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/app/stat-card";
import { ApiKeySection } from "@/components/app/api-key-section";
import { useAuth } from "@/contexts/auth-context";
import { getUserStats } from "@/lib/api";
import type { UserStats } from "@/types/api";
import {
  Sparkles,
  Calendar,
  TrendingUp,
  Crown,
  ArrowRight,
  Loader2,
} from "lucide-react";

/** Маппинг плана на отображаемое название */
const planNames: Record<string, string> = {
  free: "Старт",
  pro: "Про",
  enterprise: "Бизнес",
};

/** Месячные лимиты по планам */
const monthlyLimits: Record<string, number> = {
  free: 50,
  pro: 2000,
  enterprise: 1000000,
};

/** Порог для отображения безлимита (Enterprise = 999999) */
const UNLIMITED_THRESHOLD = 100000;

/** Проверка безлимитного тарифа */
const isUnlimited = (limit: number) => limit >= UNLIMITED_THRESHOLD;

/** Форматирование лимита для отображения */
const formatLimit = (limit: number) => (isUnlimited(limit) ? "∞" : limit);

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Загружаем статистику при монтировании
  useEffect(() => {
    async function loadStats() {
      try {
        setStatsLoading(true);
        setStatsError(null);
        const data = await getUserStats();
        setStats(data);
      } catch (error) {
        console.error("Ошибка загрузки статистики:", error);
        setStatsError(
          error instanceof Error ? error.message : "Ошибка загрузки"
        );
      } finally {
        setStatsLoading(false);
      }
    }

    if (user) {
      loadStats();
    }
  }, [user]);

  // Показываем загрузку пока грузится auth или статистика
  if (authLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-warm-gray-600">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  // Если нет пользователя (хотя middleware должен редиректить)
  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-warm-gray-600">
          Пожалуйста, войдите в систему
        </p>
        <Link href="/login">
          <Button variant="primary" className="mt-4">
            Войти
          </Button>
        </Link>
      </div>
    );
  }

  // Вычисляем значения для отображения
  const plan = user.plan || "free";
  const planName = planNames[plan] || "Старт";
  
  // Логика лимитов: для PRO показываем баланс, для FREE — остаток от 50
  const isPro = plan === "pro";
  const isEnt = plan === "enterprise";
  
  const balance = user.label_balance || 0;
  const thisMonthUsed = stats?.this_month || 0;
  const freeLimit = monthlyLimits.free;
  const remainingFree = Math.max(0, freeLimit - thisMonthUsed);

  return (
    <div className="space-y-8">
      {/* Приветствие */}
      <div>
        <h1 className="text-3xl font-bold text-warm-gray-900 mb-2">
          Привет, {user.first_name}!
        </h1>
        <p className="text-warm-gray-600">
          Добро пожаловать в ваш личный кабинет КлейКод
        </p>
      </div>

      {/* Ошибка загрузки статистики */}
      {statsError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <p className="font-medium">Ошибка загрузки статистики</p>
          <p className="text-sm">{statsError}</p>
        </div>
      )}

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title={isPro ? "Ваш баланс" : isEnt ? "Лимит" : "Осталось в этом месяце"}
          value={isEnt ? "∞" : isPro ? balance : remainingFree}
          description={
            isEnt
              ? `Использовано ${stats?.total_generated} (безлимит)`
              : isPro
                ? `Накопительный баланс`
                : `Использовано ${thisMonthUsed} из ${freeLimit}`
          }
          icon={Sparkles}
          iconColor="text-emerald-600"
        />

        <StatCard
          title="За этот месяц"
          value={thisMonthUsed}
          description="Этикеток создано"
          icon={Calendar}
          iconColor="text-blue-600"
        />

        <StatCard
          title="Всего создано"
          value={stats?.total_generated || 0}
          description="За всё время"
          icon={TrendingUp}
          iconColor="text-purple-600"
        />
      </div>

      {/* Текущий тариф */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Crown className="w-5 h-5 text-amber-500" />
              Текущий тариф
            </CardTitle>
            <span
              className={`text-sm font-medium px-3 py-1 rounded-lg ${
                plan === "free"
                  ? "bg-warm-gray-100 text-warm-gray-700"
                  : plan === "pro"
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-purple-100 text-purple-700"
              }`}
            >
              {planName}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Информация о лимитах */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-warm-gray-600">
                  {isPro ? "Использование баланса" : "Использовано в этом месяце"}
                </span>
                <span className="font-medium text-warm-gray-900">
                  {isPro ? `${balance} шт` : isEnt ? "Безлимит" : `${thisMonthUsed} / ${freeLimit}`}
                </span>
              </div>
              {!isEnt && (
                <div className="w-full bg-warm-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      (isPro ? (balance < 100) : (thisMonthUsed / freeLimit >= 0.9))
                        ? "bg-red-500"
                        : (isPro ? (balance < 500) : (thisMonthUsed / freeLimit >= 0.7))
                          ? "bg-amber-500"
                          : "bg-gradient-to-r from-emerald-500 to-emerald-600"
                    }`}
                    style={{ 
                      width: isPro 
                        ? `${Math.min(100, (balance / 10000) * 100)}%` 
                        : `${Math.min(100, (thisMonthUsed / freeLimit) * 100)}%` 
                    }}
                  />
                </div>
              )}
              {isPro && (
                <p className="text-xs text-warm-gray-500 mt-1">
                  Накопление до 10 000 этикеток. Неиспользованные переносятся на следующий месяц.
                </p>
              )}
            </div>

            {/* CTA для апгрейда */}
            {plan === "free" && (
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-amber-50 to-emerald-50 rounded-lg border border-emerald-200">
                <div>
                  <p className="font-medium text-warm-gray-900">
                    Нужно больше этикеток?
                  </p>
                  <p className="text-sm text-warm-gray-600">
                    Переходите на Про и получайте 2000 этикеток в месяц с накоплением
                  </p>
                </div>
                <Link href="/app/subscription">
                  <Button variant="primary" size="sm">
                    Улучшить
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
              </div>
            )}

            {/* Дата окончания подписки */}
            {user.plan_expires_at && plan !== "free" && (
              <p className="text-sm text-warm-gray-600">
                Подписка действует до:{" "}
                <span className="font-medium">
                  {new Date(user.plan_expires_at).toLocaleDateString("ru-RU")}
                </span>
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* API ключ (только для Enterprise) */}
      {plan === "enterprise" && <ApiKeySection plan={plan} />}

      {/* Быстрые действия */}
      <Card>
        <CardHeader>
          <CardTitle>Быстрые действия</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link href="/app/generate" className="flex-1">
              <Button variant="primary" size="lg" className="w-full">
                <Sparkles className="w-5 h-5" />
                Создать этикетки
              </Button>
            </Link>
            <Link href="/app/history" className="flex-1">
              <Button variant="secondary" size="lg" className="w-full">
                Посмотреть историю
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Заглушка для графика */}
      <Card>
        <CardHeader>
          <CardTitle>Статистика использования</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-warm-gray-50 rounded-lg border-2 border-dashed border-warm-gray-300">
            <div className="text-center">
              <TrendingUp className="w-12 h-12 text-warm-gray-400 mx-auto mb-2" />
              <p className="text-warm-gray-500">График будет добавлен позже</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
