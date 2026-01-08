"use client";

/**
 * Превью этикетки с выбранным шаблоном.
 *
 * СИНХРОНИЗИРОВАНО с backend/app/services/label_generator.py
 *
 * Шаблоны:
 * - Basic: DataMatrix слева, справа ИНН/организация/название/характеристики, внизу справа штрихкод WB
 * - Professional: двухколоночный - слева EAC/ЧЗ/DataMatrix/страна, справа штрихкод/описание/реквизиты
 */

export type LabelLayout = "basic" | "professional";

export interface LabelPreviewData {
  barcode: string;
  article?: string;
  size?: string;
  color?: string;
  name?: string;
  organization?: string;
  // Дополнительные поля
  country?: string;
  composition?: string;
  inn?: string;
  address?: string;
  certificate?: string;
  productionDate?: string;
  importer?: string;
  manufacturer?: string;
  brand?: string;
}

interface LabelPreviewProps {
  data: LabelPreviewData;
  layout: LabelLayout;
  showArticle: boolean;
  showSizeColor: boolean;
  showName: boolean;
  showOrganization?: boolean;
  showCountry?: boolean;
  showComposition?: boolean;
  // Флаги для шаблонов
  showInn?: boolean;
  showAddress?: boolean;
  showCertificate?: boolean;
  showProductionDate?: boolean;
  showImporter?: boolean;
  showManufacturer?: boolean;
  showBrand?: boolean;
  showChzCode?: boolean;
  className?: string;
}

/**
 * DataMatrix placeholder (SVG квадрат с паттерном).
 */
function DataMatrixPlaceholder({ size = 40 }: { size?: number }) {
  return (
    <div
      className="bg-white flex items-center justify-center flex-shrink-0"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} viewBox="0 0 24 24">
        <rect x="0" y="0" width="24" height="24" fill="white" />
        {/* Имитация DataMatrix паттерна */}
        {[...Array(8)].map((_, row) =>
          [...Array(8)].map((_, col) => {
            // Паттерн похожий на реальный DataMatrix
            const fill =
              (row === 0 || col === 0 || (row + col) % 3 === 0) &&
              !(row === 7 && col === 7)
                ? "#000"
                : "white";
            return (
              <rect
                key={`${row}-${col}`}
                x={col * 3}
                y={row * 3}
                width="3"
                height="3"
                fill={fill}
              />
            );
          })
        )}
      </svg>
    </div>
  );
}

/**
 * Barcode placeholder (вертикальные линии EAN-13 style).
 */
function BarcodePlaceholder({
  width = 60,
  height = 24,
}: {
  width?: number;
  height?: number;
}) {
  // Паттерн похожий на EAN-13
  const pattern = [1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1];
  return (
    <div
      className="bg-white flex items-end justify-center"
      style={{ width, height }}
    >
      <svg width={width * 0.9} height={height} viewBox="0 0 50 20">
        {pattern.map((filled, i) => (
          <rect
            key={i}
            x={i * 2.5}
            y={0}
            width={2}
            height={filled ? 20 : 16}
            fill={filled ? "#000" : "#000"}
            opacity={filled ? 1 : 0.3}
          />
        ))}
      </svg>
    </div>
  );
}

