/**
 * Функция рендеринга этикетки на Fabric.js canvas.
 *
 * Рендерит превью этикетки согласно конфигурации layout.
 * DataMatrix и штрихкод отображаются как placeholder-ы.
 */

import type { Canvas as FabricCanvas, FabricText, Rect, Line } from "fabric";
import {
  type LabelLayout,
  type LabelSize,
  LABEL_SIZES,
  getLayoutConfig,
  mmToPx,
  ptToPx,
  invertY,
} from "./label-config";

export interface LabelCanvasData {
  barcode: string;
  article?: string;
  size?: string;
  color?: string;
  name?: string;
  organization?: string;
  inn?: string;
  country?: string;
  composition?: string;
  address?: string;
  certificate?: string;
  productionDate?: string;
  importer?: string;
  manufacturer?: string;
  brand?: string;
}

export interface ShowFlags {
  showArticle?: boolean;
  showSizeColor?: boolean;
  showName?: boolean;
  showOrganization?: boolean;
  showInn?: boolean;
  showCountry?: boolean;
  showComposition?: boolean;
  showAddress?: boolean;
  showCertificate?: boolean;
  showProductionDate?: boolean;
  showImporter?: boolean;
  showManufacturer?: boolean;
  showBrand?: boolean;
  showChzCode?: boolean;
  showSerialNumber?: boolean;
}

export interface CustomLine {
  label: string;
  value: string;
}

/**
 * Рендерит этикетку на Fabric.js canvas.
 *
 * @param canvas - Fabric.Canvas объект
 * @param fabric - Fabric модуль (для создания объектов)
 * @param layout - Тип layout (basic, professional, extended)
 * @param size - Размер этикетки (58x30, 58x40, 58x60)
 * @param data - Данные для этикетки
 * @param showFlags - Флаги отображения полей
 * @param serialNumber - Серийный номер (опционально)
 * @param customLines - Кастомные строки для extended layout
 */
export function renderLabel(
  canvas: FabricCanvas,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fabric: any,
  layout: LabelLayout,
  size: LabelSize,
  data: LabelCanvasData,
  showFlags: ShowFlags,
  serialNumber?: number,
  customLines?: CustomLine[]
): void {
  // Очищаем canvas
  canvas.clear();

  // Устанавливаем белый фон
  canvas.backgroundColor = "#ffffff";

  // Получаем конфигурацию layout
  const config = getLayoutConfig(layout, size);
  if (!config) {
    // Если layout не поддерживает этот размер, показываем сообщение
    const text = new fabric.FabricText(
      `Layout "${layout}" не поддерживает размер ${size}`,
      {
        left: 10,
        top: 10,
        fontSize: 10,
        fill: "#666",
        fontFamily: "Arial",
        selectable: false,
        evented: false,
      }
    );
    canvas.add(text);
    canvas.renderAll();
    return;
  }

  // Размеры этикетки в мм
  const labelSize = LABEL_SIZES[size];
  const heightMm = labelSize.height;

  // Рендерим в зависимости от layout
  if (layout === "basic") {
    renderBasicLayout(canvas, fabric, config, data, showFlags, heightMm, serialNumber);
  } else if (layout === "professional") {
    renderProfessionalLayout(canvas, fabric, config, data, showFlags, heightMm);
  } else if (layout === "extended") {
    renderExtendedLayout(canvas, fabric, config, data, showFlags, heightMm, serialNumber, customLines);
  }

  canvas.renderAll();
}

/**
 * Рендерит BASIC layout.
 */
