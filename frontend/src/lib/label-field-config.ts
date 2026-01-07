/**
 * Конфиг полей этикеток — поддерживаемые поля и лимиты для каждого шаблона/размера.
 *
 * Синхронизирован с backend/app/services/label_generator.py
 * При изменении лимитов на бэкенде — обновить здесь!
 */

import type { LabelLayout, LabelSize } from "./api";

/** ID полей этикетки */
export type FieldId =
  | "serial_number"
  | "inn"
  | "name"
  | "article"
  | "size_color"
  | "country"
  | "composition"
  | "brand"
  | "chz_code_text";

/** Конфигурация поля для конкретного шаблона/размера */
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
export type FieldsConfig = Record<FieldId, FieldLimitConfig>;

/** Ключ для конфига: layout + size */
type ConfigKey = `${LabelLayout}_${LabelSize}`;

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
  serial_number: { supported: true, maxChars: 10 },
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
  size_color: {
    supported: true,
    maxChars: 20,
    warningHint: "Размер/цвет может быть обрезан",
  },
  country: {
    supported: false,
    warningHint: "Страна не отображается в Basic 58x30",
  },
  composition: {
    supported: false,
    warningHint: "Состав не отображается в Basic 58x30",
  },
  brand: {
    supported: false,
    warningHint: "Бренд не отображается в Basic 58x30",
  },
  chz_code_text: { supported: false },
};

/**
 * Конфиг полей для Basic 58x40 (стандартный).
 * Название, артикул, размер/цвет, страна, бренд (4 строки блок).
 */
const BASIC_58x40: FieldsConfig = {
  serial_number: { supported: true, maxChars: 10 },
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
  size_color: {
    supported: true,
    maxChars: 25,
  },
  country: {
    supported: true,
    maxChars: 25,
  },
  composition: {
    supported: false,
    warningHint: "Состав не отображается в Basic 58x40",
  },
  brand: {
    supported: true,
    maxChars: 25,
  },
  chz_code_text: { supported: false },
};

/**
 * Конфиг полей для Basic 58x60 (увеличенный).
 * Все поля включая состав (4 строки блок).
 */
const BASIC_58x60: FieldsConfig = {
  serial_number: { supported: true, maxChars: 10 },
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
  chz_code_text: { supported: false },
};

/**
 * Конфиг полей для Professional 58x40.
 * Горизонтальный layout с реквизитами (10 строк блок).
 */
const PROFESSIONAL_58x40: FieldsConfig = {
  serial_number: { supported: true, maxChars: 10 },
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
  chz_code_text: { supported: false },
};

/**
 * Конфиг полей для Extended 58x40.
 * С кастомными строками справа (12 строк блок).
 */
const EXTENDED_58x40: FieldsConfig = {
  serial_number: { supported: true, maxChars: 10 },
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
    (fieldId) => config[fieldId].supported
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
    (fieldId) => !config[fieldId].supported
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
