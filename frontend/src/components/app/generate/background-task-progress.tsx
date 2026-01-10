"use client";

/**
 * Компонент прогресса фоновой задачи Celery.
 *
 * Использует useTaskPolling для отслеживания статуса долгих операций
 * (генерация 50+ этикеток). Показывает реальный прогресс от бэкенда.
 */

import { useCallback } from "react";
import { Check, Loader2, AlertCircle, Download, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTaskPolling } from "@/hooks";
import type { TaskStatusResponse } from "@/lib/api";

interface BackgroundTaskProgressProps {
  /** ID задачи для отслеживания */
  taskId: string | null;
  /** Callback при успешном завершении */
  onComplete?: (result: TaskStatusResponse) => void;
  /** Callback при ошибке */
  onError?: (error: string) => void;
  /** Callback для скачивания результата */
  onDownload?: (resultUrl: string) => void;
  /** Callback для повторной попытки */
  onRetry?: () => void;
  className?: string;
}

/**
 * Компонент прогресса фоновой задачи.
 *
 * Автоматически polling статуса задачи с интервалом 3 сек.
 * Показывает прогресс-бар, статус и кнопку скачивания по завершении.
 */
export function BackgroundTaskProgress({
  taskId,
  onComplete,
  onError,
  onDownload,
  onRetry,
  className,
}: BackgroundTaskProgressProps) {
  const handleComplete = useCallback(
    (result: TaskStatusResponse) => {
      onComplete?.(result);
    },
    [onComplete]
  );

  const handleError = useCallback(
    (error: string) => {
      onError?.(error);
    },
    [onError]
  );

  const { status, progress, resultUrl, error, labelsCount, isPolling } = useTaskPolling(
    taskId,
    {
      onComplete: handleComplete,
      onError: handleError,
      interval: 3000,
    }
  );

  // Не показываем ничего если нет задачи
  if (!taskId) return null;

  // Определяем заголовок и описание в зависимости от статуса
  const getStatusInfo = () => {
    switch (status) {
      case "pending":
        return {
          title: "Задача в очереди",
          description: "Ожидание обработки...",
          icon: <Loader2 className="w-6 h-6 text-warm-gray-400 animate-spin" />,
          bgColor: "bg-warm-gray-50 border-warm-gray-200",
        };
      case "processing":
        return {
          title: "Генерация этикеток",
          description: `Обработано ${progress}%${labelsCount ? ` (${labelsCount} этикеток)` : ""}`,
          icon: <Loader2 className="w-6 h-6 text-emerald-600 animate-spin" />,
          bgColor: "bg-emerald-50 border-emerald-200",
        };
      case "completed":
        return {
          title: "Готово!",
          description: labelsCount ? `Создано ${labelsCount} этикеток` : "Этикетки созданы",
          icon: <Check className="w-6 h-6 text-emerald-600" />,
          bgColor: "bg-emerald-50 border-emerald-200",
        };
      case "failed":
        return {
          title: "Ошибка",
          description: error || "Произошла ошибка при генерации",
          icon: <AlertCircle className="w-6 h-6 text-red-600" />,
          bgColor: "bg-red-50 border-red-200",
        };
      default:
        return {
          title: "Загрузка...",
          description: "Получение статуса задачи",
          icon: <Loader2 className="w-6 h-6 text-warm-gray-400 animate-spin" />,
          bgColor: "bg-warm-gray-50 border-warm-gray-200",
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className={`rounded-xl border-2 p-6 ${statusInfo.bgColor} ${className || ""}`}>
      <div className="flex items-start gap-4">
        {/* Иконка статуса */}
        <div className="flex-shrink-0 w-12 h-12 rounded-full bg-white flex items-center justify-center shadow-sm">
          {statusInfo.icon}
        </div>

        {/* Контент */}
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-warm-gray-900">
            {statusInfo.title}
          </h3>
          <p className="text-sm text-warm-gray-600 mt-1">
            {statusInfo.description}
          </p>

          {/* Progress bar (только для pending и processing) */}
          {(status === "pending" || status === "processing") && (
            <div className="mt-4 space-y-2">
              <div className="h-3 bg-white rounded-full overflow-hidden shadow-inner">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-warm-gray-500">
                <span>{isPolling ? "Обновление каждые 3 сек" : ""}</span>
                <span className="font-medium text-emerald-600">{progress}%</span>
              </div>
            </div>
          )}

          {/* Кнопки действий */}
          {status === "completed" && resultUrl && (
            <div className="mt-4">
              <Button
                variant="primary"
                size="lg"
                onClick={() => onDownload?.(resultUrl)}
              >
                <Download className="w-5 h-5" />
                Скачать PDF
              </Button>
            </div>
          )}

          {status === "failed" && onRetry && (
            <div className="mt-4">
              <Button
                variant="secondary"
                onClick={onRetry}
              >
                <RefreshCw className="w-4 h-4" />
                Попробовать снова
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
