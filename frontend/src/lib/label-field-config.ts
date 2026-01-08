/**
 * Конфиг полей этикеток — поддерживаемые поля, лимиты и доступность для каждого шаблона/размера.
 *
 * Синхронизирован с backend/app/services/label_generator.py
 * При изменении лимитов на бэкенде — обновить здесь!
 */

import type { LabelLayout, LabelSize } from "./api";

/**
 * ID полей этикетки.
 * Расширенный список для всех шаблонов.
 */
export type FieldId =
  | "inn"
  | "name"
  | "article"
  | "size"
  | "color"
  | "size_color" // Объединённое поле размер/цвет для basic
  | "country"
  | "composition"
  | "brand"
  | "manufacturer"
  | "production_date"
  | "importer"
  | "certificate"
  | "address"
  | "chz_code_text"
  | "custom_1"
  | "custom_2"
  | "custom_3";

/**
 * Человеко-читаемые названия полей.
 */
export const FIELD_LABELS: Record<FieldId, string> = {
  inn: "ИНН",
  name: "Название товара",
  article: "Артикул",
  size: "Размер",
  color: "Цвет",
  size_color: "Размер/Цвет",
  country: "Страна",
  composition: "Состав",
  brand: "Бренд",
  manufacturer: "Производитель",
  production_date: "Дата производства",
  importer: "Импортёр",
  certificate: "Сертификат",
  address: "Адрес",
  chz_code_text: "Код ЧЗ",
  custom_1: "Строка 1",
  custom_2: "Строка 2",
  custom_3: "Строка 3",
};

/**
 * Конфигурация поля для конкретного шаблона/размера.
 */
export interface FieldLimitConfig {
  /** Поддерживается ли поле в этом шаблоне */
  supported: boolean;
  /** Максимальное количество символов (приблизительно, зависит от шрифта) */
  maxChars?: number;
  /** Максимальное количество строк */
  maxLines?: number;
  /** Подсказка при превышении лимита */
  warningHint?: string;
}

/** Конфигурация всех полей для шаблона/размера */
export type FieldsConfig = Partial<Record<FieldId, FieldLimitConfig>>;

/** Ключ для конфига: layout + size */
type ConfigKey = `${LabelLayout}_${LabelSize}`;

/**
 * Лимиты количества активных полей для каждого шаблона/размера.
 */
export const FIELD_LIMITS: Record<ConfigKey, number> = {
  // Basic
  basic_58x30: 2,
  basic_58x40: 4,
  basic_58x60: 4,
  // Professional
  professional_58x30: 10, // Не используется, но для консистентности
  professional_58x40: 10,
  professional_58x60: 10, // Не используется, но для консистентности
  // Extended
  extended_58x30: 12, // Не используется, но для консистентности
  extended_58x40: 12,
  extended_58x60: 12,
};

/**
 * Порядок полей для отображения в списке.
 * Общий порядок, неподдерживаемые поля будут скрыты.
 */
export const FIELD_ORDER: FieldId[] = [
  "inn",
  "name",
  "article",
  "size",
  "color",
  "size_color",
  "brand",
  "country",
  "composition",
  "manufacturer",
  "importer",
  "address",
  "production_date",
  "certificate",
  "custom_1",
  "custom_2",
  "custom_3",
];

/**
 * Доступные поля для каждого шаблона.
 * Определяет какие поля показываются в списке.
 */
export const AVAILABLE_FIELDS: Record<LabelLayout, FieldId[]> = {
  basic: [
    "inn",
    "name",
    "article",
    "size",
    "color",
    "brand",
    "country",
    "composition", // только для 58x60
  ],
  professional: [
    "inn",
    "name",
    "article",
    "size",
    "color",
    "brand",
    "country",
    "manufacturer",
    "importer",
    "address",
    "certificate",
  ],
  extended: [
    "inn",
    "name",
    "article",
    "size",
    "color",
    "brand",
    "country",
    "composition",
    "manufacturer",
    "address",
    "custom_1",
    "custom_2",
    "custom_3",
  ],
};

/**
 * Приблизительное количество символов на строку для каждого шаблона.
 * Рассчитано на основе ширины текстовой области и среднего шрифта.
 */
