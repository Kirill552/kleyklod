"use client";

/**
 * LabelCanvas - превью этикетки на Fabric.js canvas.
 *
 * Использует конфигурацию layouts из бэкенда (с fallback на локальную).
 * Canvas readonly - элементы не выделяются и не перетаскиваются.
 */

import { useEffect, useRef, useCallback, useMemo } from "react";
import useSWR from "swr";
import {
  type LabelLayout,
  type LabelSize,
  LABEL_SIZES,
  mmToPx,
} from "@/lib/label-config";
import {
  renderLabel,
  type LabelCanvasData,
  type ShowFlags,
  type CustomLine,
} from "@/lib/render-label";

// Re-export типы для удобства использования
export type { LabelLayout, LabelSize, LabelCanvasData, ShowFlags, CustomLine };

interface LabelCanvasProps {
  data: LabelCanvasData;
  layout: LabelLayout;
  size: LabelSize;
  // Флаги показа полей
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
  customLines?: CustomLine[];
  className?: string;
  scale?: number; // Масштаб отображения (по умолчанию 0.5)
}

// Fetcher для SWR
const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error("Failed to fetch config");
    return res.json();
  });

export function LabelCanvas({
  data,
  layout,
  size,
  showArticle = true,
  showSizeColor = true,
  showName = true,
  showOrganization = true,
  showInn = false,
  showCountry = false,
  showComposition = false,
  showAddress = false,
  showCertificate = false,
  showProductionDate = false,
  showImporter = false,
  showManufacturer = false,
  showBrand = false,
  showChzCode = true,
  customLines,
  className,
  scale = 0.5,
}: LabelCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fabricRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fabricModuleRef = useRef<any>(null);
  const initializingRef = useRef(false);

  // Загружаем конфиг с бэкенда (опционально)
  // Пока API не готов, используем локальную конфигурацию
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { data: remoteConfig } = useSWR("/api/v1/config/layouts", fetcher, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
    // Тихо игнорируем ошибки - используем локальную конфигурацию
    onError: () => {},
  });

  // Размеры canvas в пикселях
  const labelSizeMm = LABEL_SIZES[size];
  const canvasWidth = mmToPx(labelSizeMm.width);
  const canvasHeight = mmToPx(labelSizeMm.height);

  // Собираем флаги показа (мемоизировано для стабильной ссылки)
  const showFlags: ShowFlags = useMemo(() => ({
    showArticle,
    showSizeColor,
    showName,
    showOrganization,
    showInn,
    showCountry,
    showComposition,
    showAddress,
    showCertificate,
    showProductionDate,
    showImporter,
    showManufacturer,
    showBrand,
    showChzCode,
  }), [
    showArticle,
    showSizeColor,
    showName,
    showOrganization,
    showInn,
    showCountry,
    showComposition,
    showAddress,
    showCertificate,
    showProductionDate,
    showImporter,
    showManufacturer,
    showBrand,
    showChzCode,
  ]);

  // Функция рендеринга
  const doRender = useCallback(() => {
    if (!fabricRef.current || !fabricModuleRef.current) return;

    renderLabel(
      fabricRef.current,
      fabricModuleRef.current,
      layout,
      size,
      data,
      showFlags,
      customLines
    );
  }, [layout, size, data, showFlags, customLines]);

  // Инициализация canvas
  useEffect(() => {
    if (!canvasRef.current) return;
    if (initializingRef.current) return;

    initializingRef.current = true;

    // Динамический импорт fabric.js (для избежания SSR проблем)
    import("fabric").then((fabricModule) => {
      if (!canvasRef.current) return;

      fabricModuleRef.current = fabricModule;

      // Если canvas уже инициализирован, уничтожаем его
      if (fabricRef.current) {
        fabricRef.current.dispose();
      }

      // Создаем новый canvas
      const canvas = new fabricModule.Canvas(canvasRef.current, {
        width: canvasWidth,
        height: canvasHeight,
        selection: false, // Отключаем выделение области
        renderOnAddRemove: false, // Оптимизация: рендерим вручную
      });

      fabricRef.current = canvas;
      initializingRef.current = false;

      // Первоначальный рендер
      doRender();
    });

    // Cleanup
    return () => {
      if (fabricRef.current) {
        fabricRef.current.dispose();
        fabricRef.current = null;
      }
      initializingRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Обновляем размеры canvas при изменении size
  useEffect(() => {
    if (!fabricRef.current) return;

    fabricRef.current.setDimensions({
      width: canvasWidth,
      height: canvasHeight,
    });

    doRender();
  }, [canvasWidth, canvasHeight, doRender]);

  // Перерисовываем при изменении данных
  useEffect(() => {
    doRender();
  }, [doRender]);

  return (
    <div
      className={className}
      style={{
        transform: `scale(${scale})`,
        transformOrigin: "top left",
        width: canvasWidth * scale,
        height: canvasHeight * scale,
      }}
    >
      <div
        style={{
          width: canvasWidth,
          height: canvasHeight,
          border: "1px solid #e5e5e5",
          borderRadius: "4px",
          overflow: "hidden",
          backgroundColor: "#fff",
          boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        }}
      >
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}

/**
 * Компактная версия для использования в селекторе layouts.
 */
interface LabelCanvasCompactProps {
  layout: LabelLayout;
  size?: LabelSize;
  className?: string;
}

export function LabelCanvasCompact({
  layout,
  size = "58x40",
  className,
}: LabelCanvasCompactProps) {
  // Демо-данные для превью
  const demoData: LabelCanvasData = {
    barcode: "4607100000012",
    article: "ABC-123",
    size: "M",
    color: "Черный",
    name: "Футболка",
    organization: "ООО Компания",
    inn: "1234567890",
    country: "Россия",
  };

  return (
    <LabelCanvas
      data={demoData}
      layout={layout}
      size={size}
      scale={0.3}
      className={className}
      showArticle={true}
      showSizeColor={true}
      showName={true}
      showOrganization={true}
      showInn={layout === "basic"}
      showCountry={layout === "professional"}
    />
  );
}

export default LabelCanvas;
