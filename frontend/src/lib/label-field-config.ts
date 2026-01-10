/**
 * Конфиг полей этикеток — поддерживаемые поля, лимиты и доступность для каждого шаблона/размера.
 *
 * Синхронизирован с backend/app/services/label_generator.py
 * При изменении лимитов на бэкенде — обновить здесь!
 */

import type { LabelLayout, LabelSize } from "./api";

/**
 * ID полей этикетки.
 * 12 стандартных полей + 3 кастомных для Extended.
 *
 * ВАЖНО: chz_code_text убран — это системное поле, всегда включено.
 * ВАЖНО: size_color — объединённое поле (на бэкенде они всегда на одной строке).
 */
export type FieldId =
  | "inn"
  | "name"
  | "article"
  | "size_color" // Объединённое поле: размер + цвет (1 чекбокс, 2 инпута)
  | "brand"
  | "composition"
  | "country"
  | "manufacturer"
  | "production_date"
  | "importer"
  | "certificate"
  | "address"
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
  size_color: "Размер/Цвет", // Объединённое поле
  brand: "Бренд",
  composition: "Состав",
  country: "Страна",
  manufacturer: "Производитель",
  production_date: "Дата производства",
  importer: "Импортёр",
  certificate: "Сертификат",
  address: "Адрес",
  custom_1: "Кастомная строка",
  custom_2: "Кастомная строка",
  custom_3: "Кастомная строка",
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
 * 12 стандартных полей + 3 кастомных (только для Extended).
 * Все поля показываются всегда, недоступные — серые.
 */
export const FIELD_ORDER: FieldId[] = [
  "inn",
  "name",
  "article",
  "size_color", // Объединённое поле
  "brand",
  "composition",
  "country",
  "manufacturer",
  "production_date",
  "importer",
  "certificate",
  "address",
  // Кастомные строки только для Extended — добавляются отдельно
  "custom_1",
  "custom_2",
  "custom_3",
];

/**
 * Стандартные поля (без кастомных).
 * Показываются для всех шаблонов.
 */
export const STANDARD_FIELDS: FieldId[] = [
  "inn",
  "name",
  "article",
  "size_color", // Объединённое поле
  "brand",
  "composition",
  "country",
  "manufacturer",
  "production_date",
  "importer",
  "certificate",
  "address",
];

/**
 * Поля которые ПОДДЕРЖИВАЮТСЯ (можно включить) для каждого шаблона.
 * По таблице из плана 2026-01-08-unified-fields-ui-design.md
 *
 * Остальные поля показываются серыми (disabled).
 */
export const SUPPORTED_FIELDS: Record<LabelLayout, FieldId[]> = {
  // Basic: ИНН, Название, Артикул, Размер/Цвет, Бренд, Страна
  // Состав только для 58x60 (контролируется через supported в конфигах)
  basic: [
    "inn",
    "name",
    "article",
    "size_color", // Объединённое поле
    "brand",
    "composition", // Доступен только для 58x60 (в BASIC_58x30/58x40 supported: false)
    "country",
  ],
  // Professional: + Производитель, Импортёр, Сертификат, Адрес
  // НЕТ: Состав, Дата производства
  professional: [
    "inn",
    "name",
    "article",
    "size_color", // Объединённое поле
    "brand",
    "country",
    "manufacturer",
    "importer",
    "certificate",
    "address",
  ],
  // Extended: + Состав, Производитель, Адрес, 3 кастомных
  // НЕТ: Дата производства, Импортёр, Сертификат
  extended: [
    "inn",
    "name",
    "article",
    "size_color", // Объединённое поле
    "brand",
    "composition",
    "country",
    "manufacturer",
    "address",
    "custom_1",
    "custom_2",
    "custom_3",
  ],
};

// Для обратной совместимости
export const AVAILABLE_FIELDS = SUPPORTED_FIELDS;

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
 * Лимит: 2 поля в блоке.
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
  size_color: {
    supported: true,
    maxChars: 25, // Размер + цвет суммарно
    warningHint: "Размер/цвет слишком длинные",
  },
  brand: {
    supported: true,
    maxChars: 20,
  },
  composition: {
    supported: false,
    warningHint: "Состав не отображается в Basic 58x30",
  },
  country: {
    supported: true,
    maxChars: 20,
  },
  manufacturer: {
    supported: false,
    warningHint: "Производитель не отображается в Basic",
  },
  production_date: {
    supported: false,
    warningHint: "Дата производства не отображается в Basic",
  },
  importer: {
    supported: false,
    warningHint: "Импортёр не отображается в Basic",
  },
  certificate: {
    supported: false,
    warningHint: "Сертификат не отображается в Basic",
  },
  address: {
    supported: false,
    warningHint: "Адрес не отображается в Basic",
  },
  custom_1: { supported: false },
  custom_2: { supported: false },
  custom_3: { supported: false },
};