const CHARS_PER_LINE: Record<ConfigKey, number> = {
  // Basic 58x30: 28.5мм ширина, ~6pt шрифт → ~25 символов
  basic_58x30: 25,
  // Basic 58x40: 31мм ширина, ~7pt шрифт → ~28 символов
  basic_58x40: 28,
  // Basic 58x60: 33мм ширина, ~8pt шрифт → ~30 символов
  basic_58x60: 30,
  // Professional: 30.5мм, ~5pt шрифт → ~35 символов
  professional_58x30: 35,
  professional_58x40: 35,
  professional_58x60: 35,
  // Extended: 31мм, ~5.5pt шрифт → ~32 символа
  extended_58x30: 32,
  extended_58x40: 32,
  extended_58x60: 32,
};

/**
 * Конфиг полей для Basic 58x30 (компактный).
 * Только: название, размер/цвет, артикул (2 строки блок).
 */
const BASIC_58x30: FieldsConfig = {
  inn: { supported: true, maxChars: 12 },
  name: {
    supported: true,
    maxLines: 2,
    maxChars: 50,
    warningHint: "Название будет обрезано до 2 строк",
  },
  article: {
    supported: true,
    maxChars: 20,
    warningHint: "Артикул может не поместиться",
  },
  size: {
    supported: true,
    maxChars: 10,
  },
  color: {
    supported: true,
    maxChars: 15,
  },
  size_color: {
    supported: true,
    maxChars: 20,
    warningHint: "Размер/цвет может быть обрезан",
  },
  country: {
    supported: true,
    maxChars: 20,
  },
  brand: {
    supported: true,
    maxChars: 20,
  },
  composition: {
    supported: false,
    warningHint: "Состав не отображается в Basic 58x30",
  },
  manufacturer: {
    supported: false,
  },
  importer: {
    supported: false,
  },
  address: {
    supported: false,
  },
  production_date: {
    supported: false,
  },
  certificate: {
    supported: false,
  },
  custom_1: { supported: false },
  custom_2: { supported: false },
  custom_3: { supported: false },
  chz_code_text: { supported: false },
};

/**
 * Конфиг полей для Basic 58x40 (стандартный).
 * Название, артикул, размер/цвет, страна, бренд (4 строки блок).
 */
const BASIC_58x40: FieldsConfig = {
  inn: { supported: true, maxChars: 12 },
  name: {
    supported: true,
    maxLines: 2,
    maxChars: 56,
    warningHint: "Название будет обрезано до 2 строк",
  },
  article: {
    supported: true,
    maxChars: 25,
    warningHint: "Длинный артикул будет обрезан",
  },
  size: {
    supported: true,
    maxChars: 12,
  },
  color: {
    supported: true,
    maxChars: 18,
  },
  size_color: {
    supported: true,
    maxChars: 25,
  },
  country: {
    supported: true,
    maxChars: 25,
  },
  brand: {
    supported: true,
    maxChars: 25,
  },
  composition: {
    supported: false,
    warningHint: "Состав не отображается в Basic 58x40",
  },
  manufacturer: {
    supported: false,
  },
  importer: {
    supported: false,
  },
  address: {
    supported: false,
  },
  production_date: {
    supported: false,
  },
  certificate: {
    supported: false,
  },
  custom_1: { supported: false },
  custom_2: { supported: false },
  custom_3: { supported: false },
  chz_code_text: { supported: false },
};

/**
 * Конфиг полей для Basic 58x60 (увеличенный).
 * Все поля включая состав (4 строки блок).
 */
const BASIC_58x60: FieldsConfig = {
  inn: { supported: true, maxChars: 12 },
  name: {
    supported: true,
    maxLines: 2,
    maxChars: 60,
    warningHint: "Название будет обрезано до 2 строк",
  },
  article: {
    supported: true,
    maxChars: 28,
  },
  size: {
    supported: true,
    maxChars: 14,
  },
  color: {
    supported: true,
    maxChars: 20,
  },
  size_color: {
    supported: true,
    maxChars: 28,
  },
  country: {
    supported: true,
    maxChars: 28,
  },
  composition: {
    supported: true,
    maxChars: 60,
    maxLines: 2,
    warningHint: "Длинный состав будет перенесён",
  },
  brand: {
    supported: true,
    maxChars: 28,
  },
  manufacturer: {
    supported: false,
  },
  importer: {
    supported: false,
  },
  address: {
    supported: false,
  },
  production_date: {
    supported: false,
  },
  certificate: {
    supported: false,
  },
  custom_1: { supported: false },
  custom_2: { supported: false },
  custom_3: { supported: false },
  chz_code_text: { supported: false },
};

