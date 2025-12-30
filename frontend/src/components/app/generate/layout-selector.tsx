"use client";

/**
 * Селектор шаблона этикеток с превью.
 *
 * Позволяет выбрать один из 2 шаблонов:
 * - Basic: вертикальный, DataMatrix слева, штрихкод WB справа внизу
 * - Professional: горизонтальный, два столбца с реквизитами организации
 */

import { LabelLayout, LabelPreview, LabelPreviewData } from "./label-preview";

interface LayoutOption {
  value: LabelLayout;
  title: string;
  description: string;
  badge?: string;
}

const LAYOUT_OPTIONS: LayoutOption[] = [
  {
    value: "basic",
    title: "Базовый",
    description: "Вертикальный, DataMatrix слева",
  },
  {
    value: "professional",
    title: "Профессиональный",
    description: "Горизонтальный, реквизиты организации",
    badge: "PRO",
  },
];

interface LayoutSelectorProps {
  value: LabelLayout;
  onChange: (layout: LabelLayout) => void;
  previewData: LabelPreviewData;
  showArticle: boolean;
  showSizeColor: boolean;
  showName: boolean;
  disabled?: boolean;
  className?: string;
}

export function LayoutSelector({
  value,
  onChange,
  previewData,
  showArticle,
  showSizeColor,
  showName,
  disabled,
  className,
}: LayoutSelectorProps) {
  return (
    <div className={`space-y-4 ${className || ""}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-warm-gray-800">
          Выберите шаблон
        </h3>
        <span className="text-sm text-warm-gray-500">
          Внешний вид этикетки
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {LAYOUT_OPTIONS.map((option) => {
          const isSelected = value === option.value;

          return (
            <button
              key={option.value}
              type="button"
              disabled={disabled}
              onClick={() => onChange(option.value)}
              className={`
                relative p-4 rounded-xl border-2 transition-all duration-200
                flex flex-col items-center text-center
                ${
                  isSelected
                    ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-500/20"
                    : "border-warm-gray-200 bg-white hover:border-emerald-300 hover:bg-emerald-50/30"
                }
                ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
              `}
            >
              {/* Badge (PRO) */}
              {option.badge && (
                <div className="absolute top-2 left-2 px-1.5 py-0.5 bg-amber-100 text-amber-700 text-[10px] font-bold rounded">
                  {option.badge}
                </div>
              )}

              {/* Selected indicator */}
              {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center">
                  <svg
                    className="w-3 h-3 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              )}

              {/* Preview */}
              <div className="w-full max-w-[140px] mb-3">
                <LabelPreview
                  data={previewData}
                  layout={option.value}
                  showArticle={showArticle}
                  showSizeColor={showSizeColor}
                  showName={showName}
                />
              </div>

              {/* Title */}
              <p
                className={`font-medium mb-1 ${
                  isSelected ? "text-emerald-700" : "text-warm-gray-800"
                }`}
              >
                {option.title}
              </p>

              {/* Description */}
              <p className="text-xs text-warm-gray-500">{option.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Компактный селектор для мобильных устройств (dropdown).
 */
interface LayoutDropdownProps {
  value: LabelLayout;
  onChange: (layout: LabelLayout) => void;
  disabled?: boolean;
  className?: string;
}

export function LayoutDropdown({
  value,
  onChange,
  disabled,
  className,
}: LayoutDropdownProps) {
  const selectedOption = LAYOUT_OPTIONS.find((o) => o.value === value);

  return (
    <div className={className}>
      <label className="block text-sm font-medium text-warm-gray-700 mb-1">
        Шаблон этикетки
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as LabelLayout)}
        disabled={disabled}
        className={`
          w-full px-4 py-2.5 rounded-xl border border-warm-gray-300
          bg-white text-warm-gray-800
          focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
          ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
        `}
      >
        {LAYOUT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.title} — {option.description}
          </option>
        ))}
      </select>
      {selectedOption && (
        <p className="mt-1 text-xs text-warm-gray-500">
          {selectedOption.description}
        </p>
      )}
    </div>
  );
}
