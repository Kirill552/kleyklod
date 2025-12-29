"use client";

/**
 * Страница генерации этикеток.
 *
 * Функционал:
 * - Автоопределение типа файла (PDF или Excel)
 * - Загрузка настроек пользователя
 * - Ввод кодов маркировки (textarea или файл CSV/Excel)
 * - Pre-flight проверка перед генерацией
 * - Скачивание результата
 */

import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ConversionPrompts } from "@/components/conversion-prompts";
import { FeedbackModal } from "@/components/feedback-modal";
import { useAuth } from "@/contexts/auth-context";
import {
  generateLabels,
  getUserStats,
  submitFeedback,
  getFeedbackStatus,
  generateFromExcel,
  getUserPreferences,
} from "@/lib/api";
import type {
  GenerateLabelsResponse,
  GenerateFromExcelResponse,
  LabelLayout,
  LabelSize,
  FileDetectionResult,
} from "@/lib/api";
import type { LabelFormat, UserStats } from "@/types/api";
import { LayoutSelector } from "@/components/app/generate/layout-selector";
import { ShowFieldsToggle } from "@/components/app/generate/show-fields-toggle";
import {
  LabelPreview,
  LabelPreviewData,
} from "@/components/app/generate/label-preview";
import {
  UnifiedDropzone,
  type FileType,
} from "@/components/app/generate/unified-dropzone";
import { analytics } from "@/lib/analytics";
import {
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
} from "lucide-react";

/** Максимальный размер файла (50 МБ) */
const MAX_FILE_SIZE = 50 * 1024 * 1024;

