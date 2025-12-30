"use client";

/**
 * Превью этикетки с выбранным шаблоном.
 *
 * Показывает как будет выглядеть этикетка с заданными параметрами.
 *
 * Шаблоны:
 * - Basic: вертикальный, DataMatrix слева, штрихкод WB справа внизу
 * - Professional: горизонтальный, два столбца с реквизитами организации
 */

import { useMemo } from "react";

export type LabelLayout = "basic" | "professional";

export interface LabelPreviewData {
  barcode: string;
  article?: string;
  size?: string;
  color?: string;
  name?: string;
  organization?: string;
  // Дополнительные поля для профессионального шаблона
  country?: string;
  composition?: string;
  inn?: string;
  address?: string;
  certificate?: string;
  productionDate?: string;
  importer?: string;
  manufacturer?: string;
  brand?: string;
}

interface LabelPreviewProps {
  data: LabelPreviewData;
  layout: LabelLayout;
  showArticle: boolean;
  showSizeColor: boolean;
  showName: boolean;
  showOrganization?: boolean;
  showCountry?: boolean;
  showComposition?: boolean;
  // Флаги для профессионального шаблона
  showInn?: boolean;
  showAddress?: boolean;
  showCertificate?: boolean;
  showProductionDate?: boolean;
  showImporter?: boolean;
  showManufacturer?: boolean;
  showBrand?: boolean;
  className?: string;
}

/**
 * DataMatrix placeholder (SVG квадрат с точками).
 */
function DataMatrixPlaceholder({ size = 40 }: { size?: number }) {
  return (
    <div
      className="bg-white border border-warm-gray-300 flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size * 0.8} height={size * 0.8} viewBox="0 0 24 24">
        {/* Имитация DataMatrix паттерна */}
        <rect x="0" y="0" width="24" height="24" fill="white" />
        {[...Array(6)].map((_, row) =>
          [...Array(6)].map((_, col) => {
            const fill = (row + col) % 2 === 0 ? "#1f2937" : "white";
            return (
              <rect
                key={`${row}-${col}`}
                x={col * 4}
                y={row * 4}
                width="4"
                height="4"
                fill={fill}
              />
            );
          })
        )}
      </svg>
    </div>
  );
}

/**
 * Barcode placeholder (вертикальные линии).
 */
function BarcodePlaceholder({
  width = 60,
  height = 24,
}: {
  width?: number;
  height?: number;
}) {
  return (
    <div
      className="bg-white flex items-end justify-center gap-[1px]"
      style={{ width, height }}
    >
      {[...Array(Math.floor(width / 3))].map((_, i) => (
        <div
          key={i}
          className="bg-warm-gray-800"
          style={{
            width: 2,
            height: `${50 + (i % 3) * 15}%`,
          }}
        />
      ))}
    </div>
  );
}

