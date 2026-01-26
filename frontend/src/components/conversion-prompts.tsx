"use client";

/**
 * Компоненты для мягких триггеров конверсии Старт → Про.
 *
 * Показываем ненавязчивые напоминания о Про тарифе:
 * - При приближении к месячному лимиту (≤10 этикеток)
 * - Когда лимит исчерпан
 *
 * Правило: не чаще 1 раза за сессию.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { AlertTriangle, TrendingUp, Clock, Sparkles, X } from "lucide-react";

// ============================================
// Хук для управления показом триггеров
// ============================================

/** Ключи для хранения состояния */
const SESSION_KEY = "conversion_prompt_shown";
const REMIND_KEY = "remind_upgrade_date";

/**
 * Проверить, был ли уже показан триггер в этой сессии.
 */
function getInitialShouldShow(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const shown = sessionStorage.getItem(SESSION_KEY);
  return !shown;
}

/**
 * Проверить, нужно ли показать напоминание сегодня.
 */
function getInitialShouldRemind(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const remindDate = localStorage.getItem(REMIND_KEY);
  if (remindDate) {
    const today = new Date().toISOString().split("T")[0];
    // Очищаем после проверки
    localStorage.removeItem(REMIND_KEY);
    return remindDate === today;
  }
  return false;
}

/**
 * Хук для управления показом триггеров конверсии.
 *
 * Гарантирует, что показываем не чаще 1 раза за сессию.
 */
export function useConversionPrompt() {
  // Ленивая инициализация — проверяем sessionStorage только при первом рендере
  const [shouldShow, setShouldShow] = useState(getInitialShouldShow);

  /**
   * Отметить, что триггер был показан.
   */
  const markShown = useCallback(() => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem(SESSION_KEY, "true");
      setShouldShow(false);
    }
  }, []);

  return { shouldShow, markShown };
}

/**
 * Хук для проверки напоминания "на завтра".
 *
 * Возвращает true, если сегодня — день напоминания.
 */
export function useRemindTodayCheck(): boolean {
  // Ленивая инициализация — проверяем localStorage только при первом рендере
  // useMemo гарантирует, что значение вычисляется один раз
  const shouldRemind = useMemo(() => getInitialShouldRemind(), []);
  return shouldRemind;
}

/**
 * Сохранить напоминание на завтра.
 */
export function setRemindTomorrow() {
  if (typeof window !== "undefined") {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split("T")[0];
    localStorage.setItem(REMIND_KEY, tomorrowStr);
  }
}

// ============================================
// Компонент: Предупреждение о приближении к лимиту
// ============================================

interface LimitWarningProps {
  /** Осталось этикеток */
  remaining: number;
  /** Всего в лимите */
  total: number;
  /** Обработчик перехода на страницу тарифов */
  onUpgrade: () => void;
  /** Обработчик закрытия */
  onClose?: () => void;
}

/**
 * Предупреждение о приближении к лимиту.
 *
 * Показывается когда осталось ≤10 этикеток из месячного лимита.
 */