export default function GeneratePage() {
  const { user } = useAuth();

  // Тип загруженного файла (определяется автоматически)
  const [fileType, setFileType] = useState<FileType | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [fileDetectionResult, setFileDetectionResult] =
    useState<FileDetectionResult | null>(null);

  // Состояние для PDF
  const [pdfPages, setPdfPages] = useState<number>(0);

  // Состояние для Excel
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);

  // Настройки layout этикетки
  const [labelLayout, setLabelLayout] = useState<LabelLayout>("classic");
  const [labelSize, setLabelSize] = useState<LabelSize>("58x40");
  const [organizationName, setOrganizationName] = useState("");
  const [showArticle, setShowArticle] = useState(true);
  const [showSizeColor, setShowSizeColor] = useState(true);
  const [showName, setShowName] = useState(true);

  // Флаг загрузки настроек пользователя
  const [prefsLoaded, setPrefsLoaded] = useState(false);

  // Состояние кодов маркировки
  const [codesText, setCodesText] = useState("");
  const [codesFile, setCodesFile] = useState<File | null>(null);

  // Формат этикеток
  const [labelFormat, setLabelFormat] = useState<LabelFormat>("combined");

  // Состояние генерации
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] =
    useState<GenerateLabelsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Статистика использования (для триггеров конверсии)
  const [userStats, setUserStats] = useState<UserStats | null>(null);

  // Состояние модала обратной связи
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // Ref для скрытого input файла с кодами
  const codesInputRef = useRef<HTMLInputElement>(null);

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

  /**
   * Загружаем настройки пользователя при монтировании.
   */
  const fetchUserPreferences = useCallback(async () => {
    try {
      const prefs = await getUserPreferences();
      // Применяем настройки
      setOrganizationName(prefs.organization_name || "");
      setLabelLayout(prefs.preferred_layout);
      setLabelSize(prefs.preferred_label_size);
      setLabelFormat(prefs.preferred_format);
      setShowArticle(prefs.show_article);
      setShowSizeColor(prefs.show_size_color);
      setShowName(prefs.show_name);
      setPrefsLoaded(true);
    } catch {
      // Настройки не критичны — используем дефолтные
      console.error("Ошибка загрузки настроек");
      setPrefsLoaded(true);
    }
  }, []);

  useEffect(() => {
    fetchUserStats();
    fetchUserPreferences();
  }, [fetchUserStats, fetchUserPreferences]);

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
   * Обработчик автодетекта файла (PDF или Excel).
   * Вызывается из UnifiedDropzone после определения типа.
   */
  const handleFileDetected = useCallback(
    (result: FileDetectionResult, file: File) => {
      setUploadedFile(file);
      setFileDetectionResult(result);
      setError(null);
      setGenerationResult(null);

      if (result.file_type === "pdf") {
        setFileType("pdf");
        setPdfPages(result.pages_count || 1);
        setSelectedColumn(null);
      } else if (result.file_type === "excel") {
        setFileType("excel");
        setPdfPages(0);
        // Автоматически выбираем рекомендуемую колонку
        if (result.detected_barcode_column) {
          setSelectedColumn(result.detected_barcode_column);
        } else if (result.columns && result.columns.length > 0) {
          setSelectedColumn(result.columns[0]);
        }
      }
    },
    []
  );

  /**
   * Удаление загруженного файла (PDF или Excel).
   */
  const removeUploadedFile = useCallback(() => {
    setUploadedFile(null);
    setFileType(null);
    setFileDetectionResult(null);
    setPdfPages(0);
    setSelectedColumn(null);
    setGenerationResult(null);
    setError(null);
  }, []);

  /**
   * Обработчик загрузки файла с кодами.
   */
  const handleCodesFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
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
   * Данные для превью этикетки (из первой строки Excel).
   */
  const previewData: LabelPreviewData = useMemo(() => {
    const sample = fileDetectionResult?.sample_items?.[0];
    return {
      barcode: sample?.barcode || "2000000000001",
      article: sample?.article || "АРТ-12345",
      size: sample?.size || "42",
      color: sample?.color || "Белый",
      name: "Товар", // sample doesn't have name in detection result
      organization: organizationName || "ИП Иванов И.И.",
    };
  }, [fileDetectionResult, organizationName]);

  /**
   * Генерация этикеток.
   */
  const handleGenerate = async () => {
    // Проверка входных данных
    if (!uploadedFile || !fileType) {
      setError("Загрузите файл (PDF или Excel)");
      return;
    }

    if (fileType === "excel" && !selectedColumn) {
      setError("Выберите колонку с баркодами");
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

      let result: GenerateLabelsResponse | GenerateFromExcelResponse;

      if (fileType === "pdf") {
        // PDF с этикетками WB
        result = await generateLabels(uploadedFile, codes, labelFormat);
      } else {
        // Excel с баркодами и layout настройками
        result = await generateFromExcel({
          excelFile: uploadedFile,
          codes: codes,
          barcodeColumn: selectedColumn!,
          layout: labelLayout,
          labelSize: labelSize,
          labelFormat: labelFormat,
          organizationName: organizationName || undefined,
          showArticle: showArticle,
          showSizeColor: showSizeColor,
          showName: showName,
        });
      }

      setGenerationResult(result as GenerateLabelsResponse);

      // Обновляем статистику после генерации (для триггеров конверсии)
      await fetchUserStats();

      // Проверяем, нужно ли показать модал обратной связи
      // Показываем после 3-й успешной генерации, если отзыв ещё не отправлен
      if (result.success && !feedbackSubmitted) {
        // Получаем текущий счётчик из localStorage
        const currentCount = parseInt(
          localStorage.getItem("kleykod_generation_count") || "0",
          10
        );
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

      {/* Шаг 1: Загрузка файла с автодетектом */}
      {!uploadedFile && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" />
              Файл из Wildberries
            </CardTitle>
            <p className="text-sm text-warm-gray-500 mt-1">
              Загрузите PDF с этикетками или Excel с баркодами — мы определим
              автоматически
            </p>
          </CardHeader>
          <CardContent>
            <UnifiedDropzone onFileDetected={handleFileDetected} />
          </CardContent>
        </Card>
      )}

      {/* Превью загруженного PDF файла */}
      {uploadedFile && fileType === "pdf" && (
        <Card className="border-2 border-emerald-200 bg-emerald-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" />
              PDF с этикетками
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-white border border-emerald-200 rounded-lg">
              <div className="flex items-center gap-3">
                <FileText className="w-10 h-10 text-emerald-600" />
                <div>
                  <p className="font-medium text-warm-gray-900">
                    {uploadedFile.name}
                  </p>
                  <p className="text-sm text-warm-gray-600">
                    {(uploadedFile.size / 1024 / 1024).toFixed(2)} МБ
                    {pdfPages > 0 && ` • ${pdfPages} страниц`}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={removeUploadedFile}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="w-5 h-5" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Превью Excel файла + выбор колонки */}
      {uploadedFile && fileType === "excel" && fileDetectionResult && (
        <Card className="border-2 border-blue-200 bg-blue-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-blue-600" />
              Проверьте данные из Excel
            </CardTitle>
            <p className="text-sm text-warm-gray-600 mt-1">
              Файл:{" "}
              <span className="font-medium">{uploadedFile.name}</span>
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
                <option value="" disabled>
                  Выберите колонку
                </option>
                {fileDetectionResult.columns?.map((col) => (
                  <option key={col} value={col}>
                    {col}{" "}
                    {col === fileDetectionResult.detected_barcode_column
                      ? "(рекомендуется)"
                      : ""}
                  </option>
                ))}
              </select>
              {fileDetectionResult.detected_barcode_column &&
                selectedColumn ===
                  fileDetectionResult.detected_barcode_column && (
                  <p className="text-xs text-emerald-600 mt-1 flex items-center gap-1">
                    <Check className="w-3 h-3" />
                    Автоматически определена как колонка с баркодами
                  </p>
                )}
            </div>

            {/* Примеры данных */}
            {fileDetectionResult.sample_items &&
              fileDetectionResult.sample_items.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-warm-gray-700">
                      Примеры данных
                    </p>
                    <span className="text-sm text-warm-gray-500">
                      Всего строк: {fileDetectionResult.rows_count}
                    </span>
                  </div>
                  <div className="bg-white rounded-lg border border-warm-gray-200 p-4 space-y-3">
                    {fileDetectionResult.sample_items.slice(0, 5).map((item, i) => (
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
                    {(fileDetectionResult.rows_count || 0) > 5 && (
                      <p className="text-xs text-warm-gray-400 text-center pt-2 border-t border-warm-gray-100">
                        ... и ещё {(fileDetectionResult.rows_count || 0) - 5} строк
                      </p>
                    )}
                  </div>
                </div>
              )}

            {/* Кнопки действий */}
            <div className="flex gap-3 pt-2">
              <Button
                variant="secondary"
                onClick={removeUploadedFile}
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

      {/* Настройки дизайна этикетки — показываем для Excel после выбора колонки */}
      {uploadedFile && fileType === "excel" && selectedColumn && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-600" />
              Дизайн этикетки
            </CardTitle>
            <p className="text-sm text-warm-gray-500 mt-1">
              Настройте внешний вид итоговых этикеток
            </p>
          </CardHeader>
          <CardContent className="space-y-8">
            {/* Layout selector с превью */}
            <LayoutSelector
              value={labelLayout}
              onChange={setLabelLayout}
              previewData={previewData}
              showArticle={showArticle}
              showSizeColor={showSizeColor}
              showName={showName}
            />

            {/* Разделитель */}
            <hr className="border-warm-gray-200" />

            {/* Настройки полей и организации */}
            <div className="grid md:grid-cols-2 gap-8">
              {/* Левая колонка — поля */}
              <ShowFieldsToggle
                showArticle={showArticle}
                showSizeColor={showSizeColor}
                showName={showName}
                onShowArticleChange={setShowArticle}
                onShowSizeColorChange={setShowSizeColor}
                onShowNameChange={setShowName}
              />

              {/* Правая колонка — организация и размер */}
              <div className="space-y-4">
                {/* Название организации */}
                <div>
                  <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                    Название организации
                  </label>
                  <input
                    type="text"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    placeholder="ИП Иванов И.И."
                    className="w-full px-4 py-2.5 rounded-xl border border-warm-gray-300 bg-white
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                  <p className="text-xs text-warm-gray-500 mt-1">
                    Отображается внизу этикетки
                  </p>
                </div>

                {/* Размер этикетки */}
                <div>
                  <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                    Размер этикетки
                  </label>
                  <select
                    value={labelSize}
                    onChange={(e) => setLabelSize(e.target.value as LabelSize)}
                    className="w-full px-4 py-2.5 rounded-xl border border-warm-gray-300 bg-white
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    <option value="58x40">58×40 мм (стандартный)</option>
                    <option value="58x30">58×30 мм (компактный)</option>
                    <option value="58x60">58×60 мм (увеличенный)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Превью результата */}
            <div className="bg-warm-gray-50 rounded-xl p-6">
              <p className="text-sm font-medium text-warm-gray-700 mb-4 text-center">
                Превью итоговой этикетки
              </p>
              <div className="flex justify-center">
                <div className="w-48">
                  <LabelPreview
                    data={previewData}
                    layout={labelLayout}
                    showArticle={showArticle}
                    showSizeColor={showSizeColor}
                    showName={showName}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
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
                  : (fileType === "pdf" && codesCount === pdfPages) ||
                      (fileType === "excel" &&
                        codesCount === fileDetectionResult?.rows_count)
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-amber-100 text-amber-700"
              }`}
            >
              {codesCount} кодов
              {fileType === "excel" && fileDetectionResult?.rows_count && (
                <span className="text-xs font-normal ml-1">
                  / {fileDetectionResult.rows_count} баркодов
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
                {fileType === "pdf" ? "этикеток в PDF" : "баркодов в Excel"}.
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
            !uploadedFile ||
            (fileType === "excel" && !selectedColumn)
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
