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
  PreflightCheck,
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
import {
  FieldOrderEditor,
  type FieldConfig,
} from "@/components/app/generate/field-order-editor";
import { ErrorCard } from "@/components/app/generate/error-card";
import {
  OrganizationModal,
  type OrganizationData,
} from "@/components/app/generate/organization-modal";
import {
  GenerationProgress,
  PreflightSummary,
  type GenerationPhase,
} from "@/components/app/generate/generation-progress";
import { analytics } from "@/lib/analytics";
import {
  FileText,
  Info,
  AlertTriangle,
  CheckCircle,
  Download,
  X,
  FileSpreadsheet,
  Trash2,
  Layers,
  SplitSquareVertical,
  Check,
  Building2,
} from "lucide-react";

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
  const [labelLayout, setLabelLayout] = useState<LabelLayout>("basic");
  const [labelSize, setLabelSize] = useState<LabelSize>("58x40");
  const [organizationName, setOrganizationName] = useState("");
  const [inn, setInn] = useState("");
  const [organizationAddress, setOrganizationAddress] = useState("");
  const [productionCountry, setProductionCountry] = useState("");
  const [certificateNumber, setCertificateNumber] = useState("");

  // Модалка реквизитов организации
  const [showOrganizationModal, setShowOrganizationModal] = useState(false);

  // Флаги отображения полей
  const [showArticle, setShowArticle] = useState(true);
  const [showSizeColor, setShowSizeColor] = useState(true);
  const [showName, setShowName] = useState(true);
  const [showOrganization, setShowOrganization] = useState(true);
  const [showInn, setShowInn] = useState(false);
  const [showCountry, setShowCountry] = useState(false);
  const [showComposition, setShowComposition] = useState(false);
  const [showChzCodeText, setShowChzCodeText] = useState(false);
  const [showSerialNumber, setShowSerialNumber] = useState(false);
  // Флаги для профессионального шаблона
  const [showBrand, setShowBrand] = useState(false);
  const [showImporter, setShowImporter] = useState(false);
  const [showManufacturer, setShowManufacturer] = useState(false);
  const [showAddress, setShowAddress] = useState(false);
  const [showProductionDate, setShowProductionDate] = useState(false);
  const [showCertificate, setShowCertificate] = useState(false);
  // Дополнительные данные для профессионального шаблона
  const [importer, setImporter] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [productionDate, setProductionDate] = useState("");
  const [brand, setBrand] = useState("");

  // Состояние редактора полей (drag-and-drop)
  const [fieldOrder, setFieldOrder] = useState<FieldConfig[]>([
    { id: "serial_number", label: "№ п/п (0001, 0002...)", preview: null, enabled: false },
    { id: "inn", label: "ИНН", preview: null, enabled: false },
    { id: "organization", label: "Организация", preview: null, enabled: true },
    { id: "name", label: "Название товара", preview: null, enabled: true },
    { id: "article", label: "Артикул", preview: null, enabled: true },
    { id: "size_color", label: "Размер / Цвет", preview: null, enabled: true },
    { id: "country", label: "Страна", preview: null, enabled: false },
    { id: "composition", label: "Состав", preview: null, enabled: false },
    { id: "chz_code_text", label: "Код ЧЗ текстом", preview: null, enabled: false },
  ]);

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
  const [errorHint, setErrorHint] = useState<string | null>(null);

  // Прогресс генерации (Fix 7)
  const [generationPhase, setGenerationPhase] = useState<GenerationPhase>("idle");
  const [generationProgress, setGenerationProgress] = useState(0);
  const [preflightChecks, setPreflightChecks] = useState<PreflightCheck[]>([]);

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
      setInn(prefs.inn || "");
      setOrganizationAddress(prefs.organization_address || "");
      setProductionCountry(prefs.production_country || "");
      setCertificateNumber(prefs.certificate_number || "");
      setLabelLayout(prefs.preferred_layout);
      setLabelSize(prefs.preferred_label_size);
      setLabelFormat(prefs.preferred_format);
      setShowArticle(prefs.show_article);
      setShowSizeColor(prefs.show_size_color);
      setShowName(prefs.show_name);
    } catch {
      // Настройки не критичны — используем дефолтные
      console.error("Ошибка загрузки настроек");
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
   * Обновляем fieldOrder из fileDetectionResult — показываем только поля с данными.
   * Новые поля (organization, inn, serial_number, chz_code_text) добавляются как опциональные.
   */
  useEffect(() => {
    if (fileDetectionResult?.sample_items?.[0]) {
      const sample = fileDetectionResult.sample_items[0];

      // Собираем поля динамически — только те, у которых есть данные
      const newFields: FieldConfig[] = [];

      // Серийный номер (всегда добавляем как опцию, выключен по умолчанию)
      newFields.push({ id: "serial_number", label: "№ п/п (0001, 0002...)", preview: "№ 0001", enabled: false });

      // ИНН (опционально, выключен по умолчанию)
      newFields.push({ id: "inn", label: "ИНН", preview: inn ? `ИНН: ${inn}` : "ИНН: 123456789012", enabled: false });

      // Организация (включена по умолчанию если есть organizationName)
      newFields.push({
        id: "organization",
        label: "Организация",
        preview: organizationName || "ИП Иванов И.И.",
        enabled: !!organizationName,
      });

      // Название (всегда показываем если есть)
      if (sample.name) {
        newFields.push({ id: "name", label: "Название товара", preview: sample.name, enabled: true });
      } else {
        newFields.push({ id: "name", label: "Название товара", preview: null, enabled: true });
      }

      // Артикул
      if (sample.article) {
        newFields.push({ id: "article", label: "Артикул", preview: `Артикул: ${sample.article}`, enabled: true });
      } else {
        newFields.push({ id: "article", label: "Артикул", preview: null, enabled: true });
      }

      // Размер/Цвет
      const sizeColorParts = [];
      if (sample.color) sizeColorParts.push(`Цв: ${sample.color}`);
      if (sample.size) sizeColorParts.push(`Раз: ${sample.size}`);
      newFields.push({
        id: "size_color",
        label: "Размер / Цвет",
        preview: sizeColorParts.length > 0 ? sizeColorParts.join(" / ") : null,
        enabled: sizeColorParts.length > 0,
      });

      // Страна — только если есть в данных
      newFields.push({
        id: "country",
        label: "Страна",
        preview: sample.country || null,
        enabled: !!sample.country,
      });

      // Состав — только если есть в данных
      newFields.push({
        id: "composition",
        label: "Состав",
        preview: sample.composition || null,
        enabled: !!sample.composition,
      });

      // Код ЧЗ текстом (опционально, выключен по умолчанию)
      newFields.push({ id: "chz_code_text", label: "Код ЧЗ текстом", preview: "0104600439930...", enabled: false });

      setFieldOrder(newFields);
    }
  }, [fileDetectionResult, organizationName, inn]);

  /**
   * Синхронизация show* флагов с fieldOrder.
   * Когда пользователь включает/выключает поле в редакторе — обновляем соответствующий флаг.
   */
  useEffect(() => {
    const getFieldEnabled = (id: string) => fieldOrder.find((f) => f.id === id)?.enabled ?? false;

    setShowName(getFieldEnabled("name"));
    setShowArticle(getFieldEnabled("article"));
    setShowSizeColor(getFieldEnabled("size_color"));
    setShowOrganization(getFieldEnabled("organization"));
    setShowInn(getFieldEnabled("inn"));
    setShowCountry(getFieldEnabled("country"));
    setShowComposition(getFieldEnabled("composition"));
    setShowChzCodeText(getFieldEnabled("chz_code_text"));
    setShowSerialNumber(getFieldEnabled("serial_number"));
  }, [fieldOrder]);

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
   * Обработчик сохранения данных организации из модалки.
   */
  const handleOrganizationSave = (data: OrganizationData) => {
    setOrganizationName(data.organizationName);
    setInn(data.inn);
    setOrganizationAddress(data.organizationAddress);
    setProductionCountry(data.productionCountry);
    setCertificateNumber(data.certificateNumber);
    setImporter(data.importer);
    setManufacturer(data.manufacturer);
    setProductionDate(data.productionDate);
    setBrand(data.brand);
    // Включаем соответствующие флаги, если данные заполнены
    setShowOrganization(!!data.organizationName);
    setShowInn(!!data.inn);
    setShowAddress(!!data.organizationAddress);
    setShowCountry(!!data.productionCountry);
    setShowCertificate(!!data.certificateNumber);
    setShowImporter(!!data.importer);
    setShowManufacturer(!!data.manufacturer);
    setShowProductionDate(!!data.productionDate);
    setShowBrand(!!data.brand);
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
      name: sample?.name || "Товар",
      organization: organizationName || "ИП Иванов И.И.",
      country: productionCountry || sample?.country || undefined,
      composition: sample?.composition || undefined,
      inn: inn || undefined,
      address: organizationAddress || undefined,
      certificate: certificateNumber || undefined,
      productionDate: productionDate || undefined,
      importer: importer || undefined,
      manufacturer: manufacturer || undefined,
      brand: brand || undefined,
    };
  }, [fileDetectionResult, organizationName, inn, organizationAddress, productionCountry, certificateNumber, productionDate, importer, manufacturer, brand]);

  /**
   * Генерация этикеток с прогрессом.
   */
  const handleGenerate = async () => {
    // Проверка входных данных
    if (!uploadedFile || !fileType) {
      setError("Загрузите файл (PDF или Excel)");
      setErrorHint("Перетащите файл в зону загрузки или нажмите для выбора");
      return;
    }

    if (fileType === "excel" && !selectedColumn) {
      setError("Выберите колонку с баркодами");
      setErrorHint("Укажите, в какой колонке находятся баркоды товаров");
      return;
    }

    const codes = parseCodes(codesText);
    if (codes.length === 0) {
      setError("Введите коды маркировки");
      setErrorHint("Скачайте коды из личного кабинета ЧЗ (crpt.ru) и вставьте их в поле");
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);
      setErrorHint(null);
      setGenerationResult(null);
      setPreflightChecks([]);

      // Фаза 1: Валидация
      setGenerationPhase("validating");
      setGenerationProgress(10);

      // Небольшая задержка для отображения прогресса
      await new Promise((resolve) => setTimeout(resolve, 300));
      setGenerationProgress(25);

      let result: GenerateLabelsResponse | GenerateFromExcelResponse;

      // Фаза 2: Генерация
      setGenerationPhase("generating");
      setGenerationProgress(40);

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
          // Данные организации
          organizationName: organizationName || undefined,
          inn: inn || undefined,
          organizationAddress: organizationAddress || undefined,
          productionCountry: productionCountry || undefined,
          certificateNumber: certificateNumber || undefined,
          // Профессиональный шаблон
          importer: importer || undefined,
          manufacturer: manufacturer || undefined,
          productionDate: productionDate || undefined,
          // Флаги базового шаблона
          showArticle: showArticle,
          showSizeColor: showSizeColor,
          showName: showName,
          showOrganization: showOrganization,
          showInn: showInn,
          showCountry: showCountry,
          showComposition: showComposition,
          // Флаги профессионального шаблона
          showBrand: showBrand,
          showImporter: showImporter,
          showManufacturer: showManufacturer,
          showAddress: showAddress,
          showProductionDate: showProductionDate,
          showCertificate: showCertificate,
        });
      }

      setGenerationProgress(70);

      // Фаза 3: Проверка качества
      setGenerationPhase("checking");
      setGenerationProgress(85);

      // Сохраняем preflight проверки
      if (result.preflight?.checks) {
        setPreflightChecks(result.preflight.checks);
      }

      await new Promise((resolve) => setTimeout(resolve, 300));
      setGenerationProgress(100);

      // Фаза 4: Завершение
      setGenerationPhase("complete");
      setGenerationResult(result as GenerateLabelsResponse);

      // Обновляем статистику после генерации (для триггеров конверсии)
      await fetchUserStats();

      // Проверяем, нужно ли показать модал обратной связи
      // Показываем на 3-й генерации, потом не чаще раза в 7 дней
      if (result.success && !feedbackSubmitted) {
        const currentCount = parseInt(
          localStorage.getItem("kleykod_generation_count") || "0",
          10
        );
        const newCount = currentCount + 1;
        localStorage.setItem("kleykod_generation_count", String(newCount));

        const lastShown = localStorage.getItem("kleykod_feedback_last_shown");
        const lastShownTime = lastShown ? parseInt(lastShown, 10) : 0;
        const now = Date.now();
        const sevenDays = 7 * 24 * 60 * 60 * 1000;

        // Показываем если: ровно 3-я генерация ИЛИ прошло больше 7 дней с последнего показа
        const shouldShow = newCount === 3 || (newCount > 3 && now - lastShownTime > sevenDays);

        if (shouldShow) {
          localStorage.setItem("kleykod_feedback_last_shown", String(now));
          setShowFeedbackModal(true);
        }
      }
    } catch (err) {
      setGenerationPhase("error");
      const errorMessage = err instanceof Error ? err.message : "Ошибка генерации";
      setError(errorMessage);

      // Добавляем дружелюбные подсказки в зависимости от ошибки
      if (errorMessage.includes("формат") || errorMessage.includes("PDF")) {
        setErrorHint("Проверьте, что скачали файл из WB, а не скриншот. Формат: .pdf, .xlsx, .xls");
      } else if (errorMessage.includes("код") || errorMessage.includes("DataMatrix")) {
        setErrorHint("Убедитесь, что файл содержит коды маркировки из crpt.ru. Коды начинаются с 01 и содержат 31+ символ");
      } else if (errorMessage.includes("количество")) {
        setErrorHint("Проверьте, все ли коды маркировки на месте. Количество должно совпадать");
      } else {
        setErrorHint("Попробуйте ещё раз. Если ошибка повторяется, обратитесь в поддержку");
      }
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

      {/* Ошибка валидации (Fix 5 - дружелюбные ошибки) */}
      {error && !isGenerating && (
        <ErrorCard
          message={error}
          hint={errorHint || undefined}
          onRetry={() => {
            setError(null);
            setErrorHint(null);
            setGenerationPhase("idle");
          }}
          onDismiss={() => {
            setError(null);
            setErrorHint(null);
          }}
        />
      )}

      {/* Прогресс генерации (Fix 7) */}
      {isGenerating && (
        <Card className="border-2 border-emerald-200 bg-emerald-50/30">
          <CardContent className="pt-6">
            <GenerationProgress
              phase={generationPhase}
              progress={generationProgress}
              checks={preflightChecks}
            />
          </CardContent>
        </Card>
      )}

      {/* Результат генерации - ошибка (Fix 5) */}
      {generationResult && !generationResult.success && !isGenerating && (
        <ErrorCard
          message={generationResult.message || "Ошибка генерации"}
          hint={
            generationResult.preflight?.checks?.filter((c) => c.status === "error").length
              ? generationResult.preflight.checks
                  .filter((c) => c.status === "error")
                  .map((c) => c.message)
                  .join(". ")
              : "Попробуйте ещё раз или обратитесь в поддержку"
          }
          onRetry={handleGenerate}
        />
      )}

      {/* Результат генерации - успех */}
      {generationResult && generationResult.success && !isGenerating && (
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

              {/* Сводка проверок качества (Fix 4) */}
              {generationResult.preflight?.checks && generationResult.preflight.checks.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-warm-gray-700 mb-2">Проверка качества:</p>
                  <PreflightSummary checks={generationResult.preflight.checks} />
                </div>
              )}

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

      {/* Шаг 1: Загрузка файла с автодетектом (скрыто при генерации) */}
      {!isGenerating && !uploadedFile && (
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

      {/* Превью загруженного PDF файла (скрыто при генерации) */}
      {!isGenerating && uploadedFile && fileType === "pdf" && (
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

      {/* Превью Excel файла + выбор колонки (скрыто при генерации) */}
      {!isGenerating && uploadedFile && fileType === "excel" && fileDetectionResult && (
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

      {/* Настройки дизайна этикетки — показываем для Excel после выбора колонки (скрыто при генерации) */}
      {!isGenerating && uploadedFile && fileType === "excel" && selectedColumn && (
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
              {/* Левая колонка — поля с drag-and-drop */}
              <FieldOrderEditor
                fields={fieldOrder}
                onChange={setFieldOrder}
              />

              {/* Правая колонка — организация, ИНН, размер */}
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
                    Отображается на этикетке
                  </p>
                </div>

                {/* ИНН */}
                <div>
                  <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                    ИНН организации
                    <span className="text-warm-gray-400 font-normal ml-1">(опционально)</span>
                  </label>
                  <input
                    type="text"
                    value={inn}
                    onChange={(e) => setInn(e.target.value.replace(/\D/g, "").slice(0, 12))}
                    placeholder="123456789012"
                    maxLength={12}
                    className="w-full px-4 py-2.5 rounded-xl border border-warm-gray-300 bg-white
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                  <p className="text-xs text-warm-gray-500 mt-1">
                    10 или 12 цифр. Включите поле «ИНН» слева чтобы отобразить.
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

            {/* Кнопка реквизитов организации (для профессионального шаблона) */}
            {labelLayout === "professional" && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <Building2 className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-amber-800 mb-1">
                      Профессиональный шаблон
                    </p>
                    <p className="text-sm text-amber-700 mb-3">
                      Добавьте реквизиты организации для отображения на этикетке
                    </p>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowOrganizationModal(true)}
                    >
                      <Building2 className="w-4 h-4 mr-2" />
                      {organizationName ? "Изменить реквизиты" : "Добавить реквизиты"}
                    </Button>
                    {organizationName && (
                      <p className="text-xs text-amber-600 mt-2">
                        Заполнено: {organizationName}
                        {inn && `, ИНН ${inn}`}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

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
                    showOrganization={showOrganization}
                    showCountry={showCountry}
                    showComposition={showComposition}
                    showInn={showInn}
                    showAddress={showAddress}
                    showCertificate={showCertificate}
                    showProductionDate={showProductionDate}
                    showImporter={showImporter}
                    showManufacturer={showManufacturer}
                    showBrand={showBrand}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Выбор формата этикеток (скрыто при генерации) */}
      {!isGenerating && (
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
      )}

      {/* Ввод кодов маркировки (скрыто при генерации) */}
      {!isGenerating && (
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
      )}

      {/* Кнопка генерации (скрыто при генерации) */}
      {!isGenerating && (
        <div className="flex justify-end gap-4">
          <Button
            variant="primary"
            size="lg"
            onClick={handleGenerate}
            disabled={
              codesCount === 0 ||
              !uploadedFile ||
              (fileType === "excel" && !selectedColumn)
            }
          >
            <CheckCircle className="w-5 h-5" />
            Создать этикетки
          </Button>
        </div>
      )}

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

      {/* Модал реквизитов организации */}
      <OrganizationModal
        isOpen={showOrganizationModal}
        onClose={() => setShowOrganizationModal(false)}
        onSave={handleOrganizationSave}
        initialData={{
          organizationName,
          inn,
          organizationAddress,
          productionCountry,
          certificateNumber,
          importer,
          manufacturer,
          productionDate,
          brand,
        }}
      />
    </div>
  );
}
