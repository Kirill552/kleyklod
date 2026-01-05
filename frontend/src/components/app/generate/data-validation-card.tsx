"use client";

/**
 * Компонент проверки данных ДО генерации.
 *
 * Показывает заполненность полей для выбранного шаблона,
 * чтобы пользователь знал о пустых полях до траты лимита.
 */

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ClipboardList,
  Check,
  AlertTriangle,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import type { LabelLayout, FileDetectionResult } from "@/lib/api";

/** Конфигурация полей для каждого шаблона */
const TEMPLATE_FIELDS: Record<LabelLayout, FieldRequirement[]> = {
  basic: [
    { id: "barcode", label: "Баркод", required: true },
  ],
  professional: [
    { id: "barcode", label: "Баркод", required: true },
    { id: "name", label: "Название", required: false },
    { id: "article", label: "Артикул", required: false },
    { id: "size", label: "Размер", required: false },
    { id: "color", label: "Цвет", required: false },
    { id: "organization", label: "Организация", required: false, fromSettings: true },
  ],
  extended: [
    { id: "barcode", label: "Баркод", required: true },
    { id: "name", label: "Название", required: false },
    { id: "article", label: "Артикул", required: false },
    { id: "size", label: "Размер", required: false },
    { id: "color", label: "Цвет", required: false },
    { id: "organization", label: "Организация", required: false, fromSettings: true },
    { id: "inn", label: "ИНН", required: false, fromSettings: true },
    { id: "composition", label: "Состав", required: false },
    { id: "country", label: "Страна", required: false },
    { id: "brand", label: "Бренд", required: false },
    { id: "manufacturer", label: "Производитель", required: false },
  ],
};

/** Требование к полю */
interface FieldRequirement {
  id: string;
  label: string;
  required: boolean;
  /** Поле берётся из настроек, а не из Excel */
  fromSettings?: boolean;
}

/** Статистика заполненности поля */
interface FieldStats {
  id: string;
  label: string;
  filled: number;
  empty: number;
  total: number;
  source: "Excel" | "Настройки" | "—";
  required: boolean;
}

interface DataValidationCardProps {
  layout: LabelLayout;
  fileDetectionResult: FileDetectionResult | null;
  /** Данные из настроек */
  organizationName?: string;
  inn?: string;
  /** Кастомные строки для Расширенного шаблона */
  customLinesCount?: number;
  /** Callback для смены шаблона */
  onChangeLayout?: (layout: LabelLayout) => void;
  className?: string;
}