export function LabelPreview({
  data,
  layout,
  showArticle,
  showSizeColor,
  showName,
  showOrganization = true,
  showCountry = false,
  // showComposition пока не используется, оставлен в интерфейсе для будущего
  showInn = false,
  showAddress = false,
  showCertificate = false,
  showProductionDate = false,
  showImporter = false,
  showManufacturer = false,
  showBrand = false,
  showChzCode = true,
  className,
}: LabelPreviewProps) {
  // Пример кода ЧЗ для превью
  const chzCodeExample = "0104600439931256";
  const chzCodeLine2 = "21ABC123def456g";

  // ============================================
  // BASIC Layout
  // Соответствует backend BASIC 58x40:
  // - Левая колонка: DataMatrix, код ЧЗ, "ЧЕСТНЫЙ ЗНАК", EAC
  // - Правая колонка: ИНН, организация, название, цвет, размер, артикул, штрихкод WB
  // ============================================
  if (layout === "basic") {
    return (
      <div
        className={`aspect-[58/40] bg-white border-2 border-warm-gray-300 rounded p-1.5 flex shadow-sm ${className || ""}`}
        style={{ minHeight: 80 }}
      >
        {/* === ЛЕВАЯ КОЛОНКА: DataMatrix + код ЧЗ + метки === */}
        <div className="flex flex-col items-start justify-between mr-1.5 flex-shrink-0" style={{ width: '38%' }}>
          {/* DataMatrix сверху */}
          <DataMatrixPlaceholder size={36} />

          {/* Код ЧЗ текстом (две строки) */}
          {showChzCode && (
            <div className="mt-0.5 w-full">
              <p className="text-[4px] text-warm-gray-600 font-mono leading-tight truncate">
                {chzCodeExample}
              </p>
              <p className="text-[4px] text-warm-gray-600 font-mono leading-tight truncate">
                {chzCodeLine2}
              </p>
            </div>
          )}

          {/* "ЧЕСТНЫЙ ЗНАК" */}
          <p className="text-[5px] font-semibold text-warm-gray-700 mt-0.5">
            ЧЕСТНЫЙ ЗНАК
          </p>

          {/* EAC */}
          <div className="flex items-center gap-1 mt-0.5">
            <span className="text-[6px] font-bold text-warm-gray-800">EAC</span>
          </div>
        </div>

        {/* === ПРАВАЯ КОЛОНКА: информация + штрихкод WB === */}
        <div className="flex-1 flex flex-col justify-between min-w-0">
          {/* Верхняя часть: ИНН, организация, название, характеристики */}
          <div className="space-y-0 overflow-hidden">
            {/* ИНН сверху */}
            {showInn && data.inn && (
              <p className="text-[4px] text-warm-gray-500 truncate">
                ИНН: {data.inn}
              </p>
            )}

            {/* Организация */}
            {showOrganization && data.organization && (
              <p className="text-[5px] text-warm-gray-600 truncate">
                {data.organization}
              </p>
            )}

            {/* Название товара (крупно) */}
            {showName && data.name && (
              <p className="text-[7px] font-semibold text-warm-gray-800 truncate mt-0.5">
                {data.name}
              </p>
            )}

            {/* Цвет */}
            {showSizeColor && data.color && (
              <p className="text-[5px] text-warm-gray-600 truncate">
                цвет: {data.color}
              </p>
            )}

            {/* Размер */}
            {showSizeColor && data.size && (
              <p className="text-[5px] text-warm-gray-600 truncate">
                размер: {data.size}
              </p>
            )}

            {/* Артикул */}
            {showArticle && data.article && (
              <p className="text-[5px] text-warm-gray-600 truncate">
                арт.: {data.article}
              </p>
            )}
          </div>

          {/* Нижняя часть: штрихкод WB справа */}
          <div className="flex flex-col items-end mt-auto">
            <BarcodePlaceholder width={50} height={14} />
            <p className="text-[5px] text-warm-gray-500 font-mono mt-0.5">
              {data.barcode}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ============================================
  // PROFESSIONAL Layout
  // Соответствует backend PROFESSIONAL 58x40:
  // - Левая колонка: EAC, "ЧЕСТНЫЙ ЗНАК", DataMatrix, код ЧЗ, страна
  // - Правая колонка: штрихкод, описание, артикул, бренд, размер/цвет, реквизиты
  // ============================================
  return (
    <div
      className={`aspect-[58/40] bg-white border-2 border-warm-gray-300 rounded p-1 flex shadow-sm ${className || ""}`}
      style={{ minHeight: 80 }}
    >
      {/* === ЛЕВАЯ КОЛОНКА === */}
      <div className="flex flex-col items-start justify-between flex-shrink-0" style={{ width: '42%' }}>
        {/* EAC + "ЧЕСТНЫЙ ЗНАК" сверху */}
        <div className="flex items-start gap-1">
          <span className="text-[6px] font-bold text-warm-gray-800">EAC</span>
          <div className="leading-none">
            <p className="text-[4px] font-semibold text-warm-gray-700">ЧЕСТНЫЙ</p>
            <p className="text-[4px] font-semibold text-warm-gray-700">ЗНАК</p>
          </div>
        </div>

        {/* DataMatrix */}
        <DataMatrixPlaceholder size={32} />

        {/* Код ЧЗ текстом */}
        {showChzCode && (
          <div className="w-full">
            <p className="text-[3.5px] text-warm-gray-600 font-mono leading-tight truncate">
              {chzCodeExample}
            </p>
            <p className="text-[3.5px] text-warm-gray-600 font-mono leading-tight truncate">
              {chzCodeLine2}
            </p>
          </div>
        )}

        {/* Страна внизу */}
        {showCountry && (
          <p className="text-[4px] text-warm-gray-600 truncate mt-auto">
            Сделано в {data.country || "России"}
          </p>
        )}
      </div>

      {/* === ПРАВАЯ КОЛОНКА === */}
      <div className="flex-1 flex flex-col min-w-0 ml-1">
        {/* Штрихкод WB сверху */}
        <div className="flex flex-col items-start">
          <BarcodePlaceholder width={48} height={12} />
          <p className="text-[4px] text-warm-gray-500 font-mono">
            {data.barcode}
          </p>
        </div>

        {/* Описание (название, цвет, артикул, размер) */}
        {showName && data.name && (
          <div className="mt-0.5">
            <p className="text-[4px] text-warm-gray-700 leading-tight">
              {data.name}
              {data.color && `, цвет ${data.color}`}
              {data.article && `, артикул ${data.article}`}
              {data.size && `, размер ${data.size}`}
            </p>
          </div>
        )}

        {/* Артикул отдельно */}
        {showArticle && data.article && (
          <p className="text-[4px] text-warm-gray-600 truncate">
            Артикул: {data.article}
          </p>
        )}

        {/* Бренд */}
        {showBrand && data.brand && (
          <p className="text-[4px] text-warm-gray-600 truncate">
            Бренд: {data.brand}
          </p>
        )}

        {/* Размер / Цвет */}
        {showSizeColor && (data.size || data.color) && (
          <p className="text-[4px] text-warm-gray-600 truncate">
            {data.size && `Размер: ${data.size}`}
            {data.size && data.color && "    "}
            {data.color && `Цвет: ${data.color}`}
          </p>
        )}

        {/* Реквизиты */}
        <div className="mt-auto space-y-0">
          {showImporter && (
            <p className="text-[3.5px] text-warm-gray-500 truncate">
              Импортер: {data.importer || data.organization || "ООО Компания"}
            </p>
          )}
          {showManufacturer && (
            <p className="text-[3.5px] text-warm-gray-500 truncate">
              Производитель: {data.manufacturer || data.organization || "ООО Компания"}
            </p>
          )}
          {showAddress && data.address && (
            <p className="text-[3.5px] text-warm-gray-500 truncate">
              Адрес: {data.address}
            </p>
          )}
          <div className="flex gap-2">
            {showProductionDate && data.productionDate && (
              <p className="text-[3.5px] text-warm-gray-500">
                Дата: {data.productionDate}
              </p>
            )}
            {showCertificate && data.certificate && (
              <p className="text-[3.5px] text-warm-gray-500">
                Серт: {data.certificate}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
