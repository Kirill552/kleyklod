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
 * Компактная версия для встраивания в карточку результата.
 */
interface PreflightSummaryProps {
  checks: PreflightCheck[];
  className?: string;
}

export function PreflightSummary({ checks, className }: PreflightSummaryProps) {
  if (!checks.length) return null;

  const okCount = checks.filter((c) => c.status === "ok").length;
  const warningCount = checks.filter((c) => c.status === "warning").length;
  const errorCount = checks.filter((c) => c.status === "error").length;

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
