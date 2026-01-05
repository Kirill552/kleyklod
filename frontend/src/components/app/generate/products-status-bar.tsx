"use client";

/**
 * Информационная строка о статусе базы товаров.
 *
 * Показывает:
 * - Сколько товаров в базе пользователя
 * - Сколько из загруженных баркодов найдено в базе
 * - Для FREE плана — предложение перейти на PRO
 */

import { useState, useEffect, useMemo } from "react";
import { Database, Crown, ExternalLink, Check, AlertCircle } from "lucide-react";
import { getProducts, type FileDetectionResult } from "@/lib/api";
import type { UserPlan } from "@/types/api";

interface ProductsStatusBarProps {
  /** Тарифный план пользователя */
  userPlan: UserPlan;
  /** Результат детекта файла (для извлечения баркодов) */
  fileDetectionResult?: FileDetectionResult | null;
  className?: string;
}

interface ProductsStats {
  total: number;
  canCreateMore: boolean;
  loading: boolean;
  error: string | null;
}

export function ProductsStatusBar({
  userPlan,
  fileDetectionResult,
  className,
}: ProductsStatusBarProps) {
  const [stats, setStats] = useState<ProductsStats>({
    total: 0,
    canCreateMore: true,
    loading: true,
    error: null,
  });

  // Загружаем статистику товаров при монтировании
  useEffect(() => {
    const loadStats = async () => {
      // Для FREE плана не загружаем — база недоступна
      if (userPlan === "free") {
        setStats({
          total: 0,
          canCreateMore: false,
          loading: false,
          error: null,
        });
        return;
      }

      try {
        // Запрашиваем только 1 элемент чтобы получить total
        const data = await getProducts({ limit: 1 });
        setStats({
          total: data.total,
          canCreateMore: data.can_create_more,
          loading: false,
          error: null,
        });
      } catch (err) {
        setStats({
          total: 0,
          canCreateMore: true,
          loading: false,
          error: err instanceof Error ? err.message : "Ошибка загрузки",
        });
      }
    };

    loadStats();
  }, [userPlan]);

  // Подсчитываем сколько баркодов в загруженном файле
  const uploadedBarcodesCount = useMemo(() => {
    return fileDetectionResult?.rows_count || 0;
  }, [fileDetectionResult]);

  // Не показываем пока загружается
  if (stats.loading) {
    return null;
  }

  // FREE план — предложение PRO
  if (userPlan === "free") {
    return (
      <div
        className={`flex items-center gap-2 px-4 py-2.5 rounded-lg bg-amber-50 border border-amber-200 ${className || ""}`}
      >
        <Crown className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <span className="text-sm text-amber-800">
          {uploadedBarcodesCount > 0 ? (
            <>
              {uploadedBarcodesCount} товаров.{" "}
              <a
                href="/app/subscription"
                className="font-medium underline underline-offset-2 hover:text-amber-900"
              >
                База карточек доступна в PRO
              </a>
            </>
          ) : (
            <>
              База карточек товаров доступна в{" "}
              <a
                href="/app/subscription"
                className="font-medium underline underline-offset-2 hover:text-amber-900"
              >
                PRO плане
              </a>
            </>
          )}
        </span>
      </div>
    );
  }

  // Ошибка загрузки
  if (stats.error) {
    return (
      <div
        className={`flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-50 border border-red-200 ${className || ""}`}
      >
        <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
        <span className="text-sm text-red-700">
          Не удалось загрузить базу товаров
        </span>
      </div>
    );
  }

  // PRO/ENTERPRISE — показываем статистику
  const hasProducts = stats.total > 0;

  return (
    <div
      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg ${
        hasProducts
          ? "bg-emerald-50 border border-emerald-200"
          : "bg-warm-gray-50 border border-warm-gray-200"
      } ${className || ""}`}
    >
      {hasProducts ? (
        <>
          <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span className="text-sm text-emerald-800">
            <span className="font-medium">{stats.total}</span> товаров в базе
            {uploadedBarcodesCount > 0 && (
              <span className="text-emerald-600">
                {" "}
                — данные подтянутся автоматически
              </span>
            )}
          </span>
        </>
      ) : (
        <>
          <Database className="w-4 h-4 text-warm-gray-500 flex-shrink-0" />
          <span className="text-sm text-warm-gray-600">
            База товаров пуста.{" "}
            <a
              href="/app/products"
              className="text-emerald-600 font-medium underline underline-offset-2 hover:text-emerald-700"
            >
              Добавить товары
            </a>{" "}
            для автозаполнения этикеток
          </span>
        </>
      )}

      {/* Ссылка на базу товаров */}
      {hasProducts && (
        <a
          href="/app/products"
          className="ml-auto text-xs text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
        >
          <ExternalLink className="w-3 h-3" />
          Открыть базу
        </a>
      )}
    </div>
  );
}

/**
 * Компактная версия — только бейдж.
 */
interface ProductsStatusBadgeProps {
  userPlan: UserPlan;
  productsCount: number;
}

export function ProductsStatusBadge({
  userPlan,
  productsCount,
}: ProductsStatusBadgeProps) {
  if (userPlan === "free") {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
        <Crown className="w-3 h-3" />
        PRO
      </span>
    );
  }

  if (productsCount > 0) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
        <Database className="w-3 h-3" />
        {productsCount} в базе
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-warm-gray-500 bg-warm-gray-100 px-2 py-1 rounded">
      <Database className="w-3 h-3" />
      Нет товаров
    </span>
  );
}