function renderBasicLayout(
  canvas: FabricCanvas,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fabric: any,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  config: any,
  data: LabelCanvasData,
  showFlags: ShowFlags,
  heightMm: number,
  serialNumber?: number
): void {
  const {
    showArticle = true,
    showSizeColor = true,
    showName = true,
    showOrganization = true,
    showInn = false,
    showCountry = false,
    showComposition = false,
    showChzCode = true,
    showSerialNumber = false,
  } = showFlags;

  // === DataMatrix placeholder (слева) ===
  const dm = config.datamatrix;
  drawDataMatrixPlaceholder(
    canvas,
    fabric,
    mmToPx(dm.x),
    mmToPx(invertY(dm.y + dm.size, heightMm)),
    mmToPx(dm.size)
  );

  // === Вертикальная линия-разделитель (если есть) ===
  if (config.divider) {
    const div = config.divider;
    drawVerticalLine(
      canvas,
      fabric,
      mmToPx(div.x),
      mmToPx(invertY(div.y_end, heightMm)),
      mmToPx(div.y_end - div.y_start),
      mmToPx(div.width || 0.3)
    );
  }

  // === Код ЧЗ текстом ===
  if (showChzCode) {
    const chzCodeExample = "0104600439931256";
    const chzCodeLine2 = "21ABC123def456g";

    if (config.chz_code_text) {
      const chz = config.chz_code_text;
      drawText(
        canvas,
        fabric,
        chzCodeExample,
        mmToPx(chz.x),
        mmToPx(invertY(chz.y, heightMm)),
        ptToPx(chz.size),
        false,
        false,
        "#666"
      );
    }
    if (config.chz_code_text_2) {
      const chz2 = config.chz_code_text_2;
      drawText(
        canvas,
        fabric,
        chzCodeLine2,
        mmToPx(chz2.x),
        mmToPx(invertY(chz2.y, heightMm)),
        ptToPx(chz2.size),
        false,
        false,
        "#666"
      );
    }
  }

  // === Логотип "ЧЕСТНЫЙ ЗНАК" ===
  if (config.chz_logo) {
    const logo = config.chz_logo;
    drawText(
      canvas,
      fabric,
      "ЧЕСТНЫЙ ЗНАК",
      mmToPx(logo.x),
      mmToPx(invertY(logo.y + logo.height / 2, heightMm)),
      mmToPx(logo.height * 0.4),
      false,
      true,
      "#333"
    );
  }

  // === Логотип EAC ===
  if (config.eac_logo) {
    const eac = config.eac_logo;
    drawText(
      canvas,
      fabric,
      "EAC",
      mmToPx(eac.x),
      mmToPx(invertY(eac.y + eac.height / 2, heightMm)),
      mmToPx(eac.height * 0.6),
      false,
      true,
      "#333"
    );
  }

  // === Серийный номер ===
  if (showSerialNumber && serialNumber && config.serial_number) {
    const sn = config.serial_number;
    drawText(
      canvas,
      fabric,
      `# ${serialNumber}`,
      mmToPx(sn.x),
      mmToPx(invertY(sn.y, heightMm)),
      ptToPx(sn.size),
      false,
      sn.bold || false
    );
  }

  // === ИНН ===
  if (showInn && data.inn && config.inn) {
    const inn = config.inn;
    drawText(
      canvas,
      fabric,
      `ИНН: ${data.inn}`,
      mmToPx(inn.x),
      mmToPx(invertY(inn.y, heightMm)),
      ptToPx(inn.size),
      inn.centered || false,
      inn.bold || false
    );
  }

  // === Организация ===
  if (showOrganization && data.organization && config.organization) {
    const org = config.organization;
    drawText(
      canvas,
      fabric,
      data.organization,
      mmToPx(org.x),
      mmToPx(invertY(org.y, heightMm)),
      ptToPx(org.size),
      org.centered || false,
      org.bold || false
    );
  }

  // === Название товара ===
  if (showName && data.name && config.name) {
    const nm = config.name;
    // Упрощенно: одна строка (в реальности может быть две)
    drawText(
      canvas,
      fabric,
      data.name,
      mmToPx(nm.x),
      mmToPx(invertY(nm.y, heightMm)),
      ptToPx(nm.size),
      nm.centered || false,
      nm.bold || false
    );
  }

  // === Цвет ===
  if (showSizeColor && data.color && config.color) {
    const clr = config.color;
    drawText(
      canvas,
      fabric,
      `цвет: ${data.color}`,
      mmToPx(clr.x),
      mmToPx(invertY(clr.y, heightMm)),
      ptToPx(clr.size),
      clr.centered || false,
      clr.bold || false
    );
  }

  // === Размер ===
  if (showSizeColor && data.size && config.size_field) {
    const sz = config.size_field;
    drawText(
      canvas,
      fabric,
      `размер: ${data.size}`,
      mmToPx(sz.x),
      mmToPx(invertY(sz.y, heightMm)),
      ptToPx(sz.size),
      sz.centered || false,
      sz.bold || false
    );
  }

  // === Артикул ===
  if (showArticle && data.article && config.article) {
    const art = config.article;
    drawText(
      canvas,
      fabric,
      `арт.: ${data.article}`,
      mmToPx(art.x),
      mmToPx(invertY(art.y, heightMm)),
      ptToPx(art.size),
      art.centered || false,
      art.bold || false
    );
  }

  // === Страна ===
  if (showCountry && data.country && config.country) {
    const cnt = config.country;
    drawText(
      canvas,
      fabric,
      `Страна: ${data.country}`,
      mmToPx(cnt.x),
      mmToPx(invertY(cnt.y, heightMm)),
      ptToPx(cnt.size),
      cnt.centered || false,
      false
    );
  }

  // === Состав ===
  if (showComposition && data.composition && config.composition) {
    const comp = config.composition;
    drawText(
      canvas,
      fabric,
      `Состав: ${data.composition}`,
      mmToPx(comp.x),
      mmToPx(invertY(comp.y, heightMm)),
      ptToPx(comp.size),
      comp.centered || false,
      false
    );
  }

  // === Штрихкод WB ===
  const bc = config.barcode;
  drawBarcodePlaceholder(
    canvas,
    fabric,
    mmToPx(bc.x),
    mmToPx(invertY(bc.y + bc.height, heightMm)),
    mmToPx(bc.width),
    mmToPx(bc.height)
  );

  // === Номер штрихкода ===
  const bcText = config.barcode_text;
  drawText(
    canvas,
    fabric,
    data.barcode,
    mmToPx(bcText.x),
    mmToPx(invertY(bcText.y, heightMm)),
    ptToPx(bcText.size),
    bcText.centered || false,
    bcText.bold || false,
    "#333"
  );
}

