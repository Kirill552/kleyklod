"use client";

import { useCallback, useMemo } from "react";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { FieldRowWithError } from "./field-row";
import {
  getFieldLimit,
  getAvailableFields,
  getFieldLabel,
  getLayoutDisplayName,
  isCustomField,
  type FieldId,
} from "@/lib/label-field-config";
import type { LabelLayout, LabelSize } from "@/lib/api";

/**
 * Структура поля для FieldsList.
 */
export interface Field {
  /** Уникальный идентификатор поля */
  id: string;
  /** Название поля (для кастомных полей — редактируемое) */
  label: string;
  /** Значение поля */
  value: string;
  /** Включено ли поле (чекбокс) */
  checked: boolean;
  /** Является ли поле кастомным (редактируемый label) */
  isCustom?: boolean;
}

/**
 * Props для компонента FieldsList.
 */
export interface FieldsListProps {
  /** Массив полей */
  fields: Field[];
  /** Текущий layout этикетки */
  layout: LabelLayout;
  /** Текущий размер этикетки */
  template: LabelSize;
  /** Map ошибок: field_id -> error message */
  errors: Map<string, string>;
  /** Callback при изменении полей */
  onFieldsChange: (fields: Field[]) => void;
}

/**
 * FieldsList — компонент для отображения и редактирования полей этикетки.
 *
 * Особенности:
 * - Динамическая блокировка полей при достижении лимита
 * - Показ доступных полей в зависимости от layout/template
 * - Подсказки при блокировке
 * - Кастомные поля (только для Extended)
 * - Валидация с отображением ошибок
 */
