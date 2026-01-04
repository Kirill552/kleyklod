"use client";

/**
 * Таблица карточек товаров.
 *
 * Отображает список карточек с возможностью редактирования и удаления.
 */

import { Edit, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ProductCard } from "@/lib/api";

interface ProductTableProps {
  products: ProductCard[];
  onEdit: (product: ProductCard) => void;
  onDelete: (product: ProductCard) => void;
  loading?: boolean;
}

export function ProductTable({
  products,
  onEdit,
  onDelete,
  loading,
}: ProductTableProps) {
  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-14 bg-warm-gray-100 rounded-lg"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-warm-gray-200">
            <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
              Баркод
            </th>
            <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
              Название
            </th>
            <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700 hidden md:table-cell">
              Артикул
            </th>
            <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700 hidden lg:table-cell">
              Размер/Цвет
            </th>
            <th className="text-right py-3 px-4 text-sm font-semibold text-warm-gray-700">
              Последний №
            </th>
            <th className="text-right py-3 px-4 text-sm font-semibold text-warm-gray-700">
              Действия
            </th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr
              key={product.id}
              className="border-b border-warm-gray-100 hover:bg-warm-gray-50 transition-colors"
            >
              <td className="py-4 px-4">
                <span className="font-mono text-sm text-warm-gray-900">
                  {product.barcode}
                </span>
              </td>
              <td className="py-4 px-4">
                <div className="max-w-[200px]">
                  <p className="text-sm text-warm-gray-900 truncate">
                    {product.name || "—"}
                  </p>
                  {product.brand && (
                    <p className="text-xs text-warm-gray-500 truncate">
                      {product.brand}
                    </p>
                  )}
                </div>
              </td>
              <td className="py-4 px-4 hidden md:table-cell">
                <span className="text-sm text-warm-gray-600">
                  {product.article || "—"}
                </span>
              </td>
              <td className="py-4 px-4 hidden lg:table-cell">
                <span className="text-sm text-warm-gray-600">
                  {product.size && product.color
                    ? `${product.size} / ${product.color}`
                    : product.size || product.color || "—"}
                </span>
              </td>
              <td className="py-4 px-4 text-right">
                <span className="inline-flex items-center justify-center min-w-[48px] px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                  {product.last_serial_number}
                </span>
              </td>
              <td className="py-4 px-4">
                <div className="flex items-center justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(product)}
                    title="Редактировать"
                  >
                    <Edit className="w-4 h-4 text-warm-gray-600" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(product)}
                    title="Удалить"
                    className="hover:text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
