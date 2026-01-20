"use client";

import { AlertTriangle, FileEdit, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface TruncationInfo {
  field: string;      // "Название", "Организация"
  original: string;   // Полный текст
  maxChars: number;   // Максимум символов
}

interface TextOverflowWarningProps {
  /** Список полей которые будут обрезаны */
  truncations: TruncationInfo[];
  /** Callback при нажатии "Продолжить" */
  onContinue: () => void;
  /** Callback при нажатии "Исправить" (закрыть warning) */
  onDismiss: () => void;
  /** Предложенный шаблон большего размера */
  suggestedTemplate?: string;
}

/**
 * Предупреждение об обрезке текста.
 * Показывается когда текст не влезает в шаблон.
 */
export function TextOverflowWarning({
  truncations,
  onContinue,
  onDismiss,
  suggestedTemplate,
}: TextOverflowWarningProps) {
  if (truncations.length === 0) return null;

  return (
    <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <AlertTriangle className="h-5 w-5 text-yellow-600" />
        <span className="font-medium text-yellow-800">
          Текст будет обрезан
        </span>
      </div>

      {/* Description */}
      <p className="text-sm text-yellow-700 mb-4">
        Некоторые поля слишком длинные для выбранного шаблона:
      </p>

      {/* List of truncations */}
      <ul className="space-y-2 mb-4">
        {truncations.map((t, idx) => (
          <li key={idx} className="text-sm">
            <span className="font-medium text-warm-gray-700">• {t.field}:</span>{" "}
            <span className="text-warm-gray-600">
              &ldquo;{truncateText(t.original, 40)}&rdquo;
            </span>
            <br />
            <span className="text-yellow-700 ml-3">
              → будет обрезано до ~{t.maxChars} символов
            </span>
          </li>
        ))}
      </ul>

      {/* Suggestion */}
      <div className="flex items-start gap-2 text-sm text-warm-gray-600 mb-4 bg-white/50 rounded p-2">
        <span className="text-lg">💡</span>
        <span>
          Совет: сократите текст в Excel
          {suggestedTemplate && (
            <>
              {" "}или выберите шаблон большего размера ({suggestedTemplate})
            </>
          )}
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          variant="secondary"
          size="sm"
          onClick={onDismiss}
          className="gap-2"
        >
          <FileEdit className="h-4 w-4" />
          Исправить в Excel
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={onContinue}
          className="gap-2 bg-yellow-600 hover:bg-yellow-700"
        >
          Продолжить с обрезкой
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

/** Обрезать текст для превью */
function truncateText(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen - 3) + "...";
}
