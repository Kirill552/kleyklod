"use client";

/**
 * Модалка создания/редактирования карточки товара.
 *
 * Поддерживает валидацию баркода (13-14 цифр).
 */

import { useEffect, useState } from "react";
import { X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ProductCard, ProductCardCreate } from "@/lib/api";

interface ProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: ProductCardCreate) => Promise<void>;
  product?: ProductCard | null;
  loading?: boolean;
}

export function ProductModal({
  isOpen,
  onClose,
  onSave,
  product,
  loading,
}: ProductModalProps) {
  const [formData, setFormData] = useState<ProductCardCreate>({
    barcode: "",
    name: "",
    article: "",
    size: "",
    color: "",
    composition: "",
    country: "",
    brand: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const isEditing = !!product;

  // Заполняем форму при редактировании
  useEffect(() => {
    if (product) {
      setFormData({
        barcode: product.barcode,
        name: product.name || "",
        article: product.article || "",
        size: product.size || "",
        color: product.color || "",
        composition: product.composition || "",
        country: product.country || "",
        brand: product.brand || "",
      });
    } else {
      setFormData({
        barcode: "",
        name: "",
        article: "",
        size: "",
        color: "",
        composition: "",
        country: "",
        brand: "",
      });
    }
    setErrors({});
  }, [product, isOpen]);

  // Закрытие по Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Блокируем скролл при открытии
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  /**
   * Валидация формы.
   */
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Баркод обязателен и должен быть 13-14 цифр
    if (!formData.barcode.trim()) {
      newErrors.barcode = "Баркод обязателен";
    } else if (!/^\d{13,14}$/.test(formData.barcode.trim())) {
      newErrors.barcode = "Баркод должен содержать 13-14 цифр";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Обработка отправки формы.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setSaving(true);
    try {
      await onSave({
        ...formData,
        barcode: formData.barcode.trim(),
        name: formData.name?.trim() || null,
        article: formData.article?.trim() || null,
        size: formData.size?.trim() || null,
        color: formData.color?.trim() || null,
        composition: formData.composition?.trim() || null,
        country: formData.country?.trim() || null,
        brand: formData.brand?.trim() || null,
      });
      onClose();
    } catch (error) {
      if (error instanceof Error) {
        setErrors({ submit: error.message });
      }
    } finally {
      setSaving(false);
    }
  };

  /**
   * Обработка изменения поля.
   */
  const handleChange = (field: keyof ProductCardCreate, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Очищаем ошибку при изменении
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-warm-gray-200">
          <h2 className="text-xl font-semibold text-warm-gray-900">
            {isEditing ? "Редактирование карточки" : "Новая карточка товара"}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-warm-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-warm-gray-600" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Ошибка отправки */}
          {errors.submit && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{errors.submit}</p>
            </div>
          )}

          {/* Баркод */}
          <div>
            <label className="block text-sm font-medium text-warm-gray-700 mb-1">
              Баркод <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.barcode}
              onChange={(e) => handleChange("barcode", e.target.value)}
              placeholder="4607000000001"
              disabled={isEditing}
              className={`w-full px-4 py-2.5 rounded-lg border bg-white font-mono
                ${errors.barcode ? "border-red-300 focus:ring-red-500" : "border-warm-gray-300 focus:ring-emerald-500"}
                ${isEditing ? "bg-warm-gray-50 text-warm-gray-500 cursor-not-allowed" : ""}
                focus:outline-none focus:ring-2 focus:border-transparent`}
            />
            {errors.barcode && (
              <p className="text-xs text-red-600 mt-1">{errors.barcode}</p>
            )}
            <p className="text-xs text-warm-gray-500 mt-1">
              EAN-13 или Code128 (13-14 цифр)
            </p>
          </div>

          {/* Название */}
          <div>
            <label className="block text-sm font-medium text-warm-gray-700 mb-1">
              Название товара
            </label>
            <input
              type="text"
              value={formData.name || ""}
              onChange={(e) => handleChange("name", e.target.value)}
              placeholder="Футболка мужская"
              className="w-full px-4 py-2.5 rounded-lg border border-warm-gray-300 bg-white
                focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Артикул */}
            <div>
              <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                Артикул
              </label>
              <input
                type="text"
                value={formData.article || ""}
                onChange={(e) => handleChange("article", e.target.value)}
                placeholder="ABC-123"
                className="w-full px-4 py-2.5 rounded-lg border border-warm-gray-300 bg-white
                  focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>

            {/* Бренд */}
            <div>
              <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                Бренд
              </label>
              <input
                type="text"
                value={formData.brand || ""}
                onChange={(e) => handleChange("brand", e.target.value)}
                placeholder="Nike"
                className="w-full px-4 py-2.5 rounded-lg border border-warm-gray-300 bg-white
                  focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Размер */}
            <div>
              <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                Размер
              </label>
              <input
                type="text"
                value={formData.size || ""}
                onChange={(e) => handleChange("size", e.target.value)}
                placeholder="M"
                className="w-full px-4 py-2.5 rounded-lg border border-warm-gray-300 bg-white
                  focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>

            {/* Цвет */}
            <div>
              <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                Цвет
              </label>
              <input
                type="text"
                value={formData.color || ""}
                onChange={(e) => handleChange("color", e.target.value)}
                placeholder="Черный"
                className="w-full px-4 py-2.5 rounded-lg border border-warm-gray-300 bg-white
                  focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Состав */}
          <div>
            <label className="block text-sm font-medium text-warm-gray-700 mb-1">
              Состав
            </label>
            <input
              type="text"
              value={formData.composition || ""}
              onChange={(e) => handleChange("composition", e.target.value)}
              placeholder="100% хлопок"
              className="w-full px-4 py-2.5 rounded-lg border border-warm-gray-300 bg-white
                focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>

          {/* Страна производства */}
          <div>
            <label className="block text-sm font-medium text-warm-gray-700 mb-1">
              Страна производства
            </label>
            <input
              type="text"
              value={formData.country || ""}
              onChange={(e) => handleChange("country", e.target.value)}
              placeholder="Россия"
              className="w-full px-4 py-2.5 rounded-lg border border-warm-gray-300 bg-white
                focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-warm-gray-200 bg-warm-gray-50">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={saving}
          >
            Отмена
          </Button>
          <Button
            type="submit"
            variant="primary"
            onClick={handleSubmit}
            disabled={saving || loading}
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Сохранение...
              </>
            ) : isEditing ? (
              "Сохранить"
            ) : (
              "Создать"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
