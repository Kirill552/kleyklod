"use client";

/**
 * Hint для PRO/ENTERPRISE пользователей о карточках товаров.
 *
 * Показывает "Aha! moment" — сохрани карточки один раз,
 * потом загружай только баркоды.
 */

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Lightbulb, X, Plus, Check } from "lucide-react";

interface ProductCardsHintProps {
  /** Обработчик dismiss — вызывается при клике "Понятно" или [×] */
  onDismiss: () => void;
}

export function ProductCardsHint({ onDismiss }: ProductCardsHintProps) {
  const router = useRouter();

  const handleCreateCard = () => {
    router.push("/app/products");
  };

  return (
    <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 mb-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Lightbulb className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-emerald-900">Совет PRO</p>
            <p className="text-sm text-emerald-700 mt-1">
              Сохраните карточки товаров один раз — потом загружайте только
              баркоды.
            </p>
            <p className="text-sm text-emerald-700 mt-1">
              Название, артикул, состав подтянутся автоматически.
            </p>
            <div className="flex flex-wrap gap-2 mt-3">
              <Button variant="primary" size="sm" onClick={handleCreateCard}>
                <Plus className="w-4 h-4" />
                Создать первую карточку
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={onDismiss}
                className="text-emerald-700"
              >
                <Check className="w-4 h-4" />
                Понятно
              </Button>
            </div>
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="text-emerald-500 hover:text-emerald-700 p-1"
          aria-label="Закрыть"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