/**
 * Рендерит PROFESSIONAL layout.
 */
function renderProfessionalLayout(
  canvas: FabricCanvas,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fabric: any,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  config: any,
  data: LabelCanvasData,
  showFlags: ShowFlags,
  heightMm: number
): void {
  const {
    showArticle = true,
    showSizeColor = true,
    showName = true,
    showCountry = true,
    showBrand = false,
    showImporter = false,
    showManufacturer = false,
    showAddress = false,
    showProductionDate = false,
    showCertificate = false,
    showChzCode = true,
  } = showFlags;

  // === Вертикальная линия-разделитель ===
  if (config.divider) {
    const div = config.divider;
    drawVerticalLine(
      canvas,
      fabric,
      mmToPx(div.x),
      mmToPx(invertY(div.y_end, heightMm)),
      mmToPx(div.y_end - div.y_start),
      mmToPx(div.width || 0.3)
    );
  }

  // === EAC label ===
  if (config.eac_label) {
    const eac = config.eac_label;
    drawText(
      canvas,
      fabric,
      eac.text || "EAC",
      mmToPx(eac.x),
      mmToPx(invertY(eac.y, heightMm)),
      ptToPx(eac.size),
      false,
      true
    );
  }

  // === "ЧЕСТНЫЙ ЗНАК" ===
  if (config.chz_logo) {
    const chz = config.chz_logo;
    drawText(
      canvas,
      fabric,
      chz.text || "ЧЕСТНЫЙ",
      mmToPx(chz.x),
      mmToPx(invertY(chz.y, heightMm)),
      ptToPx(chz.size),
      false,
      true
    );
  }

  // === DataMatrix ===
  const dm = config.datamatrix;
  drawDataMatrixPlaceholder(
    canvas,
    fabric,
    mmToPx(dm.x),
    mmToPx(invertY(dm.y + dm.size, heightMm)),
    mmToPx(dm.size)
  );

  // === Код ЧЗ текстом ===
  if (showChzCode) {
    const chzCodeExample = "0104600439931256";
    const chzCodeLine2 = "21ABC123def456g";

    if (config.chz_code_text) {
      const chzT = config.chz_code_text;
      drawText(
        canvas,
        fabric,
        chzCodeExample.slice(0, 14),
        mmToPx(chzT.x),
        mmToPx(invertY(chzT.y, heightMm)),
        ptToPx(chzT.size),
        false,
        false,
        "#666"
      );
    }
    if (config.chz_code_text_2) {
      const chzT2 = config.chz_code_text_2;
      drawText(
        canvas,
        fabric,
        chzCodeLine2.slice(0, 14),
        mmToPx(chzT2.x),
        mmToPx(invertY(chzT2.y, heightMm)),
        ptToPx(chzT2.size),
        false,
        false,
        "#666"
      );
    }
  }

  // === Страна ===
  if (showCountry && config.country) {
    const cnt = config.country;
    drawText(
      canvas,
      fabric,
      `Сделано в ${data.country || "России"}`,
      mmToPx(cnt.x),
      mmToPx(invertY(cnt.y, heightMm)),
      ptToPx(cnt.size),
      false,
      false
    );
  }

  // === Штрихкод ===
  const bc = config.barcode;
  drawBarcodePlaceholder(
    canvas,
    fabric,
    mmToPx(bc.x),
    mmToPx(invertY(bc.y + bc.height, heightMm)),
    mmToPx(bc.width),
    mmToPx(bc.height)
  );

  const bcText = config.barcode_text;
  drawText(
    canvas,
    fabric,
    data.barcode,
    mmToPx(bcText.x),
    mmToPx(invertY(bcText.y, heightMm)),
    ptToPx(bcText.size),
    bcText.centered || false,
    bcText.bold || false,
    "#333"
  );

  // === Описание (название) ===
  if (showName && data.name && config.description) {
    const desc = config.description;
    drawText(
      canvas,
      fabric,
      data.name,
      mmToPx(desc.x),
      mmToPx(invertY(desc.y, heightMm)),
      ptToPx(desc.size),
      desc.centered || false,
      desc.bold || false
    );
  }

  // === Артикул ===
  if (showArticle && data.article && config.article) {
    const art = config.article;
    drawText(
      canvas,
      fabric,
      `Артикул: ${data.article}`,
      mmToPx(art.x),
      mmToPx(invertY(art.y, heightMm)),
      ptToPx(art.size),
      false,
      art.label_bold || false
    );
  }

  // === Бренд ===
  if (showBrand && data.brand && config.brand) {
    const br = config.brand;
    drawText(
      canvas,
      fabric,
      `Бренд: ${data.brand}`,
      mmToPx(br.x),
      mmToPx(invertY(br.y, heightMm)),
      ptToPx(br.size),
      false,
      br.label_bold || false
    );
  }

  // === Размер / Цвет ===
  if (showSizeColor && config.size_color) {
    const sc = config.size_color;
    const parts = [];
    if (data.size) parts.push(`Размер: ${data.size}`);
    if (data.color) parts.push(`Цвет: ${data.color}`);
    if (parts.length > 0) {
      drawText(
        canvas,
        fabric,
        parts.join("  "),
        mmToPx(sc.x),
        mmToPx(invertY(sc.y, heightMm)),
        ptToPx(sc.size),
        false,
        sc.label_bold || false
      );
    }
  }

  // === Импортер ===
  if (showImporter && config.importer) {
    const imp = config.importer;
    drawText(
      canvas,
      fabric,
      `Импортер: ${data.importer || data.organization || "ООО Компания"}`,
      mmToPx(imp.x),
      mmToPx(invertY(imp.y, heightMm)),
      ptToPx(imp.size),
      false,
      false
    );
  }

  // === Производитель ===
  if (showManufacturer && config.manufacturer) {
    const mfr = config.manufacturer;
    drawText(
      canvas,
      fabric,
      `Производитель: ${data.manufacturer || data.organization || "ООО Компания"}`,
      mmToPx(mfr.x),
      mmToPx(invertY(mfr.y, heightMm)),
      ptToPx(mfr.size),
      false,
      false
    );
  }

  // === Адрес ===
  if (showAddress && data.address && config.address) {
    const addr = config.address;
    drawText(
      canvas,
      fabric,
      `Адрес: ${data.address}`,
      mmToPx(addr.x),
      mmToPx(invertY(addr.y, heightMm)),
      ptToPx(addr.size),
      false,
      false
    );
  }

  // === Дата производства ===
  if (showProductionDate && data.productionDate && config.production_date) {
    const pd = config.production_date;
    drawText(
      canvas,
      fabric,
      `Дата: ${data.productionDate}`,
      mmToPx(pd.x),
      mmToPx(invertY(pd.y, heightMm)),
      ptToPx(pd.size),
      false,
      false
    );
  }

  // === Сертификат ===
  if (showCertificate && data.certificate && config.certificate) {
    const cert = config.certificate;
    drawText(
      canvas,
      fabric,
      `Серт: ${data.certificate}`,
      mmToPx(cert.x),
      mmToPx(invertY(cert.y, heightMm)),
      ptToPx(cert.size),
      false,
      false
    );
  }
}

