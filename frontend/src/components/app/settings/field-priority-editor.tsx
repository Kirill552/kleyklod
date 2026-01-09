"use client";

/**
 * Редактор приоритета полей для этикеток.
 *
 * Позволяет пользователям PRO/Enterprise настраивать порядок полей
 * на этикетке с помощью drag-n-drop.
 */

import { useState, useCallback } from "react";
import { GripVertical, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

// Дефолтный порядок полей (соответствует DEFAULT_FIELD_PRIORITY в backend)
const DEFAULT_FIELD_PRIORITY = [
  "name",
  "article",
  "size",
  "color",
  "brand",
  "composition",
  "country",
  "manufacturer",
  "importer",
  "production_date",
  "certificate",
];

// Человекочитаемые названия полей
const FIELD_LABELS: Record<string, string> = {
  name: "Название товара",
  article: "Артикул",
  size: "Размер",
  color: "Цвет",
  brand: "Бренд",
  composition: "Состав",
  country: "Страна",
  manufacturer: "Производитель",
  importer: "Импортёр",
  production_date: "Дата производства",
  certificate: "Сертификат",
};

interface FieldPriorityEditorProps {
  value: string[] | null;
  onChange: (priority: string[]) => void;
  disabled?: boolean;
}

export function FieldPriorityEditor({
  value,
  onChange,
  disabled = false,
}: FieldPriorityEditorProps) {
  // Используем value или дефолт
  const fields = value && value.length > 0 ? value : DEFAULT_FIELD_PRIORITY;

  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  const handleDragStart = useCallback(
    (e: React.DragEvent, index: number) => {
      if (disabled) return;
      setDraggedIndex(index);
      e.dataTransfer.effectAllowed = "move";
      // Устанавливаем данные для совместимости
      e.dataTransfer.setData("text/plain", index.toString());
    },
    [disabled]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent, index: number) => {
      if (disabled) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setDragOverIndex(index);
    },
    [disabled]
  );

  const handleDragLeave = useCallback(() => {
    setDragOverIndex(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent, dropIndex: number) => {
      if (disabled) return;
      e.preventDefault();

      if (draggedIndex === null || draggedIndex === dropIndex) {
        setDraggedIndex(null);
        setDragOverIndex(null);
        return;
      }

      // Перемещаем элемент
      const newFields = [...fields];
      const [removed] = newFields.splice(draggedIndex, 1);
      newFields.splice(dropIndex, 0, removed);

      onChange(newFields);
      setDraggedIndex(null);
      setDragOverIndex(null);
    },
    [disabled, draggedIndex, fields, onChange]
  );

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  }, []);

  const handleReset = useCallback(() => {
    onChange(DEFAULT_FIELD_PRIORITY);
  }, [onChange]);

  // Проверяем, отличается ли от дефолта
  const isModified =
    value !== null &&
    value.length > 0 &&
    JSON.stringify(value) !== JSON.stringify(DEFAULT_FIELD_PRIORITY);

  return (
    <div className="space-y-3">
      {/* Заголовок с кнопкой сброса */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-warm-gray-500">
          Перетащите поля для изменения порядка
        </p>
        {isModified && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleReset}
            disabled={disabled}
            className="text-warm-gray-500 hover:text-warm-gray-700 h-7 px-2"
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Сбросить
          </Button>
        )}
      </div>

      {/* Список полей */}
      <div className="space-y-1">
        {fields.map((field, index) => (
          <div
            key={field}
            draggable={!disabled}
            onDragStart={(e) => handleDragStart(e, index)}
            onDragOver={(e) => handleDragOver(e, index)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, index)}
            onDragEnd={handleDragEnd}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg border
              transition-all duration-150
              ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-grab active:cursor-grabbing"}
              ${
                draggedIndex === index
                  ? "opacity-50 border-emerald-400 bg-emerald-50"
                  : dragOverIndex === index
                    ? "border-emerald-500 bg-emerald-50 shadow-sm"
                    : "border-warm-gray-200 bg-white hover:border-warm-gray-300"
              }
            `}
          >
            {/* Иконка перетаскивания */}
            <GripVertical
              className={`w-4 h-4 flex-shrink-0 ${
                disabled ? "text-warm-gray-300" : "text-warm-gray-400"
              }`}
            />

            {/* Номер */}
            <span className="w-5 text-xs font-medium text-warm-gray-400">
              {index + 1}.
            </span>

            {/* Название поля */}
            <span className="flex-1 text-sm text-warm-gray-700">
              {FIELD_LABELS[field] || field}
            </span>
          </div>
        ))}
      </div>

      {/* Подсказка */}
      <p className="text-xs text-warm-gray-400">
        Поля выше в списке имеют больший приоритет при обрезке
      </p>
    </div>
  );
}