export function DataValidationCard({
  layout,
  fileDetectionResult,
  organizationName,
  inn,
  customLinesCount = 0,
  onChangeLayout,
  className,
}: DataValidationCardProps) {
  const totalRows = fileDetectionResult?.rows_count || fileDetectionResult?.sample_items?.length || 0;
  const fields = TEMPLATE_FIELDS[layout];

  // Анализируем заполненность полей (useMemo должен быть ДО early return)
  const fieldStats = useMemo((): FieldStats[] => {
    // Для basic или если нет данных — пустой массив
    if (layout === "basic" || !fileDetectionResult?.sample_items?.length) {
      return [];
    }

    const stats: FieldStats[] = [];

    for (const field of fields) {
      // Пропускаем баркод — он всегда есть
      if (field.id === "barcode") continue;

      let filled = 0;
      let source: "Excel" | "Настройки" | "—" = "—";

      if (field.fromSettings) {
        // Поля из настроек
        if (field.id === "organization" && organizationName) {
          filled = totalRows;
          source = "Настройки";
        } else if (field.id === "inn" && inn) {
          filled = totalRows;
          source = "Настройки";
        }
      } else {
        // Поля из Excel — считаем по sample (примерно)
        const sampleItems = fileDetectionResult.sample_items || [];
        const sampleFilled = sampleItems.filter((item) => {
          const value = item[field.id as keyof typeof item];
          return value !== null && value !== undefined && value !== "";
        }).length;

        // Экстраполируем на все строки
        if (sampleItems.length > 0) {
          const fillRate = sampleFilled / sampleItems.length;
          filled = Math.round(fillRate * totalRows);
          source = filled > 0 ? "Excel" : "—";
        }
      }

      stats.push({
        id: field.id,
        label: field.label,
        filled,
        empty: totalRows - filled,
        total: totalRows,
        source,
        required: field.required,
      });
    }

    return stats;
  }, [layout, fields, fileDetectionResult, organizationName, inn, totalRows]);

  // Early return после всех hooks
  if (layout === "basic" || !fileDetectionResult?.sample_items?.length) {
    return null;
  }

  // Считаем общую статистику
  const totalEmpty = fieldStats.reduce((sum, f) => sum + f.empty, 0);
  // Для Расширенного шаблона проверяем также кастомные строки
  const customLinesEmpty = layout === "extended" && customLinesCount === 0;
  const hasEmptyFields = totalEmpty > 0 || customLinesEmpty;
  const allFilled = !hasEmptyFields;

  return (
    <Card className={`border-warm-gray-200 ${className || ""}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <ClipboardList className="w-5 h-5 text-emerald-600" />
          Данные для этикеток
          {allFilled ? (
            <span className="ml-auto flex items-center gap-1 text-sm font-normal text-emerald-600">
              <Check className="w-4 h-4" />
              Всё заполнено
            </span>
          ) : (
            <span className="ml-auto flex items-center gap-1 text-sm font-normal text-amber-600">
              <AlertTriangle className="w-4 h-4" />
              Есть пустые поля
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Таблица полей */}
        <div className="rounded-lg border border-warm-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-warm-gray-50">
              <tr>
                <th className="text-left px-3 py-2 font-medium text-warm-gray-600">
                  Поле
                </th>
                <th className="text-center px-3 py-2 font-medium text-warm-gray-600 w-24">
                  Заполнено
                </th>
                <th className="text-center px-3 py-2 font-medium text-warm-gray-600 w-20">
                  Пусто
                </th>
                <th className="text-left px-3 py-2 font-medium text-warm-gray-600 w-28">
                  Источник
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-warm-gray-100">
              {fieldStats.map((field) => (
                <tr
                  key={field.id}
                  className={
                    field.empty === field.total
                      ? "bg-amber-50/50"
                      : field.empty > 0
                        ? "bg-amber-50/30"
                        : ""
                  }
                >
                  <td className="px-3 py-2 text-warm-gray-800">
                    {field.label}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {field.filled > 0 ? (
                      <span className="text-emerald-600 font-medium">
                        {field.filled}
                      </span>
                    ) : (
                      <span className="text-warm-gray-400">0</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {field.empty > 0 ? (
                      <span className="text-amber-600 font-medium">
                        {field.empty}
                      </span>
                    ) : (
                      <span className="text-warm-gray-400">0</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-warm-gray-500 text-xs">
                    {field.source}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Предупреждение о пустых кастомных строках для Расширенного шаблона */}
        {customLinesEmpty && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800">
                  Кастомные строки не заполнены
                </p>
                <p className="text-xs text-amber-700 mt-1">
                  Для Расширенного шаблона настройте 3 дополнительные строки в{" "}
                  <a href="/app/settings" className="underline hover:text-amber-900">
                    Настройках
                  </a>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Пояснение и действия */}
        {hasEmptyFields && !customLinesEmpty && (
          <div className="space-y-3">
            <p className="text-sm text-warm-gray-600">
              <strong>Пустые поля не покажутся на этикетке.</strong> Это не
              ошибка — можно генерировать.
            </p>

            <div className="flex flex-wrap gap-2">
              {/* Предложить сменить шаблон */}
              {layout === "extended" && onChangeLayout && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onChangeLayout("professional")}
                  className="text-xs"
                >
                  <ChevronRight className="w-3 h-3" />
                  Профессиональный (меньше полей)
                </Button>
              )}

              {/* Ссылка на базу товаров */}
              <a
                href="/app/products"
                className="inline-flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700 underline underline-offset-2"
              >
                <ExternalLink className="w-3 h-3" />
                Заполнить в базе товаров
              </a>
            </div>
          </div>
        )}

        {/* Всё заполнено */}
        {allFilled && (
          <p className="text-sm text-emerald-600">
            Все поля для шаблона {layout === "professional" ? "Профессиональный" : "Расширенный"} заполнены.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Компактная версия — только индикатор статуса.
 */
interface DataValidationBadgeProps {
  layout: LabelLayout;
  fileDetectionResult: FileDetectionResult | null;
  organizationName?: string;
  inn?: string;
}

export function DataValidationBadge({
  layout,
  fileDetectionResult,
  organizationName,
  inn,
}: DataValidationBadgeProps) {
  // Не показываем для Basic
  if (layout === "basic" || !fileDetectionResult?.sample_items?.length) {
    return null;
  }

  const fields = TEMPLATE_FIELDS[layout];

  // Быстрая проверка наличия пустых полей
  let hasEmptyFields = false;

  for (const field of fields) {
    if (field.id === "barcode") continue;

    if (field.fromSettings) {
      if (field.id === "organization" && !organizationName) {
        hasEmptyFields = true;
        break;
      }
      if (field.id === "inn" && !inn) {
        hasEmptyFields = true;
        break;
      }
    } else {
      const sampleItems = fileDetectionResult.sample_items || [];
      const sampleEmpty = sampleItems.some((item) => {
        const value = item[field.id as keyof typeof item];
        return value === null || value === undefined || value === "";
      });
      if (sampleEmpty) {
        hasEmptyFields = true;
        break;
      }
    }
  }

  if (!hasEmptyFields) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
        <Check className="w-3 h-3" />
        Данные заполнены
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
      <AlertTriangle className="w-3 h-3" />
      Есть пустые поля
    </span>
  );
}
