"use client";

/**
 * Переключатели полей этикетки.
 *
 * Позволяет включить/выключить отображение:
 * - Артикул
 * - Размер/Цвет
 * - Название товара
 */

import { Check } from "lucide-react";

interface ShowFieldsToggleProps {
  showArticle: boolean;
  showSizeColor: boolean;
  showName: boolean;
  onShowArticleChange: (value: boolean) => void;
  onShowSizeColorChange: (value: boolean) => void;
  onShowNameChange: (value: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function ShowFieldsToggle({
  showArticle,
  showSizeColor,
  showName,
  onShowArticleChange,
  onShowSizeColorChange,
  onShowNameChange,
  disabled,
  className,
}: ShowFieldsToggleProps) {
  const fields = [
    {
      id: "article",
      label: "Артикул",
      description: "Арт: 12345",
      checked: showArticle,
      onChange: onShowArticleChange,
    },
    {
      id: "size_color",
      label: "Размер / Цвет",
      description: "Белый / 42",
      checked: showSizeColor,
      onChange: onShowSizeColorChange,
    },
    {
      id: "name",
      label: "Название товара",
      description: "Футболка мужская...",
      checked: showName,
      onChange: onShowNameChange,
    },
  ];

  return (
    <div className={`space-y-3 ${className || ""}`}>
      <h3 className="text-sm font-medium text-warm-gray-700">
        Какие поля показывать
      </h3>

      <div className="space-y-2">
        {fields.map((field) => (
          <label
            key={field.id}
            className={`
              flex items-center gap-3 p-3 rounded-xl border transition-all
              ${
                field.checked
                  ? "border-emerald-200 bg-emerald-50"
                  : "border-warm-gray-200 bg-white"
              }
              ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:border-emerald-300"}
            `}
          >
            {/* Checkbox */}
            <div
              className={`
                w-5 h-5 rounded flex items-center justify-center flex-shrink-0
                transition-colors
                ${
                  field.checked
                    ? "bg-emerald-500"
                    : "bg-white border-2 border-warm-gray-300"
                }
              `}
            >
              {field.checked && <Check className="w-3.5 h-3.5 text-white" />}
            </div>

            {/* Hidden actual checkbox for accessibility */}
            <input
              type="checkbox"
              checked={field.checked}
              onChange={(e) => field.onChange(e.target.checked)}
              disabled={disabled}
              className="sr-only"
            />

            {/* Label */}
            <div className="flex-1 min-w-0">
              <p
                className={`font-medium ${
                  field.checked ? "text-emerald-700" : "text-warm-gray-700"
                }`}
              >
                {field.label}
              </p>
              <p className="text-xs text-warm-gray-500 truncate">
                {field.description}
              </p>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
}

/**
 * Компактная версия для использования в одну строку.
 */
interface CompactFieldsToggleProps {
  showArticle: boolean;
  showSizeColor: boolean;
  showName: boolean;
  onShowArticleChange: (value: boolean) => void;
  onShowSizeColorChange: (value: boolean) => void;
  onShowNameChange: (value: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function CompactFieldsToggle({
  showArticle,
  showSizeColor,
  showName,
  onShowArticleChange,
  onShowSizeColorChange,
  onShowNameChange,
  disabled,
  className,
}: CompactFieldsToggleProps) {
  const fields = [
    { id: "article", label: "Артикул", checked: showArticle, onChange: onShowArticleChange },
    { id: "size_color", label: "Размер/Цвет", checked: showSizeColor, onChange: onShowSizeColorChange },
    { id: "name", label: "Название", checked: showName, onChange: onShowNameChange },
  ];

  return (
    <div className={`flex flex-wrap gap-2 ${className || ""}`}>
      {fields.map((field) => (
        <button
          key={field.id}
          type="button"
          disabled={disabled}
          onClick={() => field.onChange(!field.checked)}
          className={`
            px-3 py-1.5 rounded-full text-sm font-medium
            transition-all flex items-center gap-1.5
            ${
              field.checked
                ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
                : "bg-warm-gray-100 text-warm-gray-600 border border-warm-gray-200"
            }
            ${disabled ? "opacity-50 cursor-not-allowed" : "hover:opacity-80"}
          `}
        >
          <span
            className={`w-3 h-3 rounded-sm flex items-center justify-center
              ${field.checked ? "bg-emerald-500" : "bg-warm-gray-300"}
            `}
          >
            {field.checked && <Check className="w-2 h-2 text-white" />}
          </span>
          {field.label}
        </button>
      ))}
    </div>
  );
}
