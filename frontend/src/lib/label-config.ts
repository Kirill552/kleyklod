/**
 * Конфигурация layouts для этикеток.
 *
 * СИНХРОНИЗИРОВАНО с backend/app/services/label_generator.py
 *
 * Все координаты в мм, Y от нижнего края (ReportLab convention).
 * Для canvas координаты конвертируются в пиксели и Y инвертируется.
 */

export type LabelLayout = "basic" | "professional" | "extended";
export type LabelSize = "58x30" | "58x40" | "58x60";

// Размеры этикеток в мм
export const LABEL_SIZES: Record<LabelSize, { width: number; height: number }> = {
  "58x30": { width: 58, height: 30 },
  "58x40": { width: 58, height: 40 },
  "58x60": { width: 58, height: 60 },
};

// DPI для конвертации мм -> пиксели
export const DPI = 203;
export const MM_TO_PX = DPI / 25.4; // ~8 px/mm

interface ZoneConfig {
  x: number;
  y?: number;
  size?: number;
  width?: number;
  height?: number;
  max_width?: number;
  centered?: boolean;
  bold?: boolean;
  text?: string;
  y_start?: number;
  y_end?: number;
  label_bold?: boolean;
}

interface LayoutConfig {
  datamatrix: ZoneConfig;
  chz_code_text?: ZoneConfig;
  chz_code_text_2?: ZoneConfig;
  chz_logo?: ZoneConfig;
  eac_logo?: ZoneConfig;
  eac_label?: ZoneConfig;
  serial_number?: ZoneConfig;
  inn?: ZoneConfig;
  organization?: ZoneConfig;
  address?: ZoneConfig;
  name?: ZoneConfig;
  name_2?: ZoneConfig;
  color?: ZoneConfig;
  size_field?: ZoneConfig;
  article?: ZoneConfig;
  country?: ZoneConfig;
  composition?: ZoneConfig;
  barcode: ZoneConfig;
  barcode_text: ZoneConfig;
  divider?: ZoneConfig;
  description?: ZoneConfig;
  description_2?: ZoneConfig;
  brand?: ZoneConfig;
  size_color?: ZoneConfig;
  importer?: ZoneConfig;
  manufacturer?: ZoneConfig;
  production_date?: ZoneConfig;
  certificate?: ZoneConfig;
  // Extended layout
  text_block_start_y?: number;
  text_block_x?: number;
  text_block_size?: number;
  text_block_line_height?: number;
  text_block_max_width?: number;
}

