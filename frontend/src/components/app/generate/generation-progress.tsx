"use client";

/**
 * Компонент прогресса генерации этикеток.
 *
 * Показывает:
 * - Progress bar с процентами
 * - Этапы генерации (чеклист)
 * - Результаты preflight проверок
 */

import { Check, Loader2, Circle } from "lucide-react";
import { PreflightCheck } from "@/lib/api";

export type GenerationPhase =
  | "idle"
  | "validating"
  | "generating"
  | "checking"
  | "complete"
  | "error";

interface GenerationProgressProps {
  phase: GenerationPhase;
  progress: number; // 0-100
  checks?: PreflightCheck[];
  className?: string;
}

const STEPS = [
  { phase: "validating" as const, label: "Проверка файлов" },
  { phase: "generating" as const, label: "Генерация этикеток" },
  { phase: "checking" as const, label: "Проверка качества" },
  { phase: "complete" as const, label: "Готово!" },
];

export function GenerationProgress({
  phase,
  progress,
  checks = [],
  className,
}: GenerationProgressProps) {
  // Определяем индекс текущего этапа
  const currentStepIndex = STEPS.findIndex((s) => s.phase === phase);

  return (
    <div className={`space-y-6 ${className || ""}`}>
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-warm-gray-600">Прогресс</span>
          <span className="font-medium text-emerald-600">{progress}%</span>
        </div>
        <div className="h-3 bg-warm-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Этапы */}
      <div className="space-y-3">
        {STEPS.map((step, index) => {
          const isDone = index < currentStepIndex;
          const isActive =
            index === currentStepIndex && phase !== "complete" && phase !== "error";
          const isPending = index > currentStepIndex;

          return (
            <div key={step.phase} className="flex items-center gap-3">
              {/* Иконка статуса */}
              <div
                className={`
                  w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
                  ${isDone ? "bg-emerald-500" : ""}
                  ${isActive ? "bg-emerald-100" : ""}
                  ${isPending ? "bg-warm-gray-100" : ""}
                `}
              >
                {isDone && <Check className="w-4 h-4 text-white" />}
                {isActive && (
                  <Loader2 className="w-4 h-4 text-emerald-600 animate-spin" />
                )}
                {isPending && <Circle className="w-3 h-3 text-warm-gray-400" />}
              </div>

              {/* Текст */}
              <span
                className={`
                  ${isDone ? "text-emerald-600" : ""}
                  ${isActive ? "text-warm-gray-800 font-medium" : ""}
                  ${isPending ? "text-warm-gray-400" : ""}
                `}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Preflight проверки (показываем на этапе checking и complete) */}
      {(phase === "checking" || phase === "complete") && checks.length > 0 && (
        <div className="mt-4 p-4 bg-warm-gray-50 rounded-xl border border-warm-gray-200">
          <h4 className="font-medium text-warm-gray-800 mb-3">
            Результаты проверки качества:
          </h4>
          <div className="space-y-2">
            {checks.map((check, i) => (
              <PreflightCheckItem key={i} check={check} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Отдельный элемент preflight проверки.
 */
interface PreflightCheckItemProps {
  check: PreflightCheck;
}

function PreflightCheckItem({ check }: PreflightCheckItemProps) {
  const statusColors = {
    ok: "text-emerald-600 bg-emerald-100",
    warning: "text-amber-600 bg-amber-100",
    error: "text-red-600 bg-red-100",
  };

  const statusIcons = {
    ok: "✓",
    warning: "!",
    error: "✕",
  };

  return (
    <div className="flex items-start gap-2">
      <span
        className={`
          w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0
          ${statusColors[check.status]}
        `}
      >
        {statusIcons[check.status]}
      </span>
      <div className="flex-1">
        <p className="text-sm text-warm-gray-700">{check.message}</p>
        {check.details && Object.keys(check.details).length > 0 && (
          <p className="text-xs text-warm-gray-500 mt-0.5">
            {Object.entries(check.details)
              .map(([k, v]) => `${k}: ${v}`)
              .join(", ")}
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * Детальная версия проверки качества для карточки результата.
 * Показывает все проверки с человекочитаемыми описаниями.
 */
interface PreflightSummaryProps {
  checks: PreflightCheck[];
  className?: string;
  /** Компактный режим — только счётчики без деталей */
  compact?: boolean;
}

/**
 * Человекочитаемые описания проверок с пояснениями ГОСТ vs KleyKod.
 * Имена соответствуют backend/app/services/preflight.py
 */
const CHECK_DESCRIPTIONS: Record<string, { label: string; getDetail: (check: PreflightCheck) => string }> = {
  // Размер DataMatrix
  datamatrix_size: {
    label: "Размер DataMatrix",
    getDetail: (check) => {
      const width = check.details?.width_mm;
      const height = check.details?.height_mm;
      if (width && height) {
        return `${width}×${height} мм — Рекомендация KleyKod (ГОСТ: от 10 мм)`;
      }
      return "Рекомендация KleyKod (ГОСТ: от 10 мм)";
    },
  },
  // Зона покоя
  quiet_zone: {
    label: "Зона покоя",
    getDetail: (check) => {
      const minMm = check.details?.min_margin_mm;
      if (minMm) {
        return `${minMm} мм — Рекомендация KleyKod (ГОСТ: от 0.25 мм)`;
      }
      return "Рекомендация KleyKod (ГОСТ: от 0.25 мм)";
    },
  },
  // Контрастность
  contrast: {
    label: "Контрастность",
    getDetail: (check) => {
      const contrast = check.details?.contrast_percent;
      if (contrast !== undefined) {
        return `${contrast}% — ${Number(contrast) >= 80 ? "выше" : "ниже"} рекомендации KleyKod (80%)`;
      }
      return "Рекомендация KleyKod: 80%+";
    },
  },
  // Читаемость DataMatrix
  datamatrix_readable: {
    label: "Читаемость кодов",
    getDetail: () => "Все коды читаются сканером",
  },
  // Соответствие количества
  count_match: {
    label: "Количество",
    getDetail: (check) => {
      const pages = check.details?.pages;
      const codes = check.details?.codes;
      if (pages && pages === codes) {
        return `Совпадает — ${pages} этикеток`;
      }
      if (pages && codes) {
        return `Страниц: ${pages}, кодов: ${codes}`;
      }
      return "Количество этикеток и кодов совпадает";
    },
  },
  // Консистентность GTIN
  gtin_consistency: {
    label: "GTIN",
    getDetail: (check) => {
      const gtinCount = check.details?.gtins_count as number | undefined;
      if (gtinCount === 1) {
        return "Единый — все коды для одного товара";
      }
      if (gtinCount && gtinCount > 1) {
        return `${gtinCount} разных товаров — микс-поставка`;
      }
      return "Проверка GTIN";
    },
  },
  // Парсинг PDF
  pdf_parse: {
    label: "Обработка PDF",
    getDetail: (check) => {
      const pageCount = check.details?.page_count;
      if (pageCount) {
        return `${pageCount} страниц обработано`;
      }
      return "PDF успешно обработан";
    },
  },
  // Парсинг кодов
  codes_parse: {
    label: "Парсинг кодов",
    getDetail: (check) => {
      const count = check.details?.count;
      if (count) {
        return `${count} кодов распознано`;
      }
      return "Коды маркировки распознаны";
    },
  },
  // Количество кодов (для check_codes_only)
  codes_count: {
    label: "Количество кодов",
    getDetail: (check) => {
      const count = check.details?.count;
      if (count) {
        return `Получено ${count} кодов`;
      }
      return "Коды получены";
    },
  },
  // Дубликаты
  duplicates: {
    label: "Дубликаты",
    getDetail: () => "Обнаружены повторяющиеся коды",
  },
  // Генерация DataMatrix
  datamatrix_generate: {
    label: "Генерация DataMatrix",
    getDetail: () => "Ошибка создания DataMatrix",
  },
  // Общая проверка кодов
  codes_check: {
    label: "Проверка кодов",
    getDetail: () => "Проверка кодов маркировки",
  },
};

export function PreflightSummary({ checks, className, compact = false }: PreflightSummaryProps) {
  if (!checks.length) return null;

  const okCount = checks.filter((c) => c.status === "ok").length;
  const warningCount = checks.filter((c) => c.status === "warning").length;
  const errorCount = checks.filter((c) => c.status === "error").length;

  // Компактный режим — только счётчики
  if (compact) {
    return (
      <div className={`flex items-center gap-4 text-sm ${className || ""}`}>
        {okCount > 0 && (
          <span className="flex items-center gap-1 text-emerald-600">
            <span className="w-4 h-4 rounded-full bg-emerald-100 flex items-center justify-center text-xs">
              ✓
            </span>
            {okCount}
          </span>
        )}
        {warningCount > 0 && (
          <span className="flex items-center gap-1 text-amber-600">
            <span className="w-4 h-4 rounded-full bg-amber-100 flex items-center justify-center text-xs">
              !
            </span>
            {warningCount}
          </span>
        )}
        {errorCount > 0 && (
          <span className="flex items-center gap-1 text-red-600">
            <span className="w-4 h-4 rounded-full bg-red-100 flex items-center justify-center text-xs">
              ✕
            </span>
            {errorCount}
          </span>
        )}
      </div>
    );
  }

  // Полный режим — детальный список проверок
  return (
    <div className={`space-y-3 ${className || ""}`}>
      {/* Заголовок со счётчиком */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-warm-gray-700">
          Проверка качества
        </span>
        <span className="text-sm text-warm-gray-500">
          {okCount} из {checks.length} пунктов ✓
        </span>
      </div>

      {/* Детальный список проверок */}
      <div className="space-y-2">
        {checks.map((check, i) => {
          const description = CHECK_DESCRIPTIONS[check.name || ""];
          const statusColors = {
            ok: "text-emerald-600 bg-emerald-50",
            warning: "text-amber-600 bg-amber-50",
            error: "text-red-600 bg-red-50",
          };
          const statusIcons = {
            ok: "✓",
            warning: "!",
            error: "✕",
          };

          return (
            <div
              key={i}
              className={`flex items-start gap-2 p-2 rounded-lg ${statusColors[check.status]}`}
            >
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-white/60 flex items-center justify-center text-xs font-bold">
                {statusIcons[check.status]}
              </span>
              <div className="flex-1 min-w-0">
                <span className="text-sm font-medium">
                  {description?.label || check.name || "Проверка"}
                </span>
                <span className="text-sm opacity-80 ml-1">
                  — {description ? description.getDetail(check) : check.message}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
