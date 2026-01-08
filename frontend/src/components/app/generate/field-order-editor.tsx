"use client";

import { Check, AlertTriangle, Ban, Scissors, ArrowRight } from "lucide-react";
import type { LabelLayout, LabelSize, LayoutPreflightError } from "@/lib/api";
import {
  isFieldSupported,
  checkFieldLength,
  getUnsupportedFieldHint,
  type FieldId,
} from "@/lib/label-field-config";

export interface FieldConfig {
  id: string;
  label: string;
  preview: string | null;
  enabled: boolean;
}

/** Быстрое действие для исправления ошибки */
export type QuickAction = "truncate" | "change_layout_extended";

interface FieldToggleProps {
  field: FieldConfig;
  onToggle: (id: string) => void;
  disabled?: boolean;
  disabledHint?: string;
  warning?: string;
  /** Ошибка preflight проверки */
  preflightError?: LayoutPreflightError;
  /** Callback для быстрых действий */
  onQuickAction?: (action: QuickAction) => void;
}

function FieldToggle({
  field,
  onToggle,
  disabled,
  disabledHint,
  warning,
  preflightError,
  onQuickAction,
}: FieldToggleProps) {
  // Определяем стили в зависимости от состояния
  const hasError = preflightError && field.enabled;

  const getContainerStyles = () => {
    if (disabled) {
      return "bg-warm-gray-100 border-warm-gray-200 opacity-60 cursor-not-allowed";
    }
    if (hasError) {
      return "bg-red-50 border-red-300";
    }
    if (warning && field.enabled) {
      return "bg-amber-50 border-amber-300";
    }
    if (field.enabled) {
      return "bg-emerald-50 border-emerald-200";
    }
    return "bg-warm-gray-50 border-warm-gray-200";
  };

  const getCheckboxStyles = () => {
    if (disabled) {
      return "bg-warm-gray-200 border-warm-gray-300 cursor-not-allowed";
    }
    if (hasError) {
      return "bg-red-500 border-red-500 text-white";
    }
    if (field.enabled) {
      return "bg-emerald-500 border-emerald-500 text-white";
    }
    return "bg-white border-warm-gray-300 hover:border-emerald-400";
  };

  const getLabelStyles = () => {
    if (disabled) {
      return "text-warm-gray-400";
    }
    if (hasError) {
      return "text-red-900";
    }
    if (warning && field.enabled) {
      return "text-amber-900";
    }
    if (field.enabled) {
      return "text-emerald-900";
    }
    return "text-warm-gray-600";
  };

  return (
    <div
      id={`field-${field.id}`}
      className={`flex flex-col gap-2 p-3 rounded-xl border-2 transition-all ${getContainerStyles()}`}
      title={disabled ? disabledHint : warning}
    >
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => !disabled && onToggle(field.id)}
          disabled={disabled}
          className={`h-5 w-5 rounded border-2 flex items-center justify-center transition-colors flex-shrink-0 ${getCheckboxStyles()}`}
        >
          {disabled ? (
            <Ban className="h-3 w-3 text-warm-gray-400" />
          ) : field.enabled ? (
            <Check className="h-3 w-3" />
          ) : null}
        </button>

        <div className="flex-1 min-w-0">
          <div className={`font-medium text-sm flex items-center gap-2 ${getLabelStyles()}`}>
            {field.label}
            {hasError && (
              <AlertTriangle className="h-3.5 w-3.5 text-red-500 flex-shrink-0" />
            )}
            {warning && field.enabled && !hasError && (
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500 flex-shrink-0" />
            )}
          </div>
          {field.preview && !disabled && (
            <div className="text-xs text-warm-gray-500 truncate">{field.preview}</div>
          )}
          {disabled && disabledHint && (
            <div className="text-xs text-warm-gray-400 truncate">{disabledHint}</div>
          )}
          {warning && field.enabled && !disabled && !hasError && (
            <div className="text-xs text-amber-600 truncate">{warning}</div>
          )}
        </div>
      </div>

      {/* Ошибка preflight с быстрыми действиями */}
      {hasError && (
        <div className="ml-8 space-y-2">
          <div className="text-xs text-red-600">
            {preflightError.message}
            {preflightError.suggestion && (
              <span className="text-red-500 ml-1">
                {preflightError.suggestion}
              </span>
            )}
          </div>
          {/* Быстрые действия */}
          {onQuickAction && (
            <div className="flex gap-2">
              {preflightError.message.toLowerCase().includes("текст") && (
                <button
                  type="button"
                  onClick={() => onQuickAction("truncate")}
                  className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium
                    bg-white border border-red-200 rounded-lg text-red-700
                    hover:bg-red-50 hover:border-red-300 transition-colors"
                >
                  <Scissors className="h-3 w-3" />
                  Сократить
                </button>
              )}
              {preflightError.message.toLowerCase().includes("полей") && (
                <button
                  type="button"
                  onClick={() => onQuickAction("change_layout_extended")}
                  className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium
                    bg-white border border-red-200 rounded-lg text-red-700
                    hover:bg-red-50 hover:border-red-300 transition-colors"
                >
                  <ArrowRight className="h-3 w-3" />
                  Extended
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface FieldOrderEditorProps {
  fields: FieldConfig[];
  onChange: (fields: FieldConfig[]) => void;
  /** Текущий шаблон */
  layout: LabelLayout;
  /** Текущий размер этикетки */
  size: LabelSize;
  /** Значения полей для проверки длины (из Excel) */
  fieldValues?: Record<string, string | null | undefined>;
  /** Ошибки preflight проверки (field_id -> error) */
  preflightErrors?: Map<string, LayoutPreflightError>;
  /** Callback для быстрых действий */
  onQuickAction?: (fieldId: string, action: QuickAction) => void;
}

export function FieldOrderEditor({
  fields,
  onChange,
  layout,
  size,
  fieldValues = {},
  preflightErrors,
  onQuickAction,
}: FieldOrderEditorProps) {
  const handleToggle = (id: string) => {
    // Проверяем, поддерживается ли поле
    if (!isFieldSupported(id as FieldId, layout, size)) {
      return;
    }

    onChange(
      fields.map((f) => (f.id === id ? { ...f, enabled: !f.enabled } : f))
    );
  };

  // Фильтруем поле "organization" — оно теперь обязательное справа
  const filteredFields = fields.filter((f) => f.id !== "organization");

  return (
    <div className="space-y-2">
      <div className="text-sm font-medium text-warm-gray-700 mb-2">
        Какие поля показывать на этикетке
      </div>
      <div className="space-y-2">
        {filteredFields.map((field) => {
          const fieldId = field.id as FieldId;
          const supported = isFieldSupported(fieldId, layout, size);
          const unsupportedHint = !supported
            ? getUnsupportedFieldHint(fieldId, layout, size)
            : undefined;

          // Проверяем длину значения поля
          const fieldValue = fieldValues[fieldId] || field.preview;
          const lengthCheck = checkFieldLength(fieldId, fieldValue, layout, size);

          // Получаем ошибку preflight для этого поля
          const preflightError = preflightErrors?.get(fieldId);

          return (
            <FieldToggle
              key={field.id}
              field={field}
              onToggle={handleToggle}
              disabled={!supported}
              disabledHint={unsupportedHint}
              warning={lengthCheck.isOverLimit ? lengthCheck.warning : undefined}
              preflightError={preflightError}
              onQuickAction={onQuickAction ? (action) => onQuickAction(fieldId, action) : undefined}
            />
          );
        })}
      </div>
    </div>
  );
}
