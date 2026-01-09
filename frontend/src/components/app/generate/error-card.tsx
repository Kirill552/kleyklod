"use client";

/**
 * Компонент для отображения дружелюбных ошибок.
 *
 * Показывает понятное сообщение с подсказкой и кнопкой повтора.
 */

import { AlertCircle, RefreshCw, XCircle } from "lucide-react";

interface ErrorCardProps {
  message: string;
  hint?: string;
  variant?: "error" | "warning";
  onRetry?: () => void;
  onReload?: () => void; // Кнопка "Загрузить заново" для ошибок связанных с данными файлов
  onDismiss?: () => void;
  className?: string;
}

export function ErrorCard({
  message,
  hint,
  variant = "error",
  onRetry,
  onReload,
  onDismiss,
  className,
}: ErrorCardProps) {
  const isError = variant === "error";

  return (
    <div
      className={`
        relative p-4 rounded-xl border-2
        ${
          isError
            ? "bg-red-50 border-red-200"
            : "bg-amber-50 border-amber-200"
        }
        ${className || ""}
      `}
    >
      {/* Кнопка закрытия */}
      {onDismiss && (
        <button
          onClick={onDismiss}
          className={`
            absolute top-3 right-3 p-1 rounded-full transition-colors
            ${
              isError
                ? "text-red-400 hover:text-red-600 hover:bg-red-100"
                : "text-amber-400 hover:text-amber-600 hover:bg-amber-100"
            }
          `}
          aria-label="Закрыть"
        >
          <XCircle className="w-5 h-5" />
        </button>
      )}

      <div className="flex items-start gap-3 pr-8">
        {/* Иконка */}
        <AlertCircle
          className={`
            w-6 h-6 flex-shrink-0 mt-0.5
            ${isError ? "text-red-500" : "text-amber-500"}
          `}
        />

        {/* Контент */}
        <div className="flex-1">
          <p
            className={`
              font-medium
              ${isError ? "text-red-800" : "text-amber-800"}
            `}
          >
            {message}
          </p>

          {hint && (
            <p
              className={`
                mt-1 text-sm
                ${isError ? "text-red-600" : "text-amber-600"}
              `}
            >
              {hint}
            </p>
          )}

          {/* Кнопки действий */}
          {(onRetry || onReload) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className={`
                    px-4 py-2 rounded-lg font-medium text-sm
                    flex items-center gap-2 transition-colors
                    ${
                      isError
                        ? "bg-red-100 text-red-700 hover:bg-red-200"
                        : "bg-amber-100 text-amber-700 hover:bg-amber-200"
                    }
                  `}
                >
                  <RefreshCw className="w-4 h-4" />
                  Попробовать снова
                </button>
              )}
              {onReload && (
                <button
                  onClick={onReload}
                  className={`
                    px-4 py-2 rounded-lg font-medium text-sm
                    flex items-center gap-2 transition-colors
                    ${
                      isError
                        ? "bg-red-600 text-white hover:bg-red-700"
                        : "bg-amber-600 text-white hover:bg-amber-700"
                    }
                  `}
                >
                  Загрузить заново
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Простой inline-вариант для мелких предупреждений.
 */
interface InlineErrorProps {
  message: string;
  className?: string;
}

export function InlineError({ message, className }: InlineErrorProps) {
  return (
    <p className={`text-sm text-red-600 flex items-center gap-1 ${className || ""}`}>
      <AlertCircle className="w-4 h-4" />
      {message}
    </p>
  );
}

/**
 * Карточка предупреждения (не критическая ошибка).
 */
interface WarningCardProps {
  message: string;
  hint?: string;
  className?: string;
}

export function WarningCard({ message, hint, className }: WarningCardProps) {
  return (
    <ErrorCard
      message={message}
      hint={hint}
      variant="warning"
      className={className}
    />
  );
}
