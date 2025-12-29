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

import { useState, useCallback, useRef, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ConversionPrompts } from "@/components/conversion-prompts";
import { FeedbackModal } from "@/components/feedback-modal";
import { useAuth } from "@/contexts/auth-context";
import { generateLabels, getUserStats, submitFeedback, getFeedbackStatus, parseExcel } from "@/lib/api";
import type { GenerateLabelsResponse, ExcelParseResponse } from "@/lib/api";
import type { LabelFormat, UserStats } from "@/types/api";
import { analytics } from "@/lib/analytics";
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
  Check,
  Table,
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

/** Разрешённые типы для Excel с баркодами WB */
const ACCEPTED_EXCEL_TYPES = {
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel": [".xls"],
};

export default function GeneratePage() {
  const { user } = useAuth();

  // Режим загрузки: 'pdf' (PDF с этикетками) или 'excel' (Excel с баркодами)
  const [uploadMode, setUploadMode] = useState<'pdf' | 'excel'>('pdf');

  // Состояние загруженных файлов (режим PDF)
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfPages, setPdfPages] = useState<number>(0);

  // Состояние Excel файла и превью (режим Excel)
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [excelPreview, setExcelPreview] = useState<ExcelParseResponse | null>(null);
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);
  const [isParsingExcel, setIsParsingExcel] = useState(false);

  // Состояние кодов маркировки
  const [codesText, setCodesText] = useState("");
  const [codesFile, setCodesFile] = useState<File | null>(null);

  // Формат этикеток
  const [labelFormat, setLabelFormat] = useState<LabelFormat>("combined");

  // Состояние генерации
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<GenerateLabelsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Статистика использования (для триггеров конверсии)
  const [userStats, setUserStats] = useState<UserStats | null>(null);

  // Состояние модала обратной связи
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // Ref для скрытого input файла с кодами
  const codesInputRef = useRef<HTMLInputElement>(null);
  // Ref для скрытого input файла Excel
  const excelInputRef = useRef<HTMLInputElement>(null);

  /**
   * Загружаем статистику пользователя при монтировании и после генерации.
   */
  const fetchUserStats = useCallback(async () => {
    try {
      const stats = await getUserStats();
      setUserStats(stats);
    } catch {
      // Игнорируем ошибку — статистика не критична
      console.error("Ошибка загрузки статистики");
    }
  }, []);

  useEffect(() => {
    fetchUserStats();
  }, [fetchUserStats]);

  /**
   * Проверяем статус обратной связи при монтировании.
   * Если отзыв уже отправлен — запоминаем это.
   */
  useEffect(() => {
    const checkFeedbackStatus = async () => {
      try {
        const status = await getFeedbackStatus();
        setFeedbackSubmitted(status.feedback_submitted);
      } catch {
        // Если ошибка — используем localStorage как fallback
        const submitted = localStorage.getItem("kleykod_feedback_submitted");
        if (submitted === "true") {
          setFeedbackSubmitted(true);
        }
      }
    };
    checkFeedbackStatus();
  }, []);

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
   * Обработчик отклоненных файлов (неверный формат).
   */
  const onDropRejected = useCallback(() => {
    setError("Формат не поддерживается. Нужен PDF (не картинка). Скачайте заново из WB.");
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
    onDropRejected: onDropRejected,
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
   * Обработчик загрузки Excel файла с баркодами.
   * Отправляет файл на сервер для анализа и получает превью.
   */
  const handleExcelUpload = async (file: File) => {
    setExcelFile(file);
    setIsParsingExcel(true);
    setError(null);
    setExcelPreview(null);
    setSelectedColumn(null);

    try {
      const preview = await parseExcel(file);
      setExcelPreview(preview);

      // Автоматически выбираем рекомендуемую колонку
      if (preview.detected_column) {
        setSelectedColumn(preview.detected_column);
      } else if (preview.barcode_candidates.length > 0) {
        setSelectedColumn(preview.barcode_candidates[0]);
      } else if (preview.all_columns.length > 0) {
        setSelectedColumn(preview.all_columns[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка анализа Excel");
      setExcelFile(null);
    } finally {
      setIsParsingExcel(false);
    }
  };

  /**
   * Обработчик выбора Excel файла через input.
   */
  const handleExcelFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await handleExcelUpload(file);
    }
  };

  /**
   * Удаление Excel файла и сброс превью.
   */
  const removeExcelFile = () => {
    setExcelFile(null);
    setExcelPreview(null);
    setSelectedColumn(null);
    if (excelInputRef.current) {
      excelInputRef.current.value = "";
    }
    setError(null);
  };

  /**
   * Генерация этикеток.
   */
  const handleGenerate = async () => {
    // Проверка входных данных в зависимости от режима
    if (uploadMode === 'pdf') {
      if (!pdfFile) {
        setError("Загрузите PDF файл с этикетками");
        return;
      }
    } else {
      // Режим Excel
      if (!excelFile || !excelPreview) {
        setError("Загрузите Excel файл с баркодами");
        return;
      }
      if (!selectedColumn) {
        setError("Выберите колонку с баркодами");
        return;
      }
    }

    const codes = parseCodes(codesText);
    if (codes.length === 0) {
      setError("Введите коды маркировки");
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);

      let result: GenerateLabelsResponse;

      if (uploadMode === 'pdf') {
        // Старый способ — PDF с этикетками
        result = await generateLabels(pdfFile!, codes, labelFormat);
      } else {
        // Новый способ — Excel с баркодами
        result = await generateLabels({
          barcodesExcel: excelFile!,
          barcodeColumn: selectedColumn!,
          codes: codes,
          labelFormat: labelFormat,
        });
      }

      setGenerationResult(result);

      // Обновляем статистику после генерации (для триггеров конверсии)
      await fetchUserStats();

      // Проверяем, нужно ли показать модал обратной связи
      // Показываем после 3-й успешной генерации, если отзыв ещё не отправлен
      if (result.success && !feedbackSubmitted) {
        // Получаем текущий счётчик из localStorage
        const currentCount = parseInt(localStorage.getItem("kleykod_generation_count") || "0", 10);
        const newCount = currentCount + 1;
        localStorage.setItem("kleykod_generation_count", String(newCount));

        // Показываем модал на 3-й генерации
        if (newCount >= 3) {
          setShowFeedbackModal(true);
        }
      }
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
    // Используем download_url из ответа (FileStorage endpoint)
    // или fallback на generations endpoint для совместимости
    if (generationResult?.download_url) {
      window.open(generationResult.download_url, "_blank");
    } else if (generationResult?.file_id) {
      window.open(`/api/generations/${generationResult.file_id}/download`, "_blank");
    }
  };

  /**
   * Обработчик отправки обратной связи.
   */
  const handleFeedbackSubmit = async (text: string) => {
    await submitFeedback(text, "web");
    // Отмечаем что отзыв отправлен
    setFeedbackSubmitted(true);
    localStorage.setItem("kleykod_feedback_submitted", "true");
    // Трекаем событие в аналитике
    analytics.feedbackSubmit();
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
          Объедините этикетки WB и коды Честного Знака в один файл
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

      {/* Результат генерации - ошибка */}
      {generationResult && !generationResult.success && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <AlertTriangle className="w-8 h-8 text-red-600 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900 text-lg mb-2">
                Ошибка генерации
              </h3>
              <p className="text-red-700 mb-4">
                {generationResult.message}
              </p>

              {generationResult.preflight?.checks && generationResult.preflight.checks.filter(c => c.status === "error").length > 0 && (
                <div className="bg-red-100 border border-red-300 rounded-lg p-3">
                  <p className="font-medium text-red-800 mb-1">Детали ошибки:</p>
                  <ul className="text-sm text-red-700 list-disc list-inside">
                    {generationResult.preflight.checks.filter(c => c.status === "error").map((check, i) => (
                      <li key={i}>{check.message}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Результат генерации - успех */}
      {generationResult && generationResult.success && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <CheckCircle className="w-8 h-8 text-emerald-600 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-emerald-900 text-lg mb-2">
                Готово! Этикетки 58x40мм, 203 DPI
              </h3>
              <p className="text-emerald-700 mb-4">
                Создано {generationResult.labels_count} этикеток
                {" • "}
                {generationResult.pages_count} страниц
                {" • "}
                {generationResult.label_format === "separate" ? "раздельный формат" : "объединённый формат"}
                {" • "}
                <span className="text-emerald-600">идеально для термопринтера</span>
              </p>

              {generationResult.preflight?.checks && generationResult.preflight.checks.filter(c => c.status === "warning").length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                  <p className="font-medium text-amber-800 mb-1">Предупреждения:</p>
                  <ul className="text-sm text-amber-700 list-disc list-inside">
                    {generationResult.preflight.checks.filter(c => c.status === "warning").map((check, i) => (
                      <li key={i}>{check.message}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* GTIN warning для микс-поставок */}
              {generationResult.gtin_warning && generationResult.gtin_count && generationResult.gtin_count > 1 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-blue-800">
                        Обнаружены коды для {generationResult.gtin_count} разных товаров
                      </p>
                      <p className="text-sm text-blue-700 mt-1">
                        Умное сопоставление для микс-поставок —{" "}
                        <a
                          href="#roadmap"
                          className="underline underline-offset-2 hover:text-blue-800"
                        >
                          скоро!
                        </a>
                      </p>
                    </div>
                  </div>
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

      {/* Триггеры конверсии Free → Pro */}
      {user && userStats && user.plan === "free" && (
        <ConversionPrompts
          remaining={userStats.today_limit - userStats.today_used}
          total={userStats.today_limit}
          plan={user.plan}
        />
      )}

      {/* Переключатель режима: PDF или Excel */}
      <div className="flex gap-4">
        <button
          onClick={() => {
            setUploadMode('pdf');
            removeExcelFile();
          }}
          className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
            uploadMode === 'pdf'
              ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
              : 'bg-white border-warm-gray-200 text-warm-gray-600 hover:border-warm-gray-300'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <FileText className={`w-5 h-5 ${uploadMode === 'pdf' ? 'text-emerald-600' : 'text-warm-gray-400'}`} />
            <span className="font-medium">У меня PDF с этикетками</span>
          </div>
          <p className="text-xs mt-1 text-warm-gray-500">
            Скачанный из ЛК Wildberries
          </p>
        </button>
        <button
          onClick={() => {
            setUploadMode('excel');
            removePdf();
          }}
          className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
            uploadMode === 'excel'
              ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
              : 'bg-white border-warm-gray-200 text-warm-gray-600 hover:border-warm-gray-300'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <Table className={`w-5 h-5 ${uploadMode === 'excel' ? 'text-emerald-600' : 'text-warm-gray-400'}`} />
            <span className="font-medium">У меня Excel с баркодами</span>
          </div>
          <p className="text-xs mt-1 text-warm-gray-500">
            Таблица с баркодами товаров
          </p>
        </button>
      </div>

      {/* Режим PDF: Dropzone для PDF */}
      {uploadMode === 'pdf' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" />
              PDF с этикетками из ЛК WB
            </CardTitle>
            <p className="text-sm text-warm-gray-500 mt-1">
              Поставки &rarr; Штрихкоды &rarr; Скачать PDF
            </p>
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
                  Только PDF (не картинка). Макс. 50 МБ
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      )}

      {/* Режим Excel: Загрузка и превью Excel файла */}
      {uploadMode === 'excel' && (
        <>
          {/* Скрытый input для Excel файла */}
          <input
            ref={excelInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleExcelFileChange}
            className="hidden"
          />

          {/* Загрузка Excel */}
          {!excelFile && !isParsingExcel && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Table className="w-5 h-5 text-emerald-600" />
                  Excel с баркодами товаров
                </CardTitle>
                <p className="text-sm text-warm-gray-500 mt-1">
                  Загрузите файл Excel с колонкой баркодов (штрихкодов WB)
                </p>
              </CardHeader>
              <CardContent>
                <div
                  onClick={() => excelInputRef.current?.click()}
                  className="border-2 border-dashed rounded-lg p-12 transition-colors cursor-pointer border-emerald-300 bg-gradient-to-br from-emerald-50 to-white hover:border-emerald-500"
                >
                  <div className="text-center">
                    <Upload className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                    <p className="text-lg font-medium text-warm-gray-900 mb-2">
                      Нажмите, чтобы выбрать Excel файл
                    </p>
                    <p className="text-sm text-warm-gray-500">
                      Поддерживаются форматы .xlsx и .xls
                    </p>
                    <p className="text-xs text-warm-gray-400 mt-2">
                      Макс. 50 МБ
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Индикатор загрузки Excel */}
          {isParsingExcel && (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <Loader2 className="w-12 h-12 text-emerald-500 mx-auto mb-4 animate-spin" />
                  <p className="text-lg font-medium text-warm-gray-900">
                    Анализируем файл...
                  </p>
                  <p className="text-sm text-warm-gray-500 mt-2">
                    Определяем колонку с баркодами
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Превью Excel данных */}
          {excelPreview && excelFile && (
            <Card className="border-2 border-blue-200 bg-blue-50/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5 text-blue-600" />
                  Проверьте данные из Excel
                </CardTitle>
                <p className="text-sm text-warm-gray-600 mt-1">
                  Файл: <span className="font-medium">{excelFile.name}</span>
                </p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Выбор колонки с баркодами */}
                <div>
                  <label className="block text-sm font-medium text-warm-gray-700 mb-2">
                    Колонка с баркодами:
                  </label>
                  <select
                    value={selectedColumn || ""}
                    onChange={(e) => setSelectedColumn(e.target.value)}
                    className="w-full p-3 border border-warm-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    <option value="" disabled>Выберите колонку</option>
                    {excelPreview.barcode_candidates.length > 0 ? (
                      excelPreview.barcode_candidates.map((col) => (
                        <option key={col} value={col}>
                          {col} {col === excelPreview.detected_column ? "(рекомендуется)" : ""}
                        </option>
                      ))
                    ) : (
                      excelPreview.all_columns.map((col) => (
                        <option key={col} value={col}>{col}</option>
                      ))
                    )}
                  </select>
                  {excelPreview.detected_column && selectedColumn === excelPreview.detected_column && (
                    <p className="text-xs text-emerald-600 mt-1 flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      Автоматически определена как колонка с баркодами
                    </p>
                  )}
                </div>

                {/* Примеры данных */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-warm-gray-700">
                      Примеры данных
                    </p>
                    <span className="text-sm text-warm-gray-500">
                      Всего строк: {excelPreview.total_rows}
                    </span>
                  </div>
                  <div className="bg-white rounded-lg border border-warm-gray-200 p-4 space-y-3">
                    {excelPreview.sample_items.slice(0, 5).map((item, i) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <span className="text-warm-gray-400 w-6 text-right">
                          {item.row_number}.
                        </span>
                        <code className="bg-warm-gray-100 px-3 py-1 rounded font-mono text-warm-gray-900">
                          {item.barcode}
                        </code>
                        {item.article && (
                          <span className="text-warm-gray-500 text-xs">
                            арт. {item.article}
                          </span>
                        )}
                        {item.size && (
                          <span className="text-warm-gray-500 text-xs">
                            {item.size}
                          </span>
                        )}
                        {item.color && (
                          <span className="text-warm-gray-500 text-xs">
                            {item.color}
                          </span>
                        )}
                      </div>
                    ))}
                    {excelPreview.total_rows > 5 && (
                      <p className="text-xs text-warm-gray-400 text-center pt-2 border-t border-warm-gray-100">
                        ... и ещё {excelPreview.total_rows - 5} строк
                      </p>
                    )}
                  </div>
                </div>

                {/* Кнопки действий */}
                <div className="flex gap-3 pt-2">
                  <Button
                    variant="secondary"
                    onClick={removeExcelFile}
                    className="flex-shrink-0"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Загрузить другой файл
                  </Button>
                  {selectedColumn && (
                    <div className="flex items-center gap-2 text-sm text-emerald-600 ml-auto">
                      <Check className="w-4 h-4" />
                      Готово к генерации
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

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
            <div>
              <CardTitle>Коды маркировки Честного Знака</CardTitle>
              <p className="text-sm text-warm-gray-500 mt-1">
                CSV/TXT из личного кабинета ЧЗ (crpt.ru)
              </p>
            </div>
            <span
              className={`text-sm font-medium px-3 py-1 rounded-lg ${
                codesCount === 0
                  ? "bg-warm-gray-100 text-warm-gray-600"
                  : (uploadMode === 'pdf' && codesCount === pdfPages) ||
                    (uploadMode === 'excel' && codesCount === excelPreview?.total_rows)
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-amber-100 text-amber-700"
              }`}
            >
              {codesCount} кодов
              {uploadMode === 'excel' && excelPreview?.total_rows && (
                <span className="text-xs font-normal ml-1">
                  / {excelPreview.total_rows} баркодов
                </span>
              )}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Кнопка загрузки файла с кодами */}
            <div className="flex flex-wrap items-center gap-4">
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
              <a
                href="/examples/codes-example.csv"
                download="codes-example.csv"
                className="text-sm text-emerald-600 hover:text-emerald-700 underline underline-offset-2"
              >
                Скачать пример файла
              </a>
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
                строке. Коды должны соответствовать количеству{" "}
                {uploadMode === 'pdf' ? "этикеток в PDF" : "баркодов в Excel"}.
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
          disabled={
            isGenerating ||
            codesCount === 0 ||
            (uploadMode === 'pdf' && !pdfFile) ||
            (uploadMode === 'excel' && (!excelFile || !selectedColumn))
          }
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
      {user && userStats && (
        <div className="text-center text-sm text-warm-gray-500">
          Использовано сегодня:{" "}
          <span className="font-medium text-warm-gray-700">
            {userStats.today_used} / {userStats.today_limit}
          </span>
          {" "}этикеток
        </div>
      )}

      {/* Модал обратной связи */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        onSubmit={handleFeedbackSubmit}
      />
    </div>
  );
}
