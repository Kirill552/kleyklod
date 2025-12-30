"use client";

/**
 * Модалка для ввода реквизитов организации.
 *
 * Используется для профессионального шаблона этикеток.
 * Позволяет ввести все данные организации в одном месте.
 */

import { useState, useEffect } from "react";

export interface OrganizationData {
  organizationName: string;
  inn: string;
  organizationAddress: string;
  productionCountry: string;
  certificateNumber: string;
  importer: string;
  manufacturer: string;
  productionDate: string;
  brand: string;
}

interface OrganizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: OrganizationData) => void;
  initialData?: Partial<OrganizationData>;
}

export function OrganizationModal({
  isOpen,
  onClose,
  onSave,
  initialData,
}: OrganizationModalProps) {
  const [formData, setFormData] = useState<OrganizationData>({
    organizationName: "",
    inn: "",
    organizationAddress: "",
    productionCountry: "",
    certificateNumber: "",
    importer: "",
    manufacturer: "",
    productionDate: "",
    brand: "",
  });

  // Заполняем форму начальными данными при открытии
  useEffect(() => {
    if (isOpen && initialData) {
      setFormData({
        organizationName: initialData.organizationName || "",
        inn: initialData.inn || "",
        organizationAddress: initialData.organizationAddress || "",
        productionCountry: initialData.productionCountry || "",
        certificateNumber: initialData.certificateNumber || "",
        importer: initialData.importer || "",
        manufacturer: initialData.manufacturer || "",
        productionDate: initialData.productionDate || "",
        brand: initialData.brand || "",
      });
    }
  }, [isOpen, initialData]);

  const handleChange = (field: keyof OrganizationData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-warm-gray-200">
          <h2 className="text-lg font-semibold text-warm-gray-800">
            Реквизиты организации
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-warm-gray-100 transition-colors"
          >
            <svg
              className="w-5 h-5 text-warm-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="px-6 py-4 space-y-4">
            {/* Основная информация */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-warm-gray-700">
                Основная информация
              </h3>

              <div>
                <label className="block text-sm text-warm-gray-600 mb-1">
                  Название организации
                </label>
                <input
                  type="text"
                  value={formData.organizationName}
                  onChange={(e) => handleChange("organizationName", e.target.value)}
                  placeholder="ООО «Компания» или ИП Иванов И.И."
                  className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm text-warm-gray-600 mb-1">
                  ИНН
                </label>
                <input
                  type="text"
                  value={formData.inn}
                  onChange={(e) => handleChange("inn", e.target.value)}
                  placeholder="1234567890"
                  maxLength={12}
                  className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm text-warm-gray-600 mb-1">
                  Адрес производства
                </label>
                <textarea
                  value={formData.organizationAddress}
                  onChange={(e) => handleChange("organizationAddress", e.target.value)}
                  placeholder="г. Москва, ул. Примерная, д. 1"
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-sm text-warm-gray-600 mb-1">
                  Страна производства
                </label>
                <input
                  type="text"
                  value={formData.productionCountry}
                  onChange={(e) => handleChange("productionCountry", e.target.value)}
                  placeholder="Россия"
                  className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Дополнительная информация */}
            <div className="space-y-3 pt-2 border-t border-warm-gray-100">
              <h3 className="text-sm font-medium text-warm-gray-700">
                Дополнительная информация
              </h3>

              <div>
                <label className="block text-sm text-warm-gray-600 mb-1">
                  Бренд
                </label>
                <input
                  type="text"
                  value={formData.brand}
                  onChange={(e) => handleChange("brand", e.target.value)}
                  placeholder="Название бренда"
                  className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-warm-gray-600 mb-1">
                    Импортер
                  </label>
                  <input
                    type="text"
                    value={formData.importer}
                    onChange={(e) => handleChange("importer", e.target.value)}
                    placeholder="Название импортера"
                    className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-warm-gray-600 mb-1">
                    Производитель
                  </label>
                  <input
                    type="text"
                    value={formData.manufacturer}
                    onChange={(e) => handleChange("manufacturer", e.target.value)}
                    placeholder="Название производителя"
                    className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-warm-gray-600 mb-1">
                    Номер сертификата
                  </label>
                  <input
                    type="text"
                    value={formData.certificateNumber}
                    onChange={(e) => handleChange("certificateNumber", e.target.value)}
                    placeholder="РОСС RU.XXX.X00000"
                    className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-warm-gray-600 mb-1">
                    Дата производства
                  </label>
                  <input
                    type="text"
                    value={formData.productionDate}
                    onChange={(e) => handleChange("productionDate", e.target.value)}
                    placeholder="12.2025"
                    className="w-full px-3 py-2 rounded-lg border border-warm-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
              </div>
            </div>

            {/* Hint */}
            <p className="text-xs text-warm-gray-500 pt-2">
              Эти данные будут использованы для профессионального шаблона этикеток.
              Вы можете сохранить их в настройках профиля для повторного использования.
            </p>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-warm-gray-200 bg-warm-gray-50">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-warm-gray-700 hover:bg-warm-gray-100 rounded-lg transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors"
            >
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