export function FieldsList({
  fields,
  layout,
  template,
  errors,
  onFieldsChange,
}: FieldsListProps) {
  // Получаем лимит полей для текущего шаблона
  const maxFields = useMemo(
    () => getFieldLimit(layout, template),
    [layout, template]
  );

  // Получаем список доступных полей для текущего шаблона
  const availableFieldIds = useMemo(
    () => getAvailableFields(layout, template),
    [layout, template]
  );

  // Фильтруем только доступные поля
  const visibleFields = useMemo(() => {
    return fields.filter((field) =>
      availableFieldIds.includes(field.id as FieldId)
    );
  }, [fields, availableFieldIds]);

  // Считаем количество активных (checked) полей
  const activeCount = useMemo(
    () => visibleFields.filter((f) => f.checked).length,
    [visibleFields]
  );

  // Проверяем, достигнут ли лимит
  const isAtLimit = activeCount >= maxFields;

  // Название шаблона для подсказок
  const layoutName = getLayoutDisplayName(layout);
  const templateLabel = `${layoutName} ${template}`;

  // Обработчик переключения чекбокса
  const handleToggle = useCallback(
    (fieldId: string) => {
      const updatedFields = fields.map((field) => {
        if (field.id === fieldId) {
          return { ...field, checked: !field.checked };
        }
        return field;
      });
      onFieldsChange(updatedFields);
    },
    [fields, onFieldsChange]
  );

  // Обработчик изменения label (только для кастомных полей)
  const handleLabelChange = useCallback(
    (fieldId: string, newLabel: string) => {
      const updatedFields = fields.map((field) => {
        if (field.id === fieldId && field.isCustom) {
          return { ...field, label: newLabel };
        }
        return field;
      });
      onFieldsChange(updatedFields);
    },
    [fields, onFieldsChange]
  );

  // Обработчик изменения значения
  const handleValueChange = useCallback(
    (fieldId: string, newValue: string) => {
      const updatedFields = fields.map((field) => {
        if (field.id === fieldId) {
          return { ...field, value: newValue };
        }
        return field;
      });
      onFieldsChange(updatedFields);
    },
    [fields, onFieldsChange]
  );

  // Подсказка для заблокированных полей
  const getDisabledHint = useCallback(
    (field: Field): string | undefined => {
      if (!field.checked && isAtLimit) {
        return `Лимит для ${templateLabel}. Снимите галочку с другого поля или выберите Extended.`;
      }
      return undefined;
    },
    [isAtLimit, templateLabel]
  );

  // Проверяем, должно ли поле быть заблокировано
  const isFieldDisabled = useCallback(
    (field: Field): boolean => {
      // Если поле уже выбрано — не блокируем (чтобы можно было снять)
      if (field.checked) return false;
      // Если достигнут лимит — блокируем невыбранные поля
      return isAtLimit;
    },
    [isAtLimit]
  );

  // Если нет доступных полей — показываем заглушку
  if (visibleFields.length === 0) {
    return (
      <div className="text-center py-8 text-warm-gray-500">
        Нет доступных полей для этого шаблона
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Заголовок с информацией о лимите */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2 text-sm text-warm-gray-600">
          <span className="font-medium">{templateLabel}</span>
          <span className="text-warm-gray-400">—</span>
          <span>
            максимум{" "}
            <span className="font-semibold text-warm-gray-700">
              {maxFields}
            </span>{" "}
            {getFieldsWord(maxFields)}
          </span>
        </div>
        <div
          className={cn(
            "text-sm font-medium px-2 py-0.5 rounded-full",
            isAtLimit
              ? "bg-amber-100 text-amber-700"
              : "bg-emerald-100 text-emerald-700"
          )}
        >
          {activeCount}/{maxFields}
        </div>
      </div>

      {/* Подсказка о лимите */}
      {isAtLimit && (
        <div className="flex items-start gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
          <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>
            Достигнут лимит полей для {templateLabel}. Снимите галочку с
            ненужного поля, чтобы добавить другое.
          </span>
        </div>
      )}

      {/* Разделитель */}
      <div className="border-t border-warm-gray-200" />

      {/* Список полей */}
      <div className="space-y-2">
        {visibleFields.map((field) => {
          const fieldId = field.id as FieldId;
          const isCustom = isCustomField(fieldId);
          const disabled = isFieldDisabled(field);
          const error = errors.get(field.id);
          const disabledHint = getDisabledHint(field);

          return (
            <FieldRowWithError
              key={field.id}
              id={field.id}
              label={field.label || getFieldLabel(fieldId)}
              value={field.value}
              checked={field.checked}
              disabled={disabled}
              error={error}
              isCustom={isCustom}
              disabledHint={disabledHint}
              onToggle={() => handleToggle(field.id)}
              onLabelChange={(newLabel) => handleLabelChange(field.id, newLabel)}
              onValueChange={(newValue) => handleValueChange(field.id, newValue)}
            />
          );
        })}
      </div>

      {/* Подсказка про кастомные поля для Extended */}
      {layout === "extended" && (
        <div className="flex items-start gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
          <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>
            Кастомные строки (Строка 1, 2, 3) позволяют добавить любую
            информацию. Дважды кликните на название, чтобы переименовать.
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * Склонение слова "поле" в зависимости от числа.
 */
function getFieldsWord(count: number): string {
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;

  if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
    return "полей";
  }

  if (lastDigit === 1) {
    return "поле";
  }

  if (lastDigit >= 2 && lastDigit <= 4) {
    return "поля";
  }

  return "полей";
}

/**
 * Хелпер для создания начального состояния полей.
 * Создаёт массив полей с дефолтными значениями на основе layout/template.
 */
export function createInitialFields(
  layout: LabelLayout,
  template: LabelSize,
  initialValues?: Partial<Record<FieldId, { value: string; checked: boolean }>>
): Field[] {
  const availableFieldIds = getAvailableFields(layout, template);

  return availableFieldIds.map((fieldId) => {
    const initial = initialValues?.[fieldId];
    const isCustom = isCustomField(fieldId);

    return {
      id: fieldId,
      label: getFieldLabel(fieldId),
      value: initial?.value ?? "",
      checked: initial?.checked ?? false,
      isCustom,
    };
  });
}

/**
 * Хелпер для обновления полей при смене layout/template.
 * Сохраняет значения существующих полей.
 */
export function updateFieldsForTemplate(
  currentFields: Field[],
  newLayout: LabelLayout,
  newTemplate: LabelSize
): Field[] {
  const availableFieldIds = getAvailableFields(newLayout, newTemplate);
  const maxFields = getFieldLimit(newLayout, newTemplate);

  // Создаём map текущих значений
  const currentValuesMap = new Map(
    currentFields.map((f) => [f.id, { value: f.value, checked: f.checked, label: f.label }])
  );

  // Создаём новые поля, сохраняя существующие значения
  const newFields = availableFieldIds.map((fieldId) => {
    const current = currentValuesMap.get(fieldId);
    const isCustom = isCustomField(fieldId);

    return {
      id: fieldId,
      label: current?.label || getFieldLabel(fieldId),
      value: current?.value ?? "",
      checked: current?.checked ?? false,
      isCustom,
    };
  });

  // Проверяем лимит — если активных полей больше лимита, снимаем лишние
  let activeCount = newFields.filter((f) => f.checked).length;

  if (activeCount > maxFields) {
    // Снимаем галочки с конца списка
    for (let i = newFields.length - 1; i >= 0 && activeCount > maxFields; i--) {
      if (newFields[i].checked) {
        newFields[i].checked = false;
        activeCount--;
      }
    }
  }

  return newFields;
}

export default FieldsList;
