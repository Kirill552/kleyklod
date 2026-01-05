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

export type FileType = "pdf" | "excel" | "unknown";

export interface ExcelSampleItem {
  barcode: string;
  article: string | null;
  size: string | null;
  color: string | null;
  name?: string | null;
  country?: string | null;
  composition?: string | null;
  brand?: string | null;
  manufacturer?: string | null;
  production_date?: string | null;
  importer?: string | null;
  certificate_number?: string | null;
  row_number: number;
}

export interface FileDetectionResult {
  file_type: FileType;
  filename: string;
  size_bytes: number;
  pages_count?: number;
  rows_count?: number;
  columns?: string[];
  detected_barcode_column?: string;
  sample_items?: ExcelSampleItem[];
  error?: string;
}

interface UnifiedDropzoneProps {
  onFileDetected: (result: FileDetectionResult, file: File) => void;
  disabled?: boolean;
  className?: string;
}

export function UnifiedDropzone({
  onFileDetected,
  disabled,
  className,
}: UnifiedDropzoneProps) {
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setIsDetecting(true);
      setError(null);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/api/labels/detect-file", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Ошибка определения типа файла");
        }

        const result: FileDetectionResult = await response.json();

        if (result.file_type === "unknown") {
          setError(result.error || "Неподдерживаемый формат файла");
          return;
        }

        onFileDetected(result, file);
      } catch (err) {
        console.error("Detection error:", err);
        setError("Ошибка при обработке файла");
      } finally {
        setIsDetecting(false);
      }
    },
    [onFileDetected]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
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
              href="/examples/wb-barcodes-example.xlsx"
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