export function LabelPreview({
  data,
  layout,
  showArticle,
  showSizeColor,
  showName,
  showOrganization = true,
  showCountry = false,
  showComposition = false,
  showInn = false,
  showAddress = false,
  showCertificate = false,
  showProductionDate = false,
  showImporter = false,
  showManufacturer = false,
  showBrand = false,
  className,
}: LabelPreviewProps) {
  const sizeColor = useMemo(() => {
    const parts = [];
    if (data.color) parts.push(data.color);
    if (data.size) parts.push(data.size);
    return parts.join(" / ");
  }, [data.color, data.size]);

  // Basic шаблон: вертикальный, DataMatrix слева, штрихкод WB справа внизу
  if (layout === "basic") {
    return (
      <div
        className={`aspect-[58/40] bg-white border-2 border-warm-gray-200 rounded-lg p-2 flex shadow-sm ${className || ""}`}
      >
        {/* Левая колонка: DataMatrix */}
        <div className="flex flex-col items-center justify-center mr-2">
          <DataMatrixPlaceholder size={36} />
          <p className="text-[5px] text-warm-gray-400 mt-0.5">ЧЗ</p>
        </div>

        {/* Правая колонка: информация + штрихкод WB */}
        <div className="flex-1 flex flex-col justify-between min-w-0">
          {/* Верхняя часть: информация о товаре */}
          <div className="space-y-0.5 overflow-hidden">
            {showName && data.name && (
              <p className="text-[8px] font-medium text-warm-gray-800 truncate">
                {data.name}
              </p>
            )}
            {showOrganization && data.organization && (
              <p className="text-[6px] text-warm-gray-500 truncate">
                {data.organization}
              </p>
            )}
            {showArticle && data.article && (
              <p className="text-[6px] text-warm-gray-600 truncate">
                Арт: {data.article}
              </p>
            )}
            {showSizeColor && sizeColor && (
              <p className="text-[6px] text-warm-gray-600 truncate">
                {sizeColor}
              </p>
            )}
            {showCountry && data.country && (
              <p className="text-[5px] text-warm-gray-500 truncate">
                {data.country}
              </p>
            )}
            {showComposition && data.composition && (
              <p className="text-[5px] text-warm-gray-500 truncate">
                {data.composition}
              </p>
            )}
          </div>

          {/* Нижняя часть: штрихкод WB */}
          <div className="flex flex-col items-end mt-1">
            <BarcodePlaceholder width={45} height={16} />
            <p className="text-[5px] text-warm-gray-400 mt-0.5">
              {data.barcode}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Professional шаблон: горизонтальный, два столбца с реквизитами
  return (
    <div
      className={`aspect-[58/40] bg-white border-2 border-warm-gray-200 rounded-lg p-1.5 flex flex-col shadow-sm ${className || ""}`}
    >
      {/* Верхняя часть: две колонки */}
      <div className="flex flex-1 gap-1 min-h-0">
        {/* Левая колонка: DataMatrix + основная информация */}
        <div className="flex-1 flex flex-col items-center">
          <DataMatrixPlaceholder size={28} />
          <div className="mt-0.5 w-full text-center space-y-0">
            {showBrand && data.brand && (
              <p className="text-[5px] font-medium text-warm-gray-700 truncate">
                {data.brand}
              </p>
            )}
            {showImporter && data.importer && (
              <p className="text-[4px] text-warm-gray-500 truncate">
                Имп: {data.importer}
              </p>
            )}
            {showManufacturer && data.manufacturer && (
              <p className="text-[4px] text-warm-gray-500 truncate">
                Изг: {data.manufacturer}
              </p>
            )}
          </div>
        </div>

        {/* Правая колонка: реквизиты организации */}
        <div className="flex-1 flex flex-col text-left space-y-0 overflow-hidden">
          {showOrganization && data.organization && (
            <p className="text-[5px] font-medium text-warm-gray-700 truncate">
              {data.organization}
            </p>
          )}
          {showInn && data.inn && (
            <p className="text-[4px] text-warm-gray-500 truncate">
              ИНН: {data.inn}
            </p>
          )}
          {showAddress && data.address && (
            <p className="text-[4px] text-warm-gray-500 truncate">
              {data.address}
            </p>
          )}
          {showCountry && data.country && (
            <p className="text-[4px] text-warm-gray-500 truncate">
              {data.country}
            </p>
          )}
          {showCertificate && data.certificate && (
            <p className="text-[4px] text-warm-gray-500 truncate">
              Серт: {data.certificate}
            </p>
          )}
          {showProductionDate && data.productionDate && (
            <p className="text-[4px] text-warm-gray-500 truncate">
              Дата: {data.productionDate}
            </p>
          )}
          {showName && data.name && (
            <p className="text-[5px] text-warm-gray-600 truncate mt-auto">
              {data.name}
            </p>
          )}
        </div>
      </div>

      {/* Нижняя часть: штрихкод WB по центру */}
      <div className="flex flex-col items-center mt-1 pt-0.5 border-t border-warm-gray-100">
        <BarcodePlaceholder width={50} height={12} />
        <p className="text-[5px] text-warm-gray-400">{data.barcode}</p>
      </div>
    </div>
  );
}
