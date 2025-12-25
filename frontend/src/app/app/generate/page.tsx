"use client";

/**
 * Страница генерации этикеток.
 *
 * Функционал:
 * - Drag-n-drop загрузка PDF с этикетками WB
 * - Ввод кодов маркировки (textarea или файл CSV/Excel)
 * - Pre-flight проверка перед генерацией
 * - Скачивание результата
 */

import { useState, useCallback, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { generateLabels } from "@/lib/api";
import type { GenerateLabelsResponse } from "@/lib/api";
import type { LabelFormat } from "@/types/api";
import {
  Upload,
  FileText,
  Info,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Download,
  X,
  FileSpreadsheet,
  Trash2,
  Layers,
  SplitSquareVertical,
} from "lucide-react";

/** Максимальный размер файла (50 МБ) */
const MAX_FILE_SIZE = 50 * 1024 * 1024;

/** Разрешённые MIME типы для PDF */
const ACCEPTED_PDF_TYPES = {
  "application/pdf": [".pdf"],
};

/** Разрешённые типы для файлов с кодами */
const ACCEPTED_CODES_TYPES = {
  "text/csv": [".csv"],
  "text/plain": [".txt"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel": [".xls"],
};

export default function GeneratePage() {
  const { user } = useAuth();

  // Состояние загруженных файлов
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfPages, setPdfPages] = useState<number>(0);

  // Состояние кодов маркировки
  const [codesText, setCodesText] = useState("");
  const [codesFile, setCodesFile] = useState<File | null>(null);

  // Формат этикеток
  const [labelFormat, setLabelFormat] = useState<LabelFormat>("combined");

  // Состояние генерации
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<GenerateLabelsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Ref для скрытого input файла с кодами
  const codesInputRef = useRef<HTMLInputElement>(null);

  /**
   * Парсинг текста кодов в массив.
   */
  const parseCodes = (text: string): string[] => {
    return text
      .split(/[\n,;]/)
      .map((code) => code.trim())
      .filter((code) => code.length > 0);
  };

  /**
   * Обработчик загрузки PDF.
   */
  const onDropPdf = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setPdfFile(file);
      setError(null);
      setGenerationResult(null);

      // Считаем количество страниц (упрощённо — по размеру файла)
      // В реальности нужно парсить PDF или получать от бэкенда
      // Пока используем заглушку
      setPdfPages(Math.max(1, Math.floor(file.size / 50000)));
    }
  }, []);

  /**
   * Dropzone для PDF.
   */
  const {
    getRootProps: getPdfRootProps,
    getInputProps: getPdfInputProps,
    isDragActive: isPdfDragActive,
  } = useDropzone({
    onDrop: onDropPdf,
    accept: ACCEPTED_PDF_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
  });

  /**
   * Обработчик загрузки файла с кодами.
   */
  const handleCodesFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setCodesFile(file);

    // Читаем содержимое файла
    try {
      const text = await file.text();
      setCodesText(text);
    } catch {
      setError("Ошибка чтения файла с кодами");
    }
  };

  /**
   * Удаление PDF файла.
   */
  const removePdf = () => {
    setPdfFile(null);
    setPdfPages(0);
    setGenerationResult(null);
    setError(null);
  };

  /**
   * Удаление файла с кодами.
   */
  const removeCodesFile = () => {
    setCodesFile(null);
    setCodesText("");
    if (codesInputRef.current) {
      codesInputRef.current.value = "";
    }
  };

  /**
   * Генерация этикеток.
   */
  const handleGenerate = async () => {
    if (!pdfFile) {
      setError("Загрузите PDF файл с этикетками");
      return;
    }

    const codes = parseCodes(codesText);
    if (codes.length === 0) {
      setError("Введите коды маркировки");
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);

      const result = await generateLabels(pdfFile, codes, labelFormat);
      setGenerationResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка генерации");
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Скачивание результата.
   */
  const handleDownload = () => {
    if (!generationResult) return;

    // В реальности здесь будет вызов API для скачивания файла
    window.open(`/api/generations/${generationResult.generation_id}/download`, "_blank");
  };

  const codes = parseCodes(codesText);
  const codesCount = codes.length;

  return (
    <div className="space-y-8">
      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold text-warm-gray-900 mb-2">
          Генерация этикеток
        </h1>
        <p className="text-warm-gray-600">
          Загрузите PDF с этикетками Wildberries и коды маркировки
        </p>
      </div>

      {/* Информация */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-emerald-800">
          <p className="font-medium mb-1">Как это работает:</p>
          <ol className="list-decimal list-inside space-y-1">
            <li>Загрузите PDF файл с этикетками Wildberries</li>
            <li>Введите коды маркировки Честного Знака (по одному на строку)</li>
            <li>Нажмите «Создать этикетки» и скачайте результат</li>
          </ol>
        </div>
      </div>

      {/* Ошибка */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Результат генерации */}
      {generationResult && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <CheckCircle className="w-8 h-8 text-emerald-600 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-emerald-900 text-lg mb-2">
                Этикетки успешно созданы!
              </h3>
              <p className="text-emerald-700 mb-4">
                Создано {generationResult.labels_count} этикеток
                {" • "}
                {generationResult.pages_count} страниц
                {" • "}
                {generationResult.label_format === "separate" ? "раздельный формат" : "объединённый формат"}
              </p>

              {generationResult.warnings.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                  <p className="font-medium text-amber-800 mb-1">Предупреждения:</p>
                  <ul className="text-sm text-amber-700 list-disc list-inside">
                    {generationResult.warnings.map((warning, i) => (
                      <li key={i}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              <Button variant="primary" size="lg" onClick={handleDownload}>
                <Download className="w-5 h-5" />
                Скачать PDF
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Dropzone для PDF */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-600" />
            Этикетки Wildberries
          </CardTitle>
        </CardHeader>
        <CardContent>
          {pdfFile ? (
            <div className="flex items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
              <div className="flex items-center gap-3">
                <FileText className="w-10 h-10 text-emerald-600" />
                <div>
                  <p className="font-medium text-warm-gray-900">{pdfFile.name}</p>
                  <p className="text-sm text-warm-gray-600">
                    {(pdfFile.size / 1024 / 1024).toFixed(2)} МБ
                    {pdfPages > 0 && ` • ~${pdfPages} страниц`}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={removePdf}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="w-5 h-5" />
              </Button>
            </div>
          ) : (
            <div
              {...getPdfRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 transition-colors cursor-pointer ${
                isPdfDragActive
                  ? "border-emerald-500 bg-emerald-50"
                  : "border-emerald-300 bg-gradient-to-br from-emerald-50 to-white hover:border-emerald-500"
              }`}
            >
              <input {...getPdfInputProps()} />
              <div className="text-center">
                <Upload className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                <p className="text-lg font-medium text-warm-gray-900 mb-2">
                  {isPdfDragActive
                    ? "Отпустите файл здесь"
                    : "Перетащите PDF файл сюда"}
                </p>
                <p className="text-sm text-warm-gray-500">
                  или нажмите, чтобы выбрать файл
                </p>
                <p className="text-xs text-warm-gray-400 mt-2">
                  Максимальный размер: 50 МБ
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Выбор формата этикеток */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-600" />
            Формат этикеток
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Объединённые (по умолчанию) */}
            <label
              className={`relative flex cursor-pointer rounded-lg border p-4 transition-colors ${
                labelFormat === "combined"
                  ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-500"
                  : "border-warm-gray-200 hover:border-emerald-300"
              }`}
            >
              <input
                type="radio"
                name="labelFormat"
                value="combined"
                checked={labelFormat === "combined"}
                onChange={() => setLabelFormat("combined")}
                className="sr-only"
              />
              <div className="flex items-start gap-3">
                <Layers className={`w-6 h-6 mt-0.5 ${
                  labelFormat === "combined" ? "text-emerald-600" : "text-warm-gray-400"
                }`} />
                <div>
                  <p className={`font-medium ${
                    labelFormat === "combined" ? "text-emerald-900" : "text-warm-gray-900"
                  }`}>
                    Объединённые
                    <span className="ml-2 text-xs font-normal text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded">
                      рекомендуется
                    </span>
                  </p>
                  <p className="text-sm text-warm-gray-600 mt-1">
                    WB + DataMatrix на одной этикетке.
                    Экономит материал и время.
                  </p>
                </div>
              </div>
            </label>

            {/* Раздельные */}
            <label
              className={`relative flex cursor-pointer rounded-lg border p-4 transition-colors ${
                labelFormat === "separate"
                  ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-500"
                  : "border-warm-gray-200 hover:border-emerald-300"
              }`}
            >
              <input
                type="radio"
                name="labelFormat"
                value="separate"
                checked={labelFormat === "separate"}
                onChange={() => setLabelFormat("separate")}
                className="sr-only"
              />
              <div className="flex items-start gap-3">
                <SplitSquareVertical className={`w-6 h-6 mt-0.5 ${
                  labelFormat === "separate" ? "text-emerald-600" : "text-warm-gray-400"
                }`} />
                <div>
                  <p className={`font-medium ${
                    labelFormat === "separate" ? "text-emerald-900" : "text-warm-gray-900"
                  }`}>
                    Раздельные
                  </p>
                  <p className="text-sm text-warm-gray-600 mt-1">
                    WB и DataMatrix на отдельных листах.
                    Порядок: WB1, ЧЗ1, WB2, ЧЗ2...
                  </p>
                </div>
              </div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Ввод кодов маркировки */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Коды маркировки Честного Знака</CardTitle>
            <span
              className={`text-sm font-medium px-3 py-1 rounded-lg ${
                codesCount === 0
                  ? "bg-warm-gray-100 text-warm-gray-600"
                  : codesCount === pdfPages
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-amber-100 text-amber-700"
              }`}
            >
              {codesCount} кодов
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Кнопка загрузки файла с кодами */}
            <div className="flex items-center gap-4">
              <input
                ref={codesInputRef}
                type="file"
                accept=".csv,.txt,.xlsx,.xls"
                onChange={handleCodesFileChange}
                className="hidden"
              />
              <Button
                variant="secondary"
                size="sm"
                onClick={() => codesInputRef.current?.click()}
              >
                <FileSpreadsheet className="w-4 h-4" />
                Загрузить CSV/Excel
              </Button>
              {codesFile && (
                <div className="flex items-center gap-2 text-sm text-warm-gray-600">
                  <span>{codesFile.name}</span>
                  <button
                    onClick={removeCodesFile}
                    className="text-red-500 hover:text-red-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Textarea для кодов */}
            <textarea
              value={codesText}
              onChange={(e) => setCodesText(e.target.value)}
              placeholder={`Введите коды маркировки по одному на строку:\n\n010460043400000321...\n010460043400000321...\n...`}
              className="w-full h-64 p-4 border border-warm-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 font-mono text-sm"
            />

            {/* Подсказка */}
            <div className="bg-warm-gray-50 border border-warm-gray-200 rounded-lg p-4">
              <p className="text-sm text-warm-gray-600">
                <strong>Формат кодов:</strong> введите каждый код на отдельной
                строке. Коды должны соответствовать количеству этикеток в PDF.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Кнопка генерации */}
      <div className="flex justify-end gap-4">
        <Button
          variant="primary"
          size="lg"
          onClick={handleGenerate}
          disabled={!pdfFile || codesCount === 0 || isGenerating}
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Создание...
            </>
          ) : (
            <>
              <CheckCircle className="w-5 h-5" />
              Создать этикетки
            </>
          )}
        </Button>
      </div>

      {/* Информация о лимитах */}
      {user && (
        <div className="text-center text-sm text-warm-gray-500">
          Доступно этикеток сегодня:{" "}
          <span className="font-medium text-warm-gray-700">
            {user.plan === "free" ? "50" : user.plan === "pro" ? "500" : "10,000"}
          </span>
        </div>
      )}
    </div>
  );
}
