"use client";

/**
 * Превью этикетки с выбранным шаблоном.
 *
 * Показывает как будет выглядеть этикетка с заданными параметрами.
 */

import { useMemo } from "react";

export type LabelLayout = "classic" | "centered" | "minimal";

export interface LabelPreviewData {
  barcode: string;
  article?: string;
  size?: string;
  color?: string;
  name?: string;
  organization: string;
}

interface LabelPreviewProps {
  data: LabelPreviewData;
  layout: LabelLayout;
  showArticle: boolean;
  showSizeColor: boolean;
  showName: boolean;
  className?: string;
}

export function LabelPreview({
  data,
  layout,
  showArticle,
  showSizeColor,
  showName,
  className,
}: LabelPreviewProps) {
  const sizeColor = useMemo(() => {
    const parts = [];
    if (data.color) parts.push(data.color);
    if (data.size) parts.push(data.size);
    return parts.join(" / ");
  }, [data.color, data.size]);

  // Classic шаблон: штрихкод сверху, текст слева
  if (layout === "classic") {
    return (
      <div
        className={`aspect-[58/40] bg-white border-2 border-warm-gray-200 rounded-lg p-3 flex flex-col shadow-sm ${className || ""}`}
      >
        {/* Barcode placeholder - centered */}
        <div className="w-full h-8 bg-warm-gray-100 mb-1 flex items-center justify-center">
          <div className="flex gap-[1px]">
            {[...Array(20)].map((_, i) => (
              <div
                key={i}
                className="w-[2px] bg-warm-gray-800"
                style={{ height: `${12 + (i % 3) * 4}px` }}
              />
            ))}
          </div>
        </div>
        <p className="text-[8px] text-warm-gray-600 mb-1 text-center">{data.barcode}</p>

        {/* Text - left aligned */}
        {showName && data.name && (
          <p className="text-[9px] font-medium text-warm-gray-800 truncate w-full text-left">
            {data.name}
          </p>
        )}
        {showArticle && data.article && (
          <p className="text-[8px] text-warm-gray-600 text-left">Арт: {data.article}</p>
        )}
        {showSizeColor && sizeColor && (
          <p className="text-[8px] text-warm-gray-600 text-left">{sizeColor}</p>
        )}

        <p className="text-[7px] text-warm-gray-500 mt-auto truncate w-full text-left">
          {data.organization}
        </p>
      </div>
    );
  }

  // Centered шаблон: штрихкод сверху, текст по центру
  if (layout === "centered") {
    return (
      <div
        className={`aspect-[58/40] bg-white border-2 border-warm-gray-200 rounded-lg p-3 flex flex-col items-center text-center shadow-sm ${className || ""}`}
      >
        {/* Barcode placeholder */}
        <div className="w-full h-8 bg-warm-gray-100 mb-1 flex items-center justify-center">
          <div className="flex gap-[1px]">
            {[...Array(20)].map((_, i) => (
              <div
                key={i}
                className="w-[2px] bg-warm-gray-800"
                style={{ height: `${12 + (i % 3) * 4}px` }}
              />
            ))}
          </div>
        </div>
        <p className="text-[8px] text-warm-gray-600 mb-1">{data.barcode}</p>

        {showName && data.name && (
          <p className="text-[9px] font-medium text-warm-gray-800 truncate w-full">
            {data.name}
          </p>
        )}
        {showArticle && data.article && (
          <p className="text-[8px] text-warm-gray-600">Арт: {data.article}</p>
        )}
        {showSizeColor && sizeColor && (
          <p className="text-[8px] text-warm-gray-600">{sizeColor}</p>
        )}

        <p className="text-[7px] text-warm-gray-500 mt-auto truncate w-full">
          {data.organization}
        </p>
      </div>
    );
  }

  // Minimal layout: только штрихкод + артикул
  return (
    <div
      className={`aspect-[58/40] bg-white border-2 border-warm-gray-200 rounded-lg p-3 flex flex-col items-center justify-center text-center shadow-sm ${className || ""}`}
    >
      {/* Barcode */}
      <div className="flex gap-[1px] mb-1">
        {[...Array(24)].map((_, i) => (
          <div
            key={i}
            className="w-[2px] bg-warm-gray-800"
            style={{ height: `${14 + (i % 3) * 3}px` }}
          />
        ))}
      </div>
      <p className="text-[9px] text-warm-gray-600 mb-1">{data.barcode}</p>

      {showArticle && data.article && (
        <p className="text-[10px] font-medium text-warm-gray-800">
          {data.article}
        </p>
      )}
    </div>
  );
}
