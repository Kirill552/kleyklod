"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Check, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GtinInfo, GtinMatchingStatus } from "@/lib/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ExcelItem {
  barcode: string;
  name: string | null;
  size: string | null;
  color: string | null;
  article: string | null;
}

interface GtinMatchingBlockProps {
  /** Статус матчинга */
  status: GtinMatchingStatus;
  /** Список GTIN из ЧЗ кодов */
  gtins: GtinInfo[];
  /** Товары из Excel */
  excelItems: ExcelItem[];
  /** Текущий маппинг GTIN → индекс товара */
  mapping: Map<string, number>;
  /** Callback при изменении маппинга */
  onMappingChange: (gtin: string, itemIndex: number | null) => void;
  /** Общее количество кодов */
  totalCodes: number;
}

/**
 * Блок матчинга GTIN с товарами.
 * - Свёрнут когда всё ок (auto_matched)
 * - Раскрыт когда нужно действие (manual_required)
 */
export function GtinMatchingBlock({
  status,
  gtins,
  excelItems,
  mapping,
  onMappingChange,
  totalCodes,
}: GtinMatchingBlockProps) {
  const [isExpanded, setIsExpanded] = useState(status === "manual_required");

  // Подсчёт сматченных
  const matchedCount = Array.from(mapping.values()).filter((v) => v !== null && v !== undefined).length;
  const allMatched = matchedCount === gtins.length;

  // Проверка дублей
  const duplicates = findDuplicates(mapping);

  // Форматирование товара для dropdown
  const formatItem = (item: ExcelItem): string => {
    const parts = [item.name || "Без названия"];
    if (item.color) parts.push(item.color);
    if (item.size) parts.push(`р. ${item.size}`);
    if (item.article) parts.push(`арт. ${item.article}`);
    return parts.join(" / ");
  };

  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        status === "auto_matched" && "border-green-200 bg-green-50",
        status === "auto_fallback" && "border-yellow-200 bg-yellow-50",
        status === "manual_required" && "border-orange-200 bg-orange-50",
        status === "error" && "border-red-200 bg-red-50"
      )}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          {status === "auto_matched" && (
            <>
              <Check className="h-5 w-5 text-green-600" />
              <span className="font-medium text-green-800">
                Товары сопоставлены автоматически
              </span>
            </>
          )}
          {status === "auto_fallback" && (
            <>
              <Info className="h-5 w-5 text-yellow-600" />
              <span className="font-medium text-yellow-800">
                Баркод WB отличается от GTIN — применён авто-матчинг
              </span>
            </>
          )}
          {status === "manual_required" && (
            <>
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <span className="font-medium text-orange-800">
                Требуется ручное сопоставление
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-warm-gray-600">
            {gtins.length} товаров → {totalCodes} кодов
          </span>
          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-warm-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-warm-gray-400" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Описание для manual_required */}
          {status === "manual_required" && (
            <p className="text-sm text-warm-gray-600">
              Баркоды в Excel отличаются от GTIN в кодах ЧЗ.
              Укажите какой товар соответствует каждому GTIN.
            </p>
          )}

          {/* Таблица матчинга */}
          <div className="overflow-hidden rounded-lg border border-warm-gray-200 bg-white">
            <table className="min-w-full divide-y divide-warm-gray-200">
              <thead className="bg-warm-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-warm-gray-500">
                    GTIN
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-warm-gray-500">
                    Кодов
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-warm-gray-500">
                    Товар
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-warm-gray-200">
                {gtins.map((gtin) => {
                  const selectedIndex = mapping.get(gtin.gtin);
                  const isDuplicate = duplicates.has(gtin.gtin);

                  return (
                    <tr key={gtin.gtin}>
                      <td className="px-4 py-3 font-mono text-sm">
                        {gtin.gtin}
                      </td>
                      <td className="px-4 py-3 text-sm text-warm-gray-600">
                        {gtin.codes_count}
                      </td>
                      <td className="px-4 py-3">
                        {status === "manual_required" ? (
                          <Select
                            key={`select-${gtin.gtin}`}
                            value={selectedIndex?.toString() ?? ""}
                            onValueChange={(val) =>
                              onMappingChange(
                                gtin.gtin,
                                val ? parseInt(val, 10) : null
                              )
                            }
                          >
                            <SelectTrigger
                              className={cn(
                                "w-full",
                                isDuplicate && "border-yellow-400 bg-yellow-50"
                              )}
                            >
                              <SelectValue placeholder="Выберите товар" />
                            </SelectTrigger>
                            <SelectContent
                              position="popper"
                              side="bottom"
                              align="start"
                              sideOffset={4}
                            >
                              {excelItems.map((item, idx) => (
                                <SelectItem key={idx} value={idx.toString()}>
                                  {formatItem(item)}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <span className="text-sm">
                            {selectedIndex !== undefined
                              ? formatItem(excelItems[selectedIndex])
                              : "—"}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Warning о дублях */}
          {duplicates.size > 0 && (
            <div className="flex items-start gap-2 rounded-lg bg-yellow-100 p-3 text-sm text-yellow-800">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>
                Один товар выбран для нескольких GTIN. Убедитесь что это правильно.
              </span>
            </div>
          )}

          {/* Подсказка */}
          {status === "manual_required" && !allMatched && (
            <p className="flex items-center gap-2 text-sm text-warm-gray-500">
              <Info className="h-4 w-4" />
              Все GTIN должны быть привязаны для генерации
            </p>
          )}

          {/* Подсказка для auto */}
          {(status === "auto_matched" || status === "auto_fallback") && (
            <p className="text-xs text-warm-gray-500">
              💡 Если сопоставление неверное — можете изменить вручную
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/** Найти GTIN с дублирующимися товарами */
function findDuplicates(mapping: Map<string, number>): Set<string> {
  const duplicates = new Set<string>();
  const seen = new Map<number, string>();

  for (const [gtin, itemIndex] of mapping) {
    if (itemIndex === null || itemIndex === undefined) continue;

    if (seen.has(itemIndex)) {
      duplicates.add(gtin);
      duplicates.add(seen.get(itemIndex)!);
    } else {
      seen.set(itemIndex, gtin);
    }
  }

  return duplicates;
}
