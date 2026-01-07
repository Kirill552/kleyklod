"use client";

import { Check, AlertTriangle, Ban } from "lucide-react";
import type { LabelLayout, LabelSize } from "@/lib/api";
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

interface FieldToggleProps {
  field: FieldConfig;
  onToggle: (id: string) => void;
  disabled?: boolean;
  disabledHint?: string;
  warning?: string;
}

function FieldToggle({
  field,
  onToggle,
  disabled,
  disabledHint,
  warning,
}: FieldToggleProps) {
  // Определяем стили в зависимости от состояния
  const getContainerStyles = () => {
    if (disabled) {
      return "bg-warm-gray-100 border-warm-gray-200 opacity-60 cursor-not-allowed";
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
    if (field.enabled) {
      return "bg-emerald-500 border-emerald-500 text-white";
    }
    return "bg-white border-warm-gray-300 hover:border-emerald-400";
  };

  const getLabelStyles = () => {
    if (disabled) {
      return "text-warm-gray-400";
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
      className={`flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${getContainerStyles()}`}
      title={disabled ? disabledHint : warning}
    >
      <button
        type="button"
        onClick={() => !disabled && onToggle(field.id)}
        disabled={disabled}
        className={`h-5 w-5 rounded border-2 flex items-center justify-center transition-colors ${getCheckboxStyles()}`}
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
          {warning && field.enabled && (
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500 flex-shrink-0" />
          )}
        </div>
        {field.preview && !disabled && (
          <div className="text-xs text-warm-gray-500 truncate">{field.preview}</div>
        )}
        {disabled && disabledHint && (
          <div className="text-xs text-warm-gray-400 truncate">{disabledHint}</div>
        )}
        {warning && field.enabled && !disabled && (
          <div className="text-xs text-amber-600 truncate">{warning}</div>
        )}
      </div>
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
}

export function FieldOrderEditor({
  fields,
  onChange,
  layout,
  size,
  fieldValues = {},
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

          return (
            <FieldToggle
              key={field.id}
              field={field}
              onToggle={handleToggle}
              disabled={!supported}
              disabledHint={unsupportedHint}
              warning={lengthCheck.isOverLimit ? lengthCheck.warning : undefined}
            />
          );
        })}
      </div>
    </div>
  );
}