/**
 * Рендерит EXTENDED layout.
 */
function renderExtendedLayout(
  canvas: FabricCanvas,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fabric: any,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  config: any,
  data: LabelCanvasData,
  showFlags: ShowFlags,
  heightMm: number,
  serialNumber?: number,
  customLines?: CustomLine[]
): void {
  const { showChzCode = true, showSerialNumber = false } = showFlags;

  // === DataMatrix ===
  const dm = config.datamatrix;
  drawDataMatrixPlaceholder(
    canvas,
    fabric,
    mmToPx(dm.x),
    mmToPx(invertY(dm.y + dm.size, heightMm)),
    mmToPx(dm.size)
  );

  // === Код ЧЗ текстом ===
  if (showChzCode) {
    const chzCodeExample = "0104600439931256";
    const chzCodeLine2 = "21ABC123def456g";

    if (config.chz_code_text) {
      const chz = config.chz_code_text;
      drawText(
        canvas,
        fabric,
        chzCodeExample,
        mmToPx(chz.x),
        mmToPx(invertY(chz.y, heightMm)),
        ptToPx(chz.size),
        false,
        false,
        "#666"
      );
    }
    if (config.chz_code_text_2) {
      const chz2 = config.chz_code_text_2;
      drawText(
        canvas,
        fabric,
        chzCodeLine2,
        mmToPx(chz2.x),
        mmToPx(invertY(chz2.y, heightMm)),
        ptToPx(chz2.size),
        false,
        false,
        "#666"
      );
    }
  }

  // === Логотипы ===
  if (config.chz_logo) {
    const logo = config.chz_logo;
    drawText(
      canvas,
      fabric,
      "ЧЕСТНЫЙ ЗНАК",
      mmToPx(logo.x),
      mmToPx(invertY(logo.y + logo.height / 2, heightMm)),
      mmToPx(logo.height * 0.4),
      false,
      true,
      "#333"
    );
  }

  if (config.eac_logo) {
    const eac = config.eac_logo;
    drawText(
      canvas,
      fabric,
      "EAC",
      mmToPx(eac.x),
      mmToPx(invertY(eac.y + eac.height / 2, heightMm)),
      mmToPx(eac.height * 0.6),
      false,
      true,
      "#333"
    );
  }

  // === Серийный номер ===
  if (showSerialNumber && serialNumber && config.serial_number) {
    const sn = config.serial_number;
    drawText(
      canvas,
      fabric,
      `# ${serialNumber}`,
      mmToPx(sn.x),
      mmToPx(invertY(sn.y, heightMm)),
      ptToPx(sn.size),
      false,
      sn.bold || false
    );
  }

  // === ИНН ===
  if (data.inn && config.inn) {
    const inn = config.inn;
    drawText(
      canvas,
      fabric,
      `ИНН: ${data.inn}`,
      mmToPx(inn.x),
      mmToPx(invertY(inn.y, heightMm)),
      ptToPx(inn.size),
      inn.centered || false,
      inn.bold || false
    );
  }

  // === Адрес ===
  if (data.address && config.address) {
    const addr = config.address;
    drawText(
      canvas,
      fabric,
      `Адрес: ${data.address}`,
      mmToPx(addr.x),
      mmToPx(invertY(addr.y, heightMm)),
      ptToPx(addr.size),
      addr.centered || false,
      addr.bold || false
    );
  }

  // === Текстовый блок с кастомными строками ===
  if (config.text_block_start_y && config.text_block_x) {
    const blockX = config.text_block_x;
    let currentY = config.text_block_start_y;
    const fontSize = config.text_block_size || 5;
    const lineHeight = config.text_block_line_height || 1.8;

    // Стандартные поля
    const lines: string[] = [];
    if (data.name) lines.push(`Название: ${data.name}`);
    if (data.composition) lines.push(`Состав: ${data.composition}`);
    if (data.article) lines.push(`Артикул: ${data.article}`);
    if (data.size || data.color) {
      const parts = [];
      if (data.size) parts.push(`Размер: ${data.size}`);
      if (data.color) parts.push(`Цвет: ${data.color}`);
      lines.push(parts.join(", "));
    }
    if (data.manufacturer) lines.push(`Производитель: ${data.manufacturer}`);
    if (data.productionDate) lines.push(`Дата: ${data.productionDate}`);

    // Кастомные строки
    if (customLines) {
      for (const line of customLines) {
        lines.push(`${line.label}: ${line.value}`);
      }
    }

    // Рендерим строки
    for (const line of lines) {
      drawText(
        canvas,
        fabric,
        line,
        mmToPx(blockX),
        mmToPx(invertY(currentY, heightMm)),
        ptToPx(fontSize),
        false,
        false
      );
      currentY -= lineHeight;
    }
  }

  // === Штрихкод ===
  const bc = config.barcode;
  drawBarcodePlaceholder(
    canvas,
    fabric,
    mmToPx(bc.x),
    mmToPx(invertY(bc.y + bc.height, heightMm)),
    mmToPx(bc.width),
    mmToPx(bc.height)
  );

  const bcText = config.barcode_text;
  drawText(
    canvas,
    fabric,
    data.barcode,
    mmToPx(bcText.x),
    mmToPx(invertY(bcText.y, heightMm)),
    ptToPx(bcText.size),
    bcText.centered || false,
    bcText.bold || false,
    "#333"
  );
}