/**
 * Конфиг полей для Professional 58x40.
 * Горизонтальный layout с реквизитами (10 строк блок).
 */
const PROFESSIONAL_58x40: FieldsConfig = {
  inn: { supported: true, maxChars: 12 },
  name: {
    supported: true,
    maxLines: 2,
    maxChars: 70,
    warningHint: "Название будет обрезано до 2 строк",
  },
  article: {
    supported: true,
    maxChars: 30,
  },
  size: {
    supported: true,
    maxChars: 15,
  },
  color: {
    supported: true,
    maxChars: 20,
  },
  size_color: {
    supported: true,
    maxChars: 30,
  },
  country: {
    supported: true,
    maxChars: 30,
  },
  composition: {
    supported: false,
    warningHint: "Состав не отображается в Professional",
  },
  brand: {
    supported: true,
    maxChars: 30,
  },
  manufacturer: {
    supported: true,
    maxChars: 39,
  },
  importer: {
    supported: true,
    maxChars: 39,
  },
  address: {
    supported: true,
    maxChars: 39,
  },
  production_date: {
    supported: false, // По плану production_date везде false
  },
  certificate: {
    supported: true,
    maxChars: 19,
  },
  custom_1: { supported: false },
  custom_2: { supported: false },
  custom_3: { supported: false },
  chz_code_text: { supported: false },
};

/**
 * Конфиг полей для Extended 58x40.
 * С кастомными строками справа (12 строк блок).
 */
const EXTENDED_58x40: FieldsConfig = {
  inn: {
    supported: true,
    maxChars: 36,
    warningHint: "ИНН слишком длинный (макс. 36 символов)",
  },
  name: {
    supported: true,
    maxLines: 2,
    maxChars: 64,
    warningHint: "Название будет перенесено",
  },
  article: {
    supported: true,
    maxChars: 28,
  },
  size: {
    supported: true,
    maxChars: 14,
  },
  color: {
    supported: true,
    maxChars: 20,
  },
  size_color: {
    supported: true,
    maxChars: 28,
  },
  country: {
    supported: true,
    maxChars: 28,
  },
  composition: {
    supported: true,
    maxChars: 64,
    maxLines: 2,
  },
  brand: {
    supported: true,
    maxChars: 28,
  },
  manufacturer: {
    supported: true,
    maxChars: 31,
  },
  importer: {
    supported: false,
  },
  address: {
    supported: true,
    maxChars: 31,
  },
  production_date: {
    supported: false,
  },
  certificate: {
    supported: false,
  },
  custom_1: {
    supported: true,
    maxChars: 31,
  },
  custom_2: {
    supported: true,
    maxChars: 31,
  },
  custom_3: {
    supported: true,
    maxChars: 31,
  },
  chz_code_text: { supported: true, maxChars: 50 },
};

/**
 * Полный конфиг для всех комбинаций шаблон + размер.
 */
const FIELD_CONFIGS: Partial<Record<ConfigKey, FieldsConfig>> = {
  basic_58x30: BASIC_58x30,
  basic_58x40: BASIC_58x40,
  basic_58x60: BASIC_58x60,
  professional_58x40: PROFESSIONAL_58x40,
  extended_58x40: EXTENDED_58x40,
  // Professional и Extended поддерживают только 58x40
  // Остальные комбинации fallback на 58x40
};

/**
 * Получить конфиг полей для шаблона и размера.
 */
