"use client";

/**
 * Селектор шаблона этикеток со статическими превью.
 *
 * Позволяет выбрать один из 3 шаблонов:
 * - Basic: вертикальный, DataMatrix слева, штрихкод WB справа внизу
 * - Professional: горизонтальный, два столбца с реквизитами организации
 * - Extended: с редактируемыми строками справа
 */

import { useState } from "react";
import Image from "next/image";
import { ZoomIn, X } from "lucide-react";
import type { LabelLayout, LabelSize } from "./label-canvas";

/**
 * Возвращает путь к картинке шаблона.
 * Для Basic — зависит от размера, для остальных — только 58x40.
 */
function getTemplateImagePath(layout: LabelLayout, size: LabelSize): string {
  if (layout === "basic") {
    const sizeNum = size.replace("x", ""); // "58x40" → "5840"
    return `/templates/basic${sizeNum}.webp`;
  }
  if (layout === "professional") {
    return "/templates/PRO5840.webp";
  }
  return "/templates/extended5840.webp";
}

interface LayoutOption {
  value: LabelLayout;
  title: string;
  description: string;
  badge?: string;
}

/**
 * Лимиты полей из Excel по шаблонам и размерам.
 * Формат: {layout: {size: count}}
 *
 * Basic/Professional: название в отдельной области + текстовый блок
 * Extended: всё в одном блоке
 */
const FIELD_LIMITS: Record<LabelLayout, Record<LabelSize, number>> = {
  basic: {
    "58x30": 4,  // название + 3 поля
    "58x40": 5,  // название + 4 поля
    "58x60": 5,  // название + 4 поля
  },
  professional: {
    "58x30": 11, // название + 10 полей (но 58x30 не поддерживается)
    "58x40": 11, // название + 10 полей
    "58x60": 11, // название + 10 полей (но 58x60 не поддерживается)
  },
  extended: {
    "58x30": 12, // все в одном блоке (но 58x30 не поддерживается)
    "58x40": 12, // все в одном блоке
    "58x60": 12, // все в одном блоке
  },
};

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
  {
    value: "extended",
    title: "Расширенный",
    description: "С редактируемыми строками справа",
    badge: "NEW",
  },
];

interface LayoutSelectorProps {
  value: LabelLayout;
  onChange: (layout: LabelLayout) => void;
  size?: LabelSize;
  disabled?: boolean;
  className?: string;
}

export function LayoutSelector({
  value,
  onChange,
  size = "58x40",
  disabled,
  className,
}: LayoutSelectorProps) {
  const [zoomedTemplate, setZoomedTemplate] = useState<{
    src: string;
    title: string;
  } | null>(null);

  return (
    <>
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
            const imageSrc = getTemplateImagePath(option.value, size);

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

                {/* Preview with zoom */}
                <div className="relative w-full max-w-[140px] mb-3 flex justify-center group/preview">
                  <Image
                    src={imageSrc}
                    alt={option.title}
                    width={140}
                    height={100}
                    className="rounded border border-warm-gray-200 object-contain"
                    priority
                  />
                  {/* Zoom overlay */}
                  <div
                    className="absolute inset-0 bg-black/40 rounded opacity-0 group-hover/preview:opacity-100
                               transition-opacity duration-200 flex items-center justify-center cursor-zoom-in"
                    onClick={(e) => {
                      e.stopPropagation();
                      setZoomedTemplate({ src: imageSrc, title: option.title });
                    }}
                  >
                    <ZoomIn className="w-6 h-6 text-white drop-shadow-lg" />
                  </div>
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

                {/* Field limit badge */}
                <div className="mt-2 px-2 py-0.5 bg-warm-gray-100 rounded-full">
                  <span className="text-[10px] text-warm-gray-600 font-medium">
                    до {FIELD_LIMITS[option.value][size]} полей
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-warm-gray-400 text-center">
          Превью может незначительно отличаться от итогового PDF
        </p>
      </div>

      {/* Zoom Modal */}
      {zoomedTemplate && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm
                     animate-in fade-in duration-200"
          onClick={() => setZoomedTemplate(null)}
        >
          <div
            className="relative bg-white rounded-2xl p-4 shadow-2xl max-w-[90vw] max-h-[90vh]
                       animate-in zoom-in-95 duration-300"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setZoomedTemplate(null)}
              className="absolute -top-3 -right-3 w-8 h-8 bg-white rounded-full shadow-lg
                         flex items-center justify-center hover:bg-gray-100 transition-colors"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>

            {/* Title */}
            <h4 className="text-lg font-semibold text-gray-800 mb-3 text-center">
              {zoomedTemplate.title}
            </h4>

            {/* Zoomed image */}
            <Image
              src={zoomedTemplate.src}
              alt={zoomedTemplate.title}
              width={500}
              height={400}
              className="rounded-lg border border-gray-200 object-contain"
              priority
            />
          </div>
        </div>
      )}
    </>
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