// ============================================
// Вспомогательные функции отрисовки
// ============================================

/**
 * Рисует текст.
 */
function drawText(
  canvas: FabricCanvas,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fabric: any,
  text: string,
  x: number,
  y: number,
  fontSize: number,
  centered: boolean = false,
  bold: boolean = false,
  fill: string = "#000"
): FabricText {
  const textObj = new fabric.FabricText(text, {
    left: x,
    top: y,
    fontSize: fontSize,
    fontFamily: "Arial",
    fontWeight: bold ? "bold" : "normal",
    fill: fill,
    selectable: false,
    evented: false,
    originX: centered ? "center" : "left",
    originY: "top",
  });
  canvas.add(textObj);
  return textObj;
}

/**
 * Рисует placeholder для DataMatrix (черно-белый паттерн).
 */
function drawDataMatrixPlaceholder(
  canvas: FabricCanvas,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fabric: any,
  x: number,
  y: number,
  size: number
): void {
  // Белый фон
  const bg = new fabric.Rect({
    left: x,
    top: y,
    width: size,
    height: size,
    fill: "#ffffff",
    stroke: "#ccc",
    strokeWidth: 1,
    selectable: false,
    evented: false,
  }) as Rect;
  canvas.add(bg);

  // Сетка 8x8 для имитации DataMatrix
  const cellSize = size / 8;
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      // Паттерн похожий на реальный DataMatrix
      const fill =
        row === 0 || col === 0 || (row + col) % 3 === 0 ? "#000" : "#fff";
      if (fill === "#000") {
        const cell = new fabric.Rect({
          left: x + col * cellSize,
          top: y + row * cellSize,
          width: cellSize,
          height: cellSize,
          fill: fill,
          selectable: false,
          evented: false,
        }) as Rect;
        canvas.add(cell);
      }
    }
  }
}