export function LimitWarning({
  remaining,
  total,
  onUpgrade,
  onClose,
}: LimitWarningProps) {
  // Не показываем, если осталось больше 10
  if (remaining > 10) {
    return null;
  }

  const used = total - remaining;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <TrendingUp className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-900">
              Лимит: {used}/{total} этикеток в этом месяце
            </p>
            <p className="text-sm text-amber-700 mt-1">
              Нужно больше? Про — 2000 этикеток/мес с накоплением за 490 руб/мес
            </p>
            <Button
              variant="secondary"
              size="sm"
              onClick={onUpgrade}
              className="mt-3 bg-amber-100 hover:bg-amber-200 text-amber-900 border-amber-300"
            >
              <Sparkles className="w-4 h-4" />
              Подробнее
            </Button>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-amber-500 hover:text-amber-700 p-1"
            aria-label="Закрыть"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================
// Компонент: Лимит исчерпан
// ============================================

interface LimitExhaustedProps {
  /** Обработчик перехода на страницу тарифов */
  onUpgrade: () => void;
  /** Обработчик "Напомнить завтра" */
  onRemindTomorrow: () => void;
}

/**
 * Уведомление об исчерпании месячного лимита.
 *
 * Показывается когда remaining === 0.
 */
export function LimitExhausted({
  onUpgrade,
  onRemindTomorrow,
}: LimitExhaustedProps) {
  return (
    <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
      <div className="flex items-start gap-4">
        <AlertTriangle className="w-8 h-8 text-rose-500 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="font-semibold text-rose-900 text-lg mb-2">
            Месячный лимит исчерпан
          </h3>
          <p className="text-rose-700 mb-3">Варианты:</p>
          <ul className="text-sm text-rose-700 space-y-1 mb-4">
            <li className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Подождать до следующего месяца
            </li>
            <li className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              Перейти на Про — 2000 этикеток/мес с накоплением за 490 руб/мес
            </li>
          </ul>
          <div className="flex flex-wrap gap-3">
            <Button variant="primary" onClick={onUpgrade}>
              <Sparkles className="w-4 h-4" />
              Купить Про
            </Button>
            <Button
              variant="secondary"
              onClick={onRemindTomorrow}
              className="text-rose-700"
            >
              <Clock className="w-4 h-4" />
              Напомнить завтра
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Компонент: Напоминание (показывается на следующий день)
// ============================================

interface ReminderBannerProps {
  /** Обработчик перехода на страницу тарифов */
  onUpgrade: () => void;
  /** Обработчик закрытия */
  onClose: () => void;
}

/**
 * Баннер-напоминание о Pro тарифе.
 *
 * Показывается если пользователь вчера нажал "Напомнить завтра".
 */
export function ReminderBanner({ onUpgrade, onClose }: ReminderBannerProps) {
  return (
    <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-emerald-900">
              В этом месяце лимит закончился раньше времени?
            </p>
            <p className="text-sm text-emerald-700 mt-1">
              С Про тарифом — 2000 этикеток в месяц с накоплением до 10 000 шт. Никаких
              ограничений!
            </p>
            <Button
              variant="primary"
              size="sm"
              onClick={onUpgrade}
              className="mt-3"
            >
              <Sparkles className="w-4 h-4" />
              Попробовать Про
            </Button>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-emerald-500 hover:text-emerald-700 p-1"
          aria-label="Закрыть"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ============================================
// Обёртка с роутингом
// ============================================

interface ConversionPromptsProps {
  /** Осталось этикеток */
  remaining: number;
  /** Всего в лимите */
  total: number;
  /** Тариф пользователя */
  plan: "free" | "pro" | "enterprise";
}

/**
 * Определяем, какой триггер показывать изначально.
 */
type PromptType = "reminder" | "exhausted" | "warning" | null;

function determineInitialPrompt(
  plan: "free" | "pro" | "enterprise",
  remaining: number,
  shouldShow: boolean,
  shouldRemind: boolean
): PromptType {
  // Триггеры только для Free пользователей
  if (plan !== "free") {
    return null;
  }

  // Напоминание имеет приоритет
  if (shouldRemind) {
    return "reminder";
  }

  // Если уже показывали в этой сессии — выходим
  if (!shouldShow) {
    return null;
  }

  // Лимит исчерпан
  if (remaining === 0) {
    return "exhausted";
  }

  // Приближаемся к лимиту
  if (remaining <= 10) {
    return "warning";
  }

  return null;
}

/**
 * Обёртка для всех триггеров конверсии.
 *
 * Автоматически определяет, какой компонент показывать,
 * и управляет логикой "не чаще 1 раза в сессию".
 */
export function ConversionPrompts({
  remaining,
  total,
  plan,
}: ConversionPromptsProps) {
  const router = useRouter();
  const { shouldShow, markShown } = useConversionPrompt();
  const shouldRemind = useRemindTodayCheck();

  // Вычисляем начальный тип триггера один раз
  const initialPrompt = useMemo(
    () => determineInitialPrompt(plan, remaining, shouldShow, shouldRemind),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [] // Вычисляем только при первом рендере
  );

  // Состояние для отслеживания закрытия
  const [dismissed, setDismissed] = useState(false);

  // Отмечаем показ триггера при первом рендере (кроме reminder)
  const hasMarkedRef = useRef(false);
  useEffect(() => {
    if (!hasMarkedRef.current && initialPrompt && initialPrompt !== "reminder") {
      markShown();
      hasMarkedRef.current = true;
    }
  }, [initialPrompt, markShown]);

  /**
   * Переход на страницу подписки.
   */
  const handleUpgrade = useCallback(() => {
    router.push("/app/subscription");
  }, [router]);

  /**
   * Обработчик "Напомнить завтра".
   */
  const handleRemindTomorrow = useCallback(() => {
    setRemindTomorrow();
    setDismissed(true);
  }, []);

  /**
   * Закрыть триггер.
   */
  const handleClose = useCallback(() => {
    setDismissed(true);
  }, []);

  // Если закрыли или нечего показывать — выходим
  if (dismissed || !initialPrompt) {
    return null;
  }

  // Рендерим соответствующий компонент
  if (initialPrompt === "reminder") {
    return (
      <ReminderBanner onUpgrade={handleUpgrade} onClose={handleClose} />
    );
  }

  if (initialPrompt === "exhausted") {
    return (
      <LimitExhausted
        onUpgrade={handleUpgrade}
        onRemindTomorrow={handleRemindTomorrow}
      />
    );
  }

  if (initialPrompt === "warning") {
    return (
      <LimitWarning
        remaining={remaining}
        total={total}
        onUpgrade={handleUpgrade}
        onClose={handleClose}
      />
    );
  }

  return null;
}
