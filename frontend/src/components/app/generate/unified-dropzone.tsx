"use client";

/**
 * Dropzone для загрузки Excel файлов с баркодами.
 *
 * Определяет колонки, строки и sample data.
 */

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileSpreadsheet,
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  detectFile,
  type FileType,
  type ExcelSampleItem,
  type FileDetectionResult,
} from "@/lib/api";

// Re-export типов для обратной совместимости
export type { FileType, ExcelSampleItem, FileDetectionResult };

interface UnifiedDropzoneProps {
  onFileDetected: (result: FileDetectionResult, file: File) => void;
  disabled?: boolean;
  className?: string;
  /** URL примера файла (по умолчанию для сайта) */
  exampleFileUrl?: string;
}

export function UnifiedDropzone({
  onFileDetected,
  disabled,
  className,
  exampleFileUrl = "/examples/wb-barcodes-example.xlsx",
}: UnifiedDropzoneProps) {
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];

      // Проверка расширения файла (iOS может не передавать правильный MIME-тип)
      const fileName = file.name.toLowerCase();
      if (!fileName.endsWith(".xlsx") && !fileName.endsWith(".xls")) {
        setError("Поддерживаются только Excel файлы (.xlsx, .xls)");
        return;
      }

      setIsDetecting(true);
      setError(null);

      try {
        // Используем detectFile из api.ts (добавляет X-VK-Token для iOS VK Mini App)
        const result = await detectFile(file);

        if (result.file_type === "unknown") {
          setError(result.error || "Неподдерживаемый формат файла");
          return;
        }

        onFileDetected(result, file);
      } catch (err) {
        console.error("Detection error:", err);
        setError(err instanceof Error ? err.message : "Ошибка при обработке файла");
      } finally {
        setIsDetecting(false);
      }
    },
    [onFileDetected]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      // Стандартные MIME-типы
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
      // iOS/Safari может отдавать эти типы для Excel файлов
      "application/octet-stream": [".xlsx", ".xls"],
      "application/binary": [".xlsx", ".xls"],
      // Некоторые браузеры используют этот тип
      "application/x-xlsx": [".xlsx"],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
    disabled: disabled || isDetecting,
  });

  return (
    <div className={`space-y-4 ${className || ""}`}>
      <div
        {...getRootProps()}
        className={`
          relative p-8 rounded-2xl border-2 border-dashed cursor-pointer
          transition-all duration-300 min-h-[280px]
          flex flex-col items-center justify-center
          ${
            isDragActive
              ? "border-emerald-400 bg-emerald-50"
              : "border-warm-gray-300 bg-warm-gray-50 hover:border-emerald-400 hover:bg-emerald-50/30"
          }
          ${disabled || isDetecting ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        <input {...getInputProps()} />

        {isDetecting ? (
          <div className="text-center">
            <Loader2 className="w-16 h-16 text-emerald-500 mx-auto mb-4 animate-spin" />
            <p className="text-lg font-medium text-warm-gray-700">
              Анализируем файл...
            </p>
          </div>
        ) : (
          <>
            <Upload className="w-16 h-16 text-emerald-500 mb-4" />
            <p className="text-lg font-medium text-warm-gray-700 mb-2 text-center">
              Загрузите Excel с баркодами
            </p>
            <p className="text-sm text-warm-gray-500 mb-4 text-center">
              Скачайте файл из личного кабинета Wildberries
            </p>

            {/* Mobile button */}
            <button
              type="button"
              className="md:hidden px-6 py-3 bg-emerald-500 text-white rounded-xl font-medium"
              onClick={(e) => e.stopPropagation()}
            >
              Выбрать файл
            </button>

            {/* Example file link */}
            <a
              href={exampleFileUrl}
              download
              onClick={(e) => e.stopPropagation()}
              className="text-sm text-emerald-600 hover:text-emerald-700 underline"
            >
              Скачать пример файла
            </a>

            {/* File type hint */}
            <div className="flex gap-4 mt-4 text-xs text-warm-gray-400">
              <div className="flex items-center gap-1">
                <FileSpreadsheet className="w-4 h-4" />
                <span>Excel (.xlsx, .xls)</span>
              </div>
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-start gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