/**
 * Рисует placeholder для штрихкода (вертикальные линии).
 */
function drawBarcodePlaceholder(
  canvas: FabricCanvas,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fabric: any,
  x: number,
  y: number,
  width: number,
  height: number
): void {
  // Белый фон
  const bg = new fabric.Rect({
    left: x,
    top: y,
    width: width,
    height: height,
    fill: "#ffffff",
    selectable: false,
    evented: false,
  }) as Rect;
  canvas.add(bg);

  // Паттерн вертикальных линий
  const pattern = [1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1];
  const barWidth = width / pattern.length;

  for (let i = 0; i < pattern.length; i++) {
    const barHeight = pattern[i] ? height : height * 0.8;
    const bar = new fabric.Rect({
      left: x + i * barWidth,
      top: y + (height - barHeight),
      width: barWidth * 0.8,
      height: barHeight,
      fill: "#000",
      opacity: pattern[i] ? 1 : 0.3,
      selectable: false,
      evented: false,
    }) as Rect;
    canvas.add(bar);
  }
}

/**
 * Рисует вертикальную линию-разделитель.
 */
function drawVerticalLine(
  canvas: FabricCanvas,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fabric: any,
  x: number,
  y: number,
  height: number,
  width: number
): void {
  const line = new fabric.Line([x, y, x, y + height], {
    stroke: "#000",
    strokeWidth: width,
    selectable: false,
    evented: false,
  }) as Line;
  canvas.add(line);
}