/**
 * Конфиг полей для Basic 58x40 (стандартный).
 * Лимит: 4 поля в блоке.
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
  size_color: {
    supported: true,
    maxChars: 28, // Размер + цвет суммарно (на одной строке)
    warningHint: "Размер/цвет слишком длинные",
  },
  brand: {
    supported: true,
    maxChars: 25,
  },
  composition: {
    supported: false,
    warningHint: "Состав не отображается в Basic 58x40",
  },
  country: {
    supported: true,
    maxChars: 25,
  },
  manufacturer: {
    supported: false,
    warningHint: "Производитель не отображается в Basic",
  },
  production_date: {
    supported: false,
    warningHint: "Дата производства не отображается в Basic",
  },
  importer: {
    supported: false,
    warningHint: "Импортёр не отображается в Basic",
  },
  certificate: {
    supported: false,
    warningHint: "Сертификат не отображается в Basic",
  },
  address: {
    supported: false,
    warningHint: "Адрес не отображается в Basic",
  },
  custom_1: { supported: false },
  custom_2: { supported: false },
  custom_3: { supported: false },
};

/**
 * Конфиг полей для Basic 58x60 (увеличенный).
 * Лимит: 4 поля в блоке. Состав поддерживается!
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
  size_color: {
    supported: true,
    maxChars: 32, // Размер + цвет суммарно
    warningHint: "Размер/цвет слишком длинные",
  },
  brand: {
    supported: true,
    maxChars: 28,
  },
  composition: {
    supported: true,
    maxChars: 60,
    maxLines: 2,
    warningHint: "Длинный состав будет перенесён",
  },
  country: {
    supported: true,
    maxChars: 28,
  },
  manufacturer: {
    supported: false,
    warningHint: "Производитель не отображается в Basic",
  },
  production_date: {
    supported: false,
    warningHint: "Дата производства не отображается в Basic",
  },
  importer: {
    supported: false,
    warningHint: "Импортёр не отображается в Basic",
  },
  certificate: {
    supported: false,
    warningHint: "Сертификат не отображается в Basic",
  },
  address: {
    supported: false,
    warningHint: "Адрес не отображается в Basic",
  },
  custom_1: { supported: false },
  custom_2: { supported: false },
  custom_3: { supported: false },
};

/**
 * Конфиг полей для Professional 58x40.
 * Лимит: 10 полей в блоке.
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
  size_color: {
    supported: true,
    maxChars: 32, // Размер + цвет суммарно
    warningHint: "Размер/цвет слишком длинные",
  },
  brand: {
    supported: true,
    maxChars: 30,
  },
  composition: {
    supported: false,
    warningHint: "Состав не отображается в Professional",
  },
  country: {
    supported: true,
    maxChars: 30,
  },
  manufacturer: {
    supported: true,
    maxChars: 39,
  },
  production_date: {
    supported: false,
    warningHint: "Дата производства не отображается в Professional",
  },
  importer: {
    supported: true,
    maxChars: 39,
  },
  certificate: {
    supported: true,
    maxChars: 19,
  },
  address: {
    supported: true,
    maxChars: 39,
  },
  custom_1: { supported: false },
  custom_2: { supported: false },
  custom_3: { supported: false },
};

/**
 * Конфиг полей для Extended 58x40.
 * Лимит: 12 полей в блоке. Кастомные строки поддерживаются!
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
  size_color: {
    supported: true,
    maxChars: 32, // Размер + цвет суммарно
    warningHint: "Размер/цвет слишком длинные",
  },
  brand: {
    supported: true,
    maxChars: 28,
  },
  composition: {
    supported: true,
    maxChars: 64,
    maxLines: 2,
  },
  country: {
    supported: true,
    maxChars: 28,
  },
  manufacturer: {
    supported: true,
    maxChars: 31,
  },
  production_date: {
    supported: false,
    warningHint: "Дата производства не отображается в Extended",
  },
  importer: {
    supported: false,
    warningHint: "Импортёр не отображается в Extended",
  },
  certificate: {
    supported: false,
    warningHint: "Сертификат не отображается в Extended",
  },
  address: {
    supported: true,
    maxChars: 31,
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
 * Поля, которые НЕ считаются в лимит текстового блока.
 *
 * Для Basic и Extended: ИНН находится ВВЕРХУ этикетки (отдельная строка),
 * он не занимает место в текстовом блоке.
 *
 * Для Professional: все поля в текстовом блоке, исключений нет.
 */
export function getFieldsExcludedFromLimit(
  layout: LabelLayout,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _size: LabelSize
): FieldId[] {
  if (layout === "basic" || layout === "extended") {
    // ИНН для Basic и Extended находится ВВЕРХУ этикетки (отдельная строка),
    // он не занимает место в текстовом блоке
    return ["inn"];
  }
  // Для Professional все поля в текстовом блоке
  return [];
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
 * Проверить, является ли поле объединённым size_color.
 * Такое поле имеет два инпута (размер и цвет) но один чекбокс.
 */
export function isSizeColorField(fieldId: FieldId): boolean {
  return fieldId === "size_color";
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

/**
 * Получить ВСЕ поля для отображения в списке.
 * 13 стандартных полей + 3 кастомных (только для Extended).
 * Все поля показываются, недоступные — серые.
 */
export function getAllFieldsForDisplay(layout: LabelLayout): FieldId[] {
  // 13 стандартных полей — показываются всегда
  const fields: FieldId[] = [...STANDARD_FIELDS];

  // Кастомные строки — только для Extended
  if (layout === "extended") {
    fields.push("custom_1", "custom_2", "custom_3");
  }

  return fields;
}