export function getFieldConfig(
  layout: LabelLayout,
  size: LabelSize
): FieldsConfig {
  const key: ConfigKey = `${layout}_${size}`;

  // Прямое совпадение
  if (FIELD_CONFIGS[key]) {
    return FIELD_CONFIGS[key]!;
  }

  // Fallback для Professional/Extended — только 58x40
  if (layout === "professional") {
    return PROFESSIONAL_58x40;
  }
  if (layout === "extended") {
    return EXTENDED_58x40;
  }

  // Fallback для Basic — 58x40
  return BASIC_58x40;
}

/**
 * Получить лимит активных полей для шаблона и размера.
 */
export function getFieldLimit(layout: LabelLayout, size: LabelSize): number {
  const key: ConfigKey = `${layout}_${size}`;
  return FIELD_LIMITS[key] ?? 4;
}

/**
 * Получить название шаблона для отображения.
 */
export function getLayoutDisplayName(layout: LabelLayout): string {
  const names: Record<LabelLayout, string> = {
    basic: "Basic",
    professional: "Professional",
    extended: "Extended",
  };
  return names[layout];
}

/**
 * Проверить, поддерживается ли поле в шаблоне.
 */
export function isFieldSupported(
  fieldId: FieldId,
  layout: LabelLayout,
  size: LabelSize
): boolean {
  const config = getFieldConfig(layout, size);
  return config[fieldId]?.supported ?? false;
}

/**
 * Проверить, является ли поле кастомным.
 */
export function isCustomField(fieldId: FieldId): boolean {
  return fieldId === "custom_1" || fieldId === "custom_2" || fieldId === "custom_3";
}

/**
 * Получить список доступных полей для шаблона и размера.
 * Учитывает особые случаи (composition только для 58x60 в Basic).
 */
export function getAvailableFields(
  layout: LabelLayout,
  size: LabelSize
): FieldId[] {
  const baseFields = AVAILABLE_FIELDS[layout];
  const config = getFieldConfig(layout, size);

  return baseFields.filter((fieldId) => {
    const fieldConfig = config[fieldId];
    return fieldConfig?.supported === true;
  });
}

/**
 * Проверить длину значения поля.
 * Возвращает warning если превышен лимит.
 */
export function checkFieldLength(
  fieldId: FieldId,
  value: string | null | undefined,
  layout: LabelLayout,
  size: LabelSize
): { isOverLimit: boolean; warning?: string } {
  if (!value) {
    return { isOverLimit: false };
  }

  const config = getFieldConfig(layout, size);
  const fieldConfig = config[fieldId];

  if (!fieldConfig?.supported) {
    return { isOverLimit: false };
  }

  if (fieldConfig.maxChars && value.length > fieldConfig.maxChars) {
    return {
      isOverLimit: true,
      warning:
        fieldConfig.warningHint ||
        `Слишком длинное значение (${value.length}/${fieldConfig.maxChars} символов)`,
    };
  }

  return { isOverLimit: false };
}

/**
 * Получить список поддерживаемых полей для шаблона.
 */
export function getSupportedFields(
  layout: LabelLayout,
  size: LabelSize
): FieldId[] {
  const config = getFieldConfig(layout, size);
  return (Object.keys(config) as FieldId[]).filter(
    (fieldId) => config[fieldId]?.supported
  );
}

/**
 * Получить список НЕподдерживаемых полей для шаблона.
 */
export function getUnsupportedFields(
  layout: LabelLayout,
  size: LabelSize
): FieldId[] {
  const config = getFieldConfig(layout, size);
  return (Object.keys(config) as FieldId[]).filter(
    (fieldId) => !config[fieldId]?.supported
  );
}

/**
 * Получить hint для неподдерживаемого поля.
 */
export function getUnsupportedFieldHint(
  fieldId: FieldId,
  layout: LabelLayout,
  size: LabelSize
): string | undefined {
  const config = getFieldConfig(layout, size);
  return config[fieldId]?.warningHint;
}

/**
 * Приблизительное количество символов на строку.
 */
export function getCharsPerLine(layout: LabelLayout, size: LabelSize): number {
  const key: ConfigKey = `${layout}_${size}`;
  return CHARS_PER_LINE[key] || 28;
}

/**
 * Получить человеко-читаемое название поля.
 */
export function getFieldLabel(fieldId: FieldId): string {
  return FIELD_LABELS[fieldId] || fieldId;
}
