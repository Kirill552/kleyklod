"use client";

/**
 * Превью этикетки с выбранным layout.
 *
 * Показывает как будет выглядеть этикетка с заданными параметрами.
 */

import { useMemo } from "react";

export type LabelLayout = "classic" | "compact" | "minimal";

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
  const barcodeDisplay = useMemo(() => {
    // Показываем короткую версию для compact
    if (layout === "compact" && data.barcode.length > 8) {
      return data.barcode.slice(0, 5) + "...";
    }
    return data.barcode;
  }, [data.barcode, layout]);

  const sizeColor = useMemo(() => {
    const parts = [];
    if (data.color) parts.push(data.color);
    if (data.size) parts.push(data.size);
    return parts.join(" / ");
  }, [data.color, data.size]);

  // Classic layout: штрихкод сверху, текст снизу
  if (layout === "classic") {
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

  // Compact layout: штрихкод слева, текст справа
  if (layout === "compact") {
    return (
      <div
        className={`aspect-[58/40] bg-white border-2 border-warm-gray-200 rounded-lg p-2 flex gap-2 shadow-sm ${className || ""}`}
      >
        {/* Barcode left */}
        <div className="flex flex-col items-center justify-center w-1/3">
          <div className="flex gap-[1px]">
            {[...Array(12)].map((_, i) => (
              <div
                key={i}
                className="w-[1px] bg-warm-gray-800"
                style={{ height: `${16 + (i % 2) * 4}px` }}
              />
            ))}
          </div>
          <p className="text-[6px] text-warm-gray-600 mt-0.5">
            {barcodeDisplay}
          </p>
        </div>

        {/* Text right */}
        <div className="flex-1 flex flex-col justify-center text-left">
          {showName && data.name && (
            <p className="text-[8px] font-medium text-warm-gray-800 truncate">
              {data.name}
            </p>
          )}
          {showSizeColor && sizeColor && (
            <p className="text-[7px] text-warm-gray-600">{sizeColor}</p>
          )}
          {showArticle && data.article && (
            <p className="text-[7px] text-warm-gray-600">
              Арт: {data.article}
            </p>
          )}
          <p className="text-[6px] text-warm-gray-500 truncate mt-auto">
            {data.organization}
          </p>
        </div>
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