// Конфигурация из backend/app/services/label_generator.py
export const LAYOUTS: Record<LabelLayout, Partial<Record<LabelSize, LayoutConfig>>> = {
  basic: {
    "58x40": {
      datamatrix: { x: 1.5, y: 16.5, size: 22 },
      chz_code_text: { x: 1.5, y: 12.5, size: 4, max_width: 22 },
      chz_code_text_2: { x: 1.5, y: 10.8, size: 4, max_width: 22 },
      chz_logo: { x: 1.5, y: 5, width: 13, height: 4.0 },
      eac_logo: { x: 1.5, y: 1.5, width: 7, height: 3 },
      serial_number: { x: 6, y: 1.5, size: 7, bold: false },
      inn: { x: 40, y: 37.3, size: 3.5, max_width: 32, centered: true, bold: true },
      organization: { x: 40, y: 35.8, size: 3.5, max_width: 32, centered: true, bold: true },
      name: { x: 40, y: 29, size: 8.5, max_width: 33, centered: true, bold: true },
      name_2: { x: 40, y: 25.5, size: 8.5, max_width: 33, centered: true, bold: true },
      color: { x: 40, y: 18.5, size: 4.5, max_width: 32, centered: true, bold: true },
      size_field: { x: 40, y: 16.4, size: 4.5, max_width: 32, centered: true, bold: true },
      article: { x: 40, y: 14.3, size: 4.5, max_width: 32, centered: true, bold: true },
      barcode: { x: 20, y: 3.5, width: 52, height: 9 },
      barcode_text: { x: 39, y: 1.5, size: 4.5, centered: true, bold: true },
    },
    "58x30": {
      datamatrix: { x: 1.5, y: 6.5, size: 22 },
      divider: { x: 26.5, y_start: 1.5, y_end: 28.5, width: 0.8 },
      chz_code_text: { x: 1.5, y: 4.5, size: 3, max_width: 22 },
      eac_logo: { x: 1.5, y: 1.5, width: 2.9, height: 2.5 },
      chz_logo: { x: 4.9, y: 1.5, width: 7.2, height: 2.5 },
      serial_number: { x: 12.6, y: 2, size: 5, bold: false },
      inn: { x: 43, y: 27.3, size: 4, max_width: 32, centered: true, bold: true },
      organization: { x: 43, y: 25.8, size: 4, max_width: 32, centered: true, bold: true },
      name: { x: 43, y: 21, size: 6, max_width: 33, centered: true, bold: true },
      name_2: { x: 43, y: 18.5, size: 6, max_width: 33, centered: true, bold: true },
      color: { x: 43, y: 14.3, size: 4, max_width: 32, centered: true, bold: true },
      size_field: { x: 43, y: 12.4, size: 4, max_width: 32, centered: true, bold: true },
      article: { x: 43, y: 10.5, size: 4, max_width: 32, centered: true, bold: true },
      barcode: { x: 30, y: 3, width: 36, height: 7 },
      barcode_text: { x: 43, y: 1.5, size: 4, centered: true, bold: true },
    },
    "58x60": {
      datamatrix: { x: 1.5, y: 36.5, size: 22 },
      chz_code_text: { x: 1.5, y: 32.5, size: 6, max_width: 22 },
      chz_code_text_2: { x: 1.5, y: 30.8, size: 6, max_width: 22 },
      chz_logo: { x: 1.5, y: 7.5, width: 15, height: 6 },
      eac_logo: { x: 1.5, y: 1.5, width: 9, height: 5 },
      serial_number: { x: 7.5, y: 1.5, size: 7, bold: false },
      country: { x: 1.5, y: 18, size: 4, max_width: 22 },
      composition: { x: 1.5, y: 12, size: 3.5, max_width: 22 },
      inn: { x: 40, y: 57.3, size: 4.5, max_width: 32, centered: true, bold: true },
      organization: { x: 40, y: 55.8, size: 4.5, max_width: 32, centered: true, bold: true },
      name: { x: 40, y: 39.5, size: 9.5, max_width: 33, centered: true, bold: true },
      name_2: { x: 40, y: 36, size: 9.5, max_width: 33, centered: true, bold: true },
      color: { x: 40, y: 18.7, size: 6, max_width: 32, centered: true, bold: true },
      size_field: { x: 40, y: 16.1, size: 6, max_width: 32, centered: true, bold: true },
      article: { x: 40, y: 13.5, size: 6, max_width: 32, centered: true, bold: true },
      barcode: { x: 20, y: 3.5, width: 52, height: 9 },
      barcode_text: { x: 39, y: 1.5, size: 4.5, centered: true, bold: true },
    },
  },
  extended: {
    "58x40": {
      datamatrix: { x: 1.5, y: 16.5, size: 22 },
      chz_code_text: { x: 1.5, y: 12.5, size: 4, max_width: 22 },
      chz_code_text_2: { x: 1.5, y: 10.8, size: 4, max_width: 22 },
      chz_logo: { x: 1.5, y: 5, width: 13, height: 4.0 },
      eac_logo: { x: 1.5, y: 1.5, width: 7, height: 3 },
      serial_number: { x: 6, y: 1.5, size: 7, bold: false },
      inn: { x: 40, y: 37.3, size: 3.5, max_width: 31, bold: true, centered: true },
      address: { x: 40, y: 35.8, size: 3.5, max_width: 31, bold: true, centered: true },
      text_block_start_y: 32.8,
      text_block_x: 25.5,
      text_block_size: 5,
      text_block_line_height: 1.8,
      text_block_max_width: 31,
      barcode: { x: 20, y: 3.5, width: 52, height: 9 },
      barcode_text: { x: 39, y: 1.5, size: 4.5, centered: true, bold: true },
    },
  },
  professional: {
    "58x40": {
      divider: { x: 16.5, y_start: 1, y_end: 39, width: 0.5 },
      eac_label: { x: 1.5, y: 36, size: 5, text: "EAC" },
      chz_logo: { x: 7, y: 36, size: 3, text: "ЧЕСТНЫЙ" },
      datamatrix: { x: 1.5, y: 19, size: 14 },
      chz_code_text: { x: 1.5, y: 16, size: 2.5, max_width: 14 },
      chz_code_text_2: { x: 1.5, y: 14, size: 2.5, max_width: 14 },
      country: { x: 1.5, y: 2, size: 3, max_width: 14 },
      barcode: { x: 18, y: 33, width: 39, height: 6 },
      barcode_text: { x: 37.5, y: 31, size: 3.5, centered: true },
      description: { x: 37.5, y: 27, size: 4, max_width: 39, centered: true, bold: true },
      description_2: { x: 37.5, y: 24, size: 4, max_width: 39, centered: true, bold: true },
      article: { x: 18, y: 20, size: 3, max_width: 39, label_bold: true },
      brand: { x: 18, y: 17.5, size: 3, max_width: 39, label_bold: true },
      size_color: { x: 18, y: 15, size: 3, max_width: 39, label_bold: true },
      importer: { x: 18, y: 12, size: 2.5, max_width: 39, label_bold: false },
      manufacturer: { x: 18, y: 9.5, size: 2.5, max_width: 39, label_bold: false },
      address: { x: 18, y: 7, size: 2.5, max_width: 39, label_bold: false },
      production_date: { x: 18, y: 4, size: 2.5, max_width: 19, label_bold: false },
      certificate: { x: 38, y: 4, size: 2.5, max_width: 19, label_bold: false },
    },
    "58x60": {
      divider: { x: 19.5, y_start: 1, y_end: 59, width: 0.5 },
      eac_label: { x: 1.5, y: 56, size: 6, text: "EAC" },
      chz_logo: { x: 8, y: 56, size: 4, text: "ЧЕСТНЫЙ" },
      datamatrix: { x: 1.5, y: 35, size: 17 },
      chz_code_text: { x: 1.5, y: 31, size: 2.5, max_width: 17 },
      chz_code_text_2: { x: 1.5, y: 28.5, size: 2.5, max_width: 17 },
      country: { x: 1.5, y: 2, size: 3.5, max_width: 17 },
      barcode: { x: 21, y: 52, width: 36, height: 7 },
      barcode_text: { x: 39, y: 50, size: 4, centered: true },
      description: { x: 39, y: 45, size: 4.5, max_width: 36, centered: true, bold: true },
      description_2: { x: 39, y: 41, size: 4.5, max_width: 36, centered: true, bold: true },
      article: { x: 21, y: 36, size: 3.5, max_width: 36, label_bold: true },
      brand: { x: 21, y: 32.5, size: 3.5, max_width: 36, label_bold: true },
      size_color: { x: 21, y: 29, size: 3.5, max_width: 36, label_bold: true },
      importer: { x: 21, y: 24, size: 3, max_width: 36, label_bold: false },
      manufacturer: { x: 21, y: 20, size: 3, max_width: 36, label_bold: false },
      address: { x: 21, y: 16, size: 3, max_width: 36, label_bold: false },
      production_date: { x: 21, y: 8, size: 3, max_width: 36, label_bold: false },
      certificate: { x: 21, y: 4, size: 3, max_width: 36, label_bold: false },
    },
  },
};

/**
 * Получить конфигурацию layout для указанного размера.
 * Если размер не поддерживается layout, возвращает null.
 */
export function getLayoutConfig(
  layout: LabelLayout,
  size: LabelSize
): LayoutConfig | null {
  const layoutConfigs = LAYOUTS[layout];
  if (!layoutConfigs) return null;

  const config = layoutConfigs[size];
  if (!config) return null;

  return config;
}

/**
 * Конвертирует координаты из мм в пиксели.
 * Y инвертируется (в PDF Y от низа, в canvas Y от верха).
 */
export function mmToPx(mm: number): number {
  return mm * MM_TO_PX;
}

/**
 * Инвертирует Y координату для canvas (PDF Y от низа -> canvas Y от верха).
 */
export function invertY(y: number, labelHeight: number): number {
  return labelHeight - y;
}
