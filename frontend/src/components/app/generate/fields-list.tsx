"use client";

import { useCallback, useMemo } from "react";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { FieldRowWithError, SizeColorFieldRowWithError } from "./field-row";
import {
  getFieldLimit,
  getFieldsExcludedFromLimit,
  getAllFieldsForDisplay,
  getFieldLabel,
  getLayoutDisplayName,
  isCustomField,
  isSizeColorField,
  isFieldSupported,
  getUnsupportedFieldHint,
  checkFieldLength,
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
  /** Значение поля (для обычных полей) */
  value: string;
  /** Включено ли поле (чекбокс) */
  checked: boolean;
  /** Является ли поле кастомным (редактируемый label) */
  isCustom?: boolean;
  /** Для size_color поля: значение размера */
  sizeValue?: string;
  /** Для size_color поля: значение цвета */
  colorValue?: string;
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

  // Получаем поля, исключённые из лимита (например, ИНН для Basic — он вверху)
  const excludedFromLimit = useMemo(
    () => getFieldsExcludedFromLimit(layout, template),
    [layout, template]
  );

  // Получаем список ВСЕХ полей для отображения (13 стандартных + кастомные для Extended)
  const allFieldIds = useMemo(
    () => getAllFieldsForDisplay(layout),
    [layout]
  );

  // Показываем ВСЕ поля (недоступные — серые)
  const visibleFields = useMemo(() => {
    return allFieldIds.map((fieldId) => {
      const existingField = fields.find((f) => f.id === fieldId);
      return existingField || {
        id: fieldId,
        label: getFieldLabel(fieldId),
        value: "",
        checked: false,
        isCustom: isCustomField(fieldId),
      };
    });
  }, [fields, allFieldIds]);

  // Считаем количество активных (checked) полей БЕЗ исключённых из лимита
  // Для Basic: ИНН не считается (он вверху этикетки, не в текстовом блоке)
  const activeCount = useMemo(
    () =>
      visibleFields.filter(
        (f) => f.checked && !excludedFromLimit.includes(f.id as FieldId)
      ).length,
    [visibleFields, excludedFromLimit]
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

  // Обработчик изменения размера (для size_color)
  const handleSizeChange = useCallback(
    (fieldId: string, newSize: string) => {
      const updatedFields = fields.map((field) => {
        if (field.id === fieldId) {
          return { ...field, sizeValue: newSize };
        }
        return field;
      });
      onFieldsChange(updatedFields);
    },
    [fields, onFieldsChange]
  );

  // Обработчик изменения цвета (для size_color)
  const handleColorChange = useCallback(
    (fieldId: string, newColor: string) => {
      const updatedFields = fields.map((field) => {
        if (field.id === fieldId) {
          return { ...field, colorValue: newColor };
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
      const fieldId = field.id as FieldId;

      // Проверяем, поддерживается ли поле шаблоном
      const supported = isFieldSupported(fieldId, layout, template);
      if (!supported) {
        return getUnsupportedFieldHint(fieldId, layout, template) ||
          `Поле недоступно для ${templateLabel}`;
      }

      // Если достигнут лимит — показываем hint для невыбранных
      if (!field.checked && isAtLimit) {
        return `Лимит для ${templateLabel}. Снимите галочку с другого поля или выберите Extended.`;
      }
      return undefined;
    },
    [isAtLimit, templateLabel, layout, template]
  );

  // Проверяем, должно ли поле быть заблокировано
  const isFieldDisabled = useCallback(
    (field: Field): boolean => {
      const fieldId = field.id as FieldId;

      // Если поле НЕ поддерживается шаблоном — всегда disabled
      const supported = isFieldSupported(fieldId, layout, template);
      if (!supported) return true;

      // Если поле уже выбрано — не блокируем (чтобы можно было снять)
      if (field.checked) return false;

      // Если достигнут лимит — блокируем невыбранные поля
      return isAtLimit;
    },
    [isAtLimit, layout, template]
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
          const isSizeColor = isSizeColorField(fieldId);
          const disabled = isFieldDisabled(field);
          const error = errors.get(field.id);
          const disabledHint = getDisabledHint(field);

          // Для size_color проверяем суммарную длину size + color
          const valueToCheck = isSizeColor
            ? `${field.sizeValue || ""}, ${field.colorValue || ""}`
            : field.value;
          const lengthCheck = checkFieldLength(fieldId, valueToCheck, layout, template);
          const warning = lengthCheck.isOverLimit ? lengthCheck.warning : undefined;

          // Для size_color используем специальный компонент
          if (isSizeColor) {
            return (
              <SizeColorFieldRowWithError
                key={field.id}
                id={field.id}
                checked={field.checked}
                disabled={disabled}
                sizeValue={field.sizeValue || ""}
                colorValue={field.colorValue || ""}
                error={error}
                warning={warning}
                disabledHint={disabledHint}
                onToggle={() => handleToggle(field.id)}
                onSizeChange={(newSize) => handleSizeChange(field.id, newSize)}
                onColorChange={(newColor) => handleColorChange(field.id, newColor)}
              />
            );
          }

          return (
            <FieldRowWithError
              key={field.id}
              id={field.id}
              label={field.label || getFieldLabel(fieldId)}
              value={field.value}
              checked={field.checked}
              disabled={disabled}
              error={error}
              warning={warning}
              isCustom={isCustom}
              disabledHint={disabledHint}
              onToggle={() => handleToggle(field.id)}
              onLabelChange={(newLabel) => handleLabelChange(field.id, newLabel)}
              onValueChange={(newValue) => handleValueChange(field.id, newValue)}
            />
          );
        })}
      </div>

      {/* Подсказка про редактирование */}
      <div className="flex items-start gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
        <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
        <span>
          Дважды кликните на значение поля, чтобы отредактировать.
          {layout === "extended" && " Кастомные строки позволяют добавить любую информацию — дважды кликните на название, чтобы переименовать."}
        </span>
      </div>
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
 * Создаёт массив полей с дефолтными значениями на основе layout.
 * Все 13 полей + кастомные для Extended.
 */
export function createInitialFields(
  layout: LabelLayout,
  _template: LabelSize,
  initialValues?: Partial<Record<FieldId, { value: string; checked: boolean }>>
): Field[] {
  const allFieldIds = getAllFieldsForDisplay(layout);

  return allFieldIds.map((fieldId) => {
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
 * Снимает checked с неподдерживаемых полей.
 */
export function updateFieldsForTemplate(
  currentFields: Field[],
  newLayout: LabelLayout,
  newTemplate: LabelSize
): Field[] {
  const allFieldIds = getAllFieldsForDisplay(newLayout);
  const maxFields = getFieldLimit(newLayout, newTemplate);

  // Создаём map текущих значений
  const currentValuesMap = new Map(
    currentFields.map((f) => [f.id, { value: f.value, checked: f.checked, label: f.label }])
  );

  // Создаём новые поля, сохраняя существующие значения
  const newFields = allFieldIds.map((fieldId) => {
    const current = currentValuesMap.get(fieldId);
    const isCustom = isCustomField(fieldId);

    // Проверяем, поддерживается ли поле новым шаблоном
    const supported = isFieldSupported(fieldId, newLayout, newTemplate);

    return {
      id: fieldId,
      label: current?.label || getFieldLabel(fieldId),
      value: current?.value ?? "",
      // Снимаем checked если поле не поддерживается
      checked: supported ? (current?.checked ?? false) : false,
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
