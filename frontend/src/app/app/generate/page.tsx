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
  getUserStats,
  submitFeedback,
  getFeedbackStatus,
  generateFromExcel,
  getUserPreferences,
  updateUserPreferences,
  getProductsCount,
  getMaxSerialNumber,
  preflightMatching,
} from "@/lib/api";
import type { GtinPreflightResponse } from "@/lib/api";
import { ProductCardsHint } from "@/components/app/generate/product-cards-hint";
import { GtinMatchingBlock } from "@/components/app/generate/gtin-matching-block";
import { TextOverflowWarning } from "@/components/app/generate/text-overflow-warning";
import type { LayoutPreflightError } from "@/lib/api";
import type { GtinMatchingStatus, GtinMatchingError } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import type {
  GenerateLabelsResponse,
  LabelLayout,
  LabelSize,
  FileDetectionResult,
  PreflightCheck,
  NumberingMode,
} from "@/lib/api";
import type { UserStats } from "@/types/api";
import { LayoutSelector } from "@/components/app/generate/layout-selector";
import {
  LabelCanvas,
  type LabelCanvasData,
} from "@/components/app/generate/label-canvas";
import {
  UnifiedDropzone,
  type FileType,
} from "@/components/app/generate/unified-dropzone";
import { type CustomLine } from "@/components/app/generate/extended-fields-editor";
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
import { BackgroundTaskProgress } from "@/components/app/generate/background-task-progress";
import type { TaskStatusResponse } from "@/lib/api";
import { DataValidationCard } from "@/components/app/generate/data-validation-card";
import { ProductsStatusBar } from "@/components/app/generate/products-status-bar";
import { analytics } from "@/lib/analytics";
import {
  FileText,
  Info,
  AlertTriangle,
  CheckCircle,
  Download,
  X,
  FileSpreadsheet,
  Layers,
  Check,
  Building2,
  Scissors,
  ChevronDown,
  ChevronUp,
  Hash,
} from "lucide-react";

export default function GeneratePage() {
  const { user, refresh: refreshUser } = useAuth();
  const { showToast } = useToast();

  // Загруженный файл Excel
  const [fileType, setFileType] = useState<FileType | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [fileDetectionResult, setFileDetectionResult] =
    useState<FileDetectionResult | null>(null);

  // Выбранная колонка с баркодами
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

  // Организация ВСЕГДА показывается (обязательное поле)
  const showOrganization = true;

  // Toggles отображения (управляются пользователем)
  const [showInn, setShowInn] = useState(true);
  const [showAddress, setShowAddress] = useState(true);

  // Флаги отображения полей (все включены — данные из Excel)
  const showArticle = true;
  const showSizeColor = true;
  const showName = true;
  const showCountry = true;
  const showComposition = true;
  const showBrand = true;
  const showImporter = true;
  const showManufacturer = true;
  const showProductionDate = true;
  const showCertificate = true;

  // Значения полей (пустые, данные берутся из Excel)
  const importer = "";
  const manufacturer = "";
  const productionDate = "";
  const brand = "";

  // Состояние кодов маркировки (только PDF файл)
  const [codesFile, setCodesFile] = useState<File | null>(null);

  // "Ножницы" — диапазон печати
  const [useRange, setUseRange] = useState(false);
  const [rangeStart, setRangeStart] = useState<number>(1);
  const [rangeEnd, setRangeEnd] = useState<number>(1);

  // Режим нумерации
  const [numberingMode, setNumberingMode] = useState<NumberingMode>("none");
  const [startNumber, setStartNumber] = useState<number>(1);
  // Глобальный счётчик (last_label_number + 1)
  const [globalNextNumber, setGlobalNextNumber] = useState<number>(1);
  // Per-product счётчик из карточек товаров (только PRO)
  const [perProductNextNumber, setPerProductNextNumber] = useState<number>(1);
  // Legacy: для совместимости (setter используется, значение — нет)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_suggestedStartNumber, setSuggestedStartNumber] = useState<number>(1);

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

  // Async обработка (Celery для больших файлов)
  const [asyncTaskId, setAsyncTaskId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_asyncEstimatedSeconds, setAsyncEstimatedSeconds] = useState<number | null>(null);

  // Ошибки preflight проверки полей
  const [fieldErrors, setFieldErrors] = useState<Map<string, LayoutPreflightError>>(new Map());
  const [preflightSuggestions, setPreflightSuggestions] = useState<string[]>([]);

  // Статистика использования (для триггеров конверсии)
  const [userStats, setUserStats] = useState<UserStats | null>(null);

  // Состояние модала обратной связи
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // Состояние сворачивания блока "Как это работает"
  const [howItWorksExpanded, setHowItWorksExpanded] = useState(false);

  // Состояние для hint о карточках товаров
  const [showProductCardsHint, setShowProductCardsHint] = useState(false);
  const [hasSeenCardsHint, setHasSeenCardsHint] = useState(true); // По умолчанию скрыт

  // Ref для скрытого input файла с кодами
  const codesInputRef = useRef<HTMLInputElement>(null);

  // GTIN матчинг (preflight — до генерации)
  const [gtinPreflightResponse, setGtinPreflightResponse] = useState<GtinPreflightResponse | null>(null);
  const [isPreflightLoading, setIsPreflightLoading] = useState(false);
  const [gtinMatchingStatus, setGtinMatchingStatus] = useState<GtinMatchingStatus | null>(null);
  const [gtinMatchingError, setGtinMatchingError] = useState<GtinMatchingError | null>(null);
  const [gtinMapping, setGtinMapping] = useState<Map<string, number>>(new Map());

  // Text overflow warnings
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [textTruncations, setTextTruncations] = useState<Array<{
    field: string;
    original: string;
    maxChars: number;
  }>>([]);
  const [showTruncationWarning, setShowTruncationWarning] = useState(false);

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
      // Загружаем флаг показа hint о карточках товаров
      setHasSeenCardsHint(prefs.has_seen_cards_hint ?? true);
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
   * Проверяем условия для показа hint о карточках товаров.
   * Показываем если:
   * - PRO или ENTERPRISE план
   * - Карточек товаров = 0
   * - Пользователь ещё не видел hint (!hasSeenCardsHint)
   */
  useEffect(() => {
    const checkProductCardsHint = async () => {
      // Не показываем FREE пользователям
      if (!user || user.plan === "free") {
        setShowProductCardsHint(false);
        return;
      }

      // Если уже видел hint — не показываем
      if (hasSeenCardsHint) {
        setShowProductCardsHint(false);
        return;
      }

      // Проверяем количество карточек
      try {
        const { count } = await getProductsCount();
        // Показываем hint только если карточек нет
        setShowProductCardsHint(count === 0);
      } catch {
        // При ошибке не показываем hint
        setShowProductCardsHint(false);
      }
    };

    checkProductCardsHint();
  }, [user, hasSeenCardsHint]);

  // Автосброс размера на 58x40 при смене на professional/extended (только 58x40 поддерживается)
  useEffect(() => {
    if ((labelLayout === "professional" || labelLayout === "extended") && labelSize !== "58x40") {
      setLabelSize("58x40");
    }
  }, [labelLayout, labelSize]);


  // Флаг что настройки загружены (чтобы не сохранять при первом рендере)
  const preferencesLoadedRef = useRef(false);

  // Автосохранение организации и ИНН в настройки (с debounce)
  useEffect(() => {
    // Пропускаем первый рендер и рендер сразу после загрузки настроек
    if (!preferencesLoadedRef.current) {
      // Отмечаем что настройки загружены после небольшой задержки
      const timer = setTimeout(() => {
        preferencesLoadedRef.current = true;
      }, 1000);
      return () => clearTimeout(timer);
    }

    // Debounce сохранения (1.5 сек после последнего изменения)
    const saveTimer = setTimeout(async () => {
      try {
        await updateUserPreferences({
          organization_name: organizationName || null,
          inn: inn || null,
        });
      } catch {
        // Тихо игнорируем ошибки сохранения
        console.error("Ошибка автосохранения настроек");
      }
    }, 1500);

    return () => clearTimeout(saveTimer);
  }, [organizationName, inn]);


  /**
   * Автообновление rangeEnd при изменении общего количества.
   */
  useEffect(() => {
    const totalCount = fileDetectionResult?.rows_count || 0;
    if (totalCount > 0) {
      setRangeEnd(totalCount);
    }
  }, [fileDetectionResult?.rows_count]);

  /**
   * Автоматический вызов preflight-matching когда оба файла загружены.
   * Показывает блок матчинга ДО генерации.
   */
  useEffect(() => {
    // Нужны оба файла
    if (!uploadedFile || !codesFile) {
      // Сброс preflight при удалении файлов
      setGtinPreflightResponse(null);
      setGtinMatchingStatus(null);
      setGtinMapping(new Map());
      return;
    }

    const runPreflight = async () => {
      setIsPreflightLoading(true);
      try {
        const response = await preflightMatching(
          uploadedFile,
          codesFile,
          selectedColumn || undefined
        );
        setGtinPreflightResponse(response);
        setGtinMatchingStatus(response.status);

        // Инициализируем маппинг из авто-маппинга
        if (response.auto_mapping) {
          const mapping = new Map<string, number>();
          for (const [gtin, idx] of Object.entries(response.auto_mapping)) {
            mapping.set(gtin, idx);
          }
          setGtinMapping(mapping);
        }
      } catch (err) {
        console.error("Ошибка preflight-matching:", err);
        // Не показываем ошибку — preflight опционален
      } finally {
        setIsPreflightLoading(false);
      }
    };

    runPreflight();
  }, [uploadedFile, codesFile, selectedColumn]);

  /**
   * Глобальный счётчик из профиля пользователя.
   */
  useEffect(() => {
    if (!user) {
      setGlobalNextNumber(1);
      setSuggestedStartNumber(1);
      return;
    }

    const nextNumber = (user.last_label_number || 0) + 1;
    setGlobalNextNumber(nextNumber);
    setSuggestedStartNumber(nextNumber);
  }, [user]);

  /**
   * Per-product счётчик из карточек товаров (только PRO/ENTERPRISE).
   */
  useEffect(() => {
    let isMounted = true;

    const fetchPerProductNumber = async () => {
      // Только для PRO/ENTERPRISE
      if (!user || user.plan === "free") {
        if (isMounted) setPerProductNextNumber(1);
        return;
      }

      // Только если есть загруженный файл с баркодами
      if (!fileDetectionResult?.sample_items?.length) {
        if (isMounted) setPerProductNextNumber(1);
        return;
      }

      try {
        const barcodes = fileDetectionResult.sample_items
          .map((item) => item.barcode)
          .filter(Boolean);

        if (barcodes.length === 0) {
          if (isMounted) setPerProductNextNumber(1);
          return;
        }

        const result = await getMaxSerialNumber(barcodes);
        if (isMounted) {
          setPerProductNextNumber(result.suggested_start);
        }
      } catch {
        if (isMounted) setPerProductNextNumber(1);
      }
    };

    fetchPerProductNumber();
    return () => { isMounted = false; };
  }, [user, fileDetectionResult?.sample_items]);

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
   * Обработчик автодетекта файла Excel.
   * Вызывается из UnifiedDropzone после определения типа.
   *
   * Приоритет заполнения полей:
   * 1. Данные из Excel (если колонка есть)
   * 2. Данные из карточки товара (будут подтянуты на бэкенде по баркоду)
   * 3. Данные из настроек пользователя (организация, ИНН — уже загружены)
   * 4. Пустое значение — user заполняет в UI
   */
  const handleFileDetected = useCallback(
    (result: FileDetectionResult, file: File) => {
      // Принимаем только Excel файлы
      if (result.file_type !== "excel") {
        setError("Пожалуйста, загрузите Excel файл с баркодами (.xlsx, .xls)");
        return;
      }

      setUploadedFile(file);
      setFileDetectionResult(result);
      setFileType("excel");
      setError(null);
      setGenerationResult(null);

      // Трекинг загрузки файла
      analytics.fileUpload();

      // Автоматически выбираем рекомендуемую колонку
      if (result.detected_barcode_column) {
        setSelectedColumn(result.detected_barcode_column);
      } else if (result.columns && result.columns.length > 0) {
        setSelectedColumn(result.columns[0]);
      }

      // Автозаполнение полей из Excel обрабатывается в useEffect по fileDetectionResult
    },
    []
  );

  /**
   * Удаление загруженного файла.
   */
  const removeUploadedFile = useCallback(() => {
    setUploadedFile(null);
    setFileType(null);
    setFileDetectionResult(null);
    setSelectedColumn(null);
    setGenerationResult(null);
    setError(null);
  }, []);

  /**
   * Обработчик загрузки файла с кодами ЧЗ (PDF, CSV, Excel).
   */
  const handleCodesFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.toLowerCase().split(".").pop();
    const allowedExtensions = ["pdf", "csv", "xlsx", "xls"];

    if (!ext || !allowedExtensions.includes(ext)) {
      setError("Неподдерживаемый формат файла");
      setErrorHint("Загрузите PDF, CSV или Excel (.xlsx) с кодами маркировки");
      return;
    }

    setCodesFile(file);
    setError(null);
    setErrorHint(null);
  };

  /**
   * Удаление файла с кодами.
   */
  const removeCodesFile = () => {
    setCodesFile(null);
    if (codesInputRef.current) {
      codesInputRef.current.value = "";
    }
  };

  /**
   * Сброс файлов и возврат к dropzone.
   * Используется при ошибках, требующих перезагрузки файлов.
   */
  const handleReloadFiles = useCallback(() => {
    // Сброс файлов
    setUploadedFile(null);
    setFileType(null);
    setFileDetectionResult(null);
    setSelectedColumn(null);
    setCodesFile(null);
    if (codesInputRef.current) {
      codesInputRef.current.value = "";
    }
    // Сброс ошибок
    setError(null);
    setErrorHint(null);
    setGenerationResult(null);
    setFieldErrors(new Map());
    setPreflightSuggestions([]);
    // Сброс прогресса
    setGenerationPhase("idle");
    setGenerationProgress(0);
  }, []);

  /**
   * Обработчик сохранения данных организации из модалки.
   */
  const handleOrganizationSave = (data: OrganizationData) => {
    // Обновляем организационные данные
    setOrganizationName(data.organizationName);
    setInn(data.inn);
    setOrganizationAddress(data.organizationAddress);
    setProductionCountry(data.productionCountry);
    setCertificateNumber(data.certificateNumber);
  };

  /**
   * Данные для превью этикетки на Fabric.js canvas (из первой строки Excel).
   */
  const previewData: LabelCanvasData = useMemo(() => {
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
   * Кастомные строки для Extended шаблона (пока пустые).
   */
  const customLines: CustomLine[] = [];

  /**
   * Обработчик dismiss для hint о карточках товаров.
   * Скрывает hint и сохраняет в preferences.
   */
  const handleDismissProductCardsHint = useCallback(async () => {
    setShowProductCardsHint(false);
    setHasSeenCardsHint(true);

    try {
      await updateUserPreferences({ has_seen_cards_hint: true });
    } catch {
      // Тихо игнорируем ошибку — UI уже скрылся
      console.error("Ошибка сохранения has_seen_cards_hint");
    }
  }, []);

  /**
   * Обработчик изменения маппинга GTIN → товар.
   */
  const handleGtinMappingChange = useCallback((gtin: string, itemIndex: number | null) => {
    setGtinMapping(prev => {
      const next = new Map(prev);
      if (itemIndex === null) {
        next.delete(gtin);
      } else {
        next.set(gtin, itemIndex);
      }
      return next;
    });
  }, []);

  /**
   * Генерация этикеток с прогрессом.
   * @param forceGenerate Игнорировать несовпадение количества (HITL подтверждение)
   */
  const handleGenerate = async (forceGenerate: boolean = false) => {
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

    if (!codesFile) {
      setError("Загрузите PDF с кодами маркировки");
      setErrorHint("Скачайте PDF из личного кабинета Честного Знака (crpt.ru)");
      return;
    }

    if (!organizationName.trim()) {
      setError("Введите название организации");
      setErrorHint("Это обязательное поле — укажите ИП, ООО или другую организацию");
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);
      setErrorHint(null);
      setGenerationResult(null);
      setPreflightChecks([]);
      setFieldErrors(new Map()); // Сбрасываем ошибки полей
      setPreflightSuggestions([]); // Сбрасываем предложения

      // Трекинг начала генерации
      analytics.generationStart();

      // Фаза 1: Валидация
      setGenerationPhase("validating");
      setGenerationProgress(10);


      // Небольшая задержка для отображения прогресса
      await new Promise((resolve) => setTimeout(resolve, 300));
      setGenerationProgress(25);

      // Фаза 2: Генерация
      setGenerationPhase("generating");
      setGenerationProgress(40);

      // Генерация из Excel с баркодами
      const result = await generateFromExcel({
        excelFile: uploadedFile,
        codesFile: codesFile,
        barcodeColumn: selectedColumn!,
        layout: labelLayout,
        labelSize: labelSize,
        labelFormat: "combined", // Только объединённый формат
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
        showSize: showSizeColor,
        showColor: showSizeColor,
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
        // Диапазон печати (ножницы)
        rangeStart: useRange ? rangeStart : undefined,
        rangeEnd: useRange ? rangeEnd : undefined,
        // HITL: игнорировать несовпадение количества
        forceGenerate: forceGenerate,
        // Extended шаблон: дополнительные строки
        customLines: labelLayout === "extended" ? customLines : undefined,
        // Режим нумерации этикеток (continue_per_product -> continue для API)
        numberingMode: numberingMode === "continue_per_product" ? "continue" : numberingMode,
        startNumber: (numberingMode === "continue" || numberingMode === "continue_per_product") ? startNumber : undefined,
        // Ручной маппинг GTIN → индекс товара (для manual_required)
        manualGtinMapping: gtinMapping.size > 0 ? gtinMapping : undefined,
      });

      // === ASYNC MODE: Задача отправлена в Celery ===
      if (result.is_async && result.task_id) {
        setAsyncTaskId(result.task_id);
        setAsyncEstimatedSeconds(result.estimated_seconds || null);
        setIsGenerating(false);
        setGenerationPhase("idle");

        // Показываем toast
        showToast({
          message: "Задача отправлена на обработку",
          description: `~${Math.ceil((result.estimated_seconds || 60) / 60)} мин. Отслеживайте прогресс ниже.`,
          type: "info",
        });
        return;
      }

      // === SYNC MODE: Обычная обработка для небольших файлов ===
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

      // Трекинг успешной генерации
      analytics.generationComplete();

      // Обновляем статистику и профиль после генерации
      await fetchUserStats();
      await refreshUser();

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

      // Проверяем на ошибку GTIN матчинга
      if (err instanceof Error) {
        // Пробуем распарсить JSON ошибку (backend возвращает 422 с gtin_matching_error)
        try {
          const errorData = JSON.parse(err.message);
          if (errorData.gtin_matching_error) {
            const gtinError = errorData.gtin_matching_error as GtinMatchingError;
            setGtinMatchingError(gtinError);
            setGtinMatchingStatus(gtinError.can_manual_match ? "manual_required" : "error");
            setError(gtinError.message);
            setErrorHint("Выберите соответствие товаров и GTIN из кодов ЧЗ ниже");
            return; // Не показываем обычную ошибку
          }
        } catch {
          // Не JSON — обрабатываем как обычную ошибку
        }
      }

      const errorMessage = err instanceof Error ? err.message : "Ошибка генерации";
      setError(errorMessage);

      // Трекинг ошибки генерации
      analytics.generationError();

      // Добавляем дружелюбные подсказки в зависимости от ошибки
      setErrorHint(getErrorHint(errorMessage));
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Скачивание результата.
   */
  const handleDownload = () => {
    // Трекинг скачивания результата
    analytics.downloadResult();

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
  };

  /**
   * Обработчик завершения async задачи (Celery).
   */
  const handleAsyncTaskComplete = useCallback(async (taskStatus: TaskStatusResponse) => {
    setAsyncTaskId(null);
    setAsyncEstimatedSeconds(null);

    // Создаём результат для UI
    const asyncResult: GenerateLabelsResponse = {
      success: true,
      labels_count: taskStatus.labels_count || 0,
      pages_count: taskStatus.labels_count || 0,
      label_format: "combined",
      preflight: null,
      download_url: taskStatus.result_url,
      file_id: null,
      message: `Готово! Создано ${taskStatus.labels_count || 0} этикеток`,
    };

    setGenerationResult(asyncResult);

    // Трекинг
    analytics.generationComplete();

    // Обновляем статистику и профиль
    await fetchUserStats();
    await refreshUser();

    showToast({
      message: "Генерация завершена!",
      description: `Создано ${taskStatus.labels_count || 0} этикеток`,
      type: "success",
    });
  }, [fetchUserStats, refreshUser, showToast]);

  /**
   * Получить дружелюбную подсказку по ошибке.
   */
  const getErrorHint = (errorMessage: string): string => {
    if (errorMessage.includes("Не найдены товары для баркодов") || errorMessage.includes("не найден товар")) {
      return "В PDF есть коды маркировки для товаров, которых нет в Excel. " +
        "Добавьте недостающие товары в Excel файл или используйте другой PDF.";
    } else if (errorMessage.includes("формат") || errorMessage.includes("PDF")) {
      return "Проверьте, что скачали файл из WB, а не скриншот. Формат: .pdf, .xlsx, .xls";
    } else if (errorMessage.includes("код") || errorMessage.includes("DataMatrix")) {
      return "Убедитесь, что файл содержит коды маркировки из crpt.ru. Коды начинаются с 01 и содержат 31+ символ";
    } else if (errorMessage.includes("количество")) {
      return "Проверьте, все ли коды маркировки на месте. Количество должно совпадать";
    } else {
      return "Попробуйте ещё раз. Если ошибка повторяется, обратитесь в поддержку";
    }
  };

  /**
   * Обработчик ошибки async задачи (Celery).
   */
  const handleAsyncTaskError = useCallback((errorMessage: string) => {
    setAsyncTaskId(null);
    setAsyncEstimatedSeconds(null);
    setError(errorMessage);
    setErrorHint(getErrorHint(errorMessage));

    // Трекинг
    analytics.generationError();
  }, []);

  /**
   * Скачивание результата async задачи.
   */
  const handleAsyncDownload = useCallback((resultUrl: string) => {
    analytics.downloadResult();
    window.open(resultUrl, "_blank");
  }, []);

  /**
   * Повторная попытка async генерации.
   */
  const handleAsyncRetry = useCallback(() => {
    setAsyncTaskId(null);
    setAsyncEstimatedSeconds(null);
    setError(null);
    setErrorHint(null);
    handleGenerate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

      {/* Информация — сворачиваемый блок */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg overflow-hidden">
        <button
          onClick={() => setHowItWorksExpanded(!howItWorksExpanded)}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-emerald-100/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Info className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span className="font-medium text-emerald-800">Как это работает?</span>
          </div>
          {howItWorksExpanded ? (
            <ChevronUp className="w-5 h-5 text-emerald-600" />
          ) : (
            <ChevronDown className="w-5 h-5 text-emerald-600" />
          )}
        </button>

        {howItWorksExpanded && (
          <div className="px-4 pb-4 text-sm text-emerald-800 border-t border-emerald-200 pt-4 space-y-4">
            {/* Общее описание */}
            <p>
              Сервис создаёт этикетки со штрихкодом и кодом маркировки «Честный Знак»
              для печати на термопринтере. Загрузите Excel с баркодами из WB — мы сгенерируем
              готовые этикетки с DataMatrix.
            </p>

            {/* Режим Excel */}
            <div className="bg-white/60 rounded-lg p-3">
              <p className="font-medium text-emerald-900 mb-2 flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4" />
                Как это работает
              </p>
              <ol className="list-decimal list-inside space-y-1 text-emerald-700 ml-1">
                <li>Скачайте Excel с баркодами из WB или создайте свой файл</li>
                <li>Загрузите файл — колонка с баркодами определится автоматически</li>
                <li>Настройте дизайн: шаблон, отображаемые поля, размер этикетки</li>
                <li>Вставьте коды маркировки ЧЗ и нажмите «Создать»</li>
              </ol>
              <p className="text-xs text-emerald-600 mt-2">
                💡 Генерируем этикетки с нуля — штрихкод, артикул,
                размер/цвет, организация и DataMatrix в одном файле.
              </p>
            </div>

            {/* Проверка качества */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="font-medium text-amber-800 mb-1">
                ✅ Автоматическая проверка качества
              </p>
              <p className="text-amber-700 text-xs">
                Перед скачиванием проверяем размер DataMatrix (мин. 22×22мм)
                и контрастность — чтобы коды точно сканировались.
              </p>
            </div>
          </div>
        )}
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
          // Показываем "Загрузить заново" для ошибок данных файлов
          onReload={
            error.includes("не найден") ||
            error.includes("Не найден") ||
            error.includes("баркод") ||
            error.includes("Excel")
              ? handleReloadFiles
              : undefined
          }
          onDismiss={() => {
            setError(null);
            setErrorHint(null);
          }}
        />
      )}

      {/* Preflight ошибки полей */}
      {fieldErrors.size > 0 && !isGenerating && (
        <Card className="border-2 border-red-300 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-red-800 mb-2">
                  Проверьте данные
                </h3>
                <p className="text-sm text-red-700 mb-3">
                  Найдены проблемы в {fieldErrors.size} {fieldErrors.size === 1 ? "поле" : "полях"}.
                  Исправьте их перед генерацией.
                </p>
                <ul className="text-sm text-red-600 space-y-1 mb-4">
                  {Array.from(fieldErrors.values()).map((err, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-red-400">-</span>
                      <span>{err.message}</span>
                    </li>
                  ))}
                </ul>
                {/* Глобальные предложения */}
                {preflightSuggestions.length > 0 && (
                  <div className="bg-white/50 rounded-lg p-3 border border-red-200">
                    <p className="text-xs font-medium text-red-800 mb-1">Рекомендации:</p>
                    <ul className="text-xs text-red-700 space-y-1">
                      {preflightSuggestions.map((suggestion, idx) => (
                        <li key={idx}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="flex gap-3 mt-4">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setFieldErrors(new Map());
                      setPreflightSuggestions([]);
                    }}
                    className="border-red-300 text-red-700 hover:bg-red-100"
                  >
                    Понятно
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={handleReloadFiles}
                  >
                    Загрузить заново
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Прогресс фоновой задачи Celery (для больших файлов) */}
      {asyncTaskId && (
        <BackgroundTaskProgress
          taskId={asyncTaskId}
          onComplete={handleAsyncTaskComplete}
          onError={handleAsyncTaskError}
          onDownload={handleAsyncDownload}
          onRetry={handleAsyncRetry}
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
          onRetry={() => handleGenerate()}
          // Показываем "Загрузить заново" для ошибок данных файлов
          onReload={
            (generationResult.message || "").includes("не найден") ||
            (generationResult.message || "").includes("Не найден") ||
            (generationResult.message || "").includes("баркод") ||
            (generationResult.message || "").includes("проверку")
              ? handleReloadFiles
              : undefined
          }
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
                {generationResult.unique_products && generationResult.codes_count ? (
                  <>
                    {generationResult.unique_products} товаров × {generationResult.codes_count} кодов ЧЗ → {" "}
                  </>
                ) : null}
                <span className="font-semibold">{generationResult.labels_count} этикеток</span>
                {" • "}
                {generationResult.pages_count} страниц
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

              {/* Предупреждение о дубликатах кодов */}
              {generationResult.duplicate_warning && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-amber-800">
                        {generationResult.duplicate_warning}
                      </p>
                      <p className="text-sm text-amber-700 mt-1">
                        Эти коды уже использовались ранее. Убедитесь, что вы не печатаете дубликаты.
                      </p>
                    </div>
                  </div>
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

              <div className="flex flex-wrap gap-3">
                <Button variant="primary" size="lg" onClick={handleDownload}>
                  <Download className="w-5 h-5" />
                  Скачать PDF
                </Button>
              </div>
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

      {/* Hint о карточках товаров для PRO/ENTERPRISE */}
      {showProductCardsHint && (
        <ProductCardsHint onDismiss={handleDismissProductCardsHint} />
      )}

      {/* Шаг 1: Загрузка Excel файла (скрыто при генерации) */}
      {!isGenerating && !uploadedFile && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-emerald-600" />
              Excel с баркодами
            </CardTitle>
            <p className="text-sm text-warm-gray-500 mt-1">
              Загрузите файл с баркодами из Wildberries (.xlsx, .xls)
            </p>
          </CardHeader>
          <CardContent>
            <UnifiedDropzone onFileDetected={handleFileDetected} />
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
                      <div key={i} className="flex flex-wrap items-center gap-2 text-sm">
                        <span className="text-warm-gray-400 w-6 text-right flex-shrink-0">
                          {item.row_number}.
                        </span>
                        <code className="bg-warm-gray-100 px-3 py-1 rounded font-mono text-warm-gray-900 flex-shrink-0">
                          {item.barcode}
                        </code>
                        {item.name && (
                          <span className="text-warm-gray-700 text-xs truncate max-w-[200px]">
                            {item.name}
                          </span>
                        )}
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
                        {item.brand && (
                          <span className="text-emerald-600 text-xs">
                            {item.brand}
                          </span>
                        )}
                        {item.country && (
                          <span className="text-warm-gray-400 text-xs">
                            {item.country}
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

      {/* Информационная строка о базе товаров (скрыто при генерации) */}
      {!isGenerating && uploadedFile && fileType === "excel" && selectedColumn && user && (
        <ProductsStatusBar
          userPlan={user.plan}
          fileDetectionResult={fileDetectionResult}
        />
      )}

      {/* Информация о матчинге — показываем когда загружены оба файла */}
      {!isGenerating && uploadedFile && fileType === "excel" && selectedColumn && codesFile && (
        <Card className="border-emerald-200 bg-emerald-50/50">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                  <span className="text-warm-gray-600">Товаров в Excel:</span>
                  <span className="font-semibold text-emerald-700">
                    {fileDetectionResult?.rows_count || 0}
                  </span>
                </div>
                <div className="w-px h-4 bg-emerald-300" />
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-600" />
                  <span className="text-warm-gray-600">PDF с кодами ЧЗ:</span>
                  <span className="font-semibold text-emerald-700">загружен</span>
                </div>
              </div>
              <div className="text-xs text-emerald-600 bg-emerald-100 px-3 py-1 rounded-full">
                Количество этикеток = количество кодов ЧЗ
              </div>
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
            {/* Layout selector с Fabric.js canvas превью */}
            <LayoutSelector
              value={labelLayout}
              onChange={setLabelLayout}
              size={labelSize}
            />

            {/* Разделитель */}
            <hr className="border-warm-gray-200" />

            {/* Toggles отображения */}
            <div className="space-y-3">
              <p className="text-sm font-medium text-warm-gray-700">Отображать на этикетке</p>

              {/* Toggle ИНН */}
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showInn}
                  onChange={(e) => setShowInn(e.target.checked)}
                  disabled={!inn.trim()}
                  className="w-4 h-4 rounded border-warm-gray-300 text-emerald-600
                    focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <span className={`text-sm ${!inn.trim() ? "text-warm-gray-400" : "text-warm-gray-700"}`}>
                  ИНН организации
                  {!inn.trim() && <span className="ml-2 text-xs">(заполните ИНН ниже)</span>}
                </span>
              </label>

              {/* Toggle Адрес — только для Extended */}
              {labelLayout === "extended" && (
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showAddress}
                    onChange={(e) => setShowAddress(e.target.checked)}
                    disabled={!organizationAddress.trim()}
                    className="w-4 h-4 rounded border-warm-gray-300 text-emerald-600
                      focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                  <span className={`text-sm ${!organizationAddress.trim() ? "text-warm-gray-400" : "text-warm-gray-700"}`}>
                    Адрес организации
                    {!organizationAddress.trim() && <span className="ml-2 text-xs">(заполните в настройках)</span>}
                  </span>
                </label>
              )}
            </div>

            {/* Разделитель */}
            <hr className="border-warm-gray-200" />

            {/* Настройки организации и размера */}
            <div className="space-y-4">
                {/* Название организации — ОБЯЗАТЕЛЬНОЕ */}
                <div>
                  <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                    Название организации
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <input
                    type="text"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    placeholder="ИП Иванов И.И."
                    className={`w-full px-4 py-2.5 rounded-xl border bg-white
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                      ${!organizationName.trim() ? "border-red-300" : "border-warm-gray-300"}`}
                  />
                  <p className={`text-xs mt-1 ${!organizationName.trim() ? "text-red-500" : "text-warm-gray-500"}`}>
                    {!organizationName.trim()
                      ? "Обязательное поле — введите название организации"
                      : "Отображается на этикетке"}
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
                    10 или 12 цифр. Используйте переключатель выше для отображения на этикетке.
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
                    disabled={labelLayout === "professional" || labelLayout === "extended"}
                    className={`w-full px-4 py-2.5 rounded-xl border border-warm-gray-300 bg-white
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                      ${(labelLayout === "professional" || labelLayout === "extended") ? "opacity-60 cursor-not-allowed" : ""}`}
                  >
                    <option value="58x40">58×40 мм (стандартный)</option>
                    {labelLayout === "basic" && (
                      <>
                        <option value="58x30">58×30 мм (компактный)</option>
                        <option value="58x60">58×60 мм (увеличенный)</option>
                      </>
                    )}
                  </select>
                  {(labelLayout === "professional" || labelLayout === "extended") && (
                    <p className="text-xs text-warm-gray-500 mt-1">
                      {labelLayout === "professional" ? "Профессиональный" : "Расширенный"} шаблон доступен только в размере 58×40 мм
                    </p>
                  )}
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
                <LabelCanvas
                  data={previewData}
                  layout={labelLayout}
                  size={labelSize}
                  scale={0.6}
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
                  customLines={labelLayout === "extended" ? customLines : undefined}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Проверка данных ДО генерации (скрыто при генерации) */}
      {!isGenerating && uploadedFile && fileType === "excel" && selectedColumn && (
        <DataValidationCard
          layout={labelLayout}
          fileDetectionResult={fileDetectionResult}
          organizationName={organizationName}
          inn={inn}
          customLinesCount={customLines.length}
          onChangeLayout={setLabelLayout}
        />
      )}


      {/* Ножницы — выбор диапазона печати (скрыто при генерации) */}
      {!isGenerating && uploadedFile && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Scissors className="w-5 h-5 text-emerald-600" />
              Диапазон печати и нумерация
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Левая колонка: Диапазон печати */}
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Scissors className="w-4 h-4 text-emerald-600" />
                  <span className="text-sm font-medium text-warm-gray-700">Диапазон печати</span>
                </div>
                <p className="text-xs text-warm-gray-500">
                  Выберите, какие этикетки генерировать
                </p>

                {/* Переключатель режима */}
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="rangeMode"
                      checked={!useRange}
                      onChange={() => setUseRange(false)}
                      className="w-4 h-4 text-emerald-600 border-warm-gray-300 focus:ring-emerald-500"
                    />
                    <span className="text-warm-gray-700">Все этикетки</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="rangeMode"
                      checked={useRange}
                      onChange={() => setUseRange(true)}
                      className="w-4 h-4 text-emerald-600 border-warm-gray-300 focus:ring-emerald-500"
                    />
                    <span className="text-warm-gray-700">Выбрать диапазон</span>
                  </label>
                </div>

                {/* Инпуты диапазона (показываем только если выбран режим диапазона) */}
                {useRange && (
                  <div className="flex items-center gap-4 p-4 bg-warm-gray-50 rounded-lg">
                    <span className="text-warm-gray-600">Этикетки с</span>
                    <input
                      type="number"
                      min={1}
                      max={rangeEnd}
                      value={rangeStart}
                      onChange={(e) => setRangeStart(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-20 px-3 py-2 text-center border border-warm-gray-300 rounded-lg
                        focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    />
                    <span className="text-warm-gray-600">по</span>
                    <input
                      type="number"
                      min={rangeStart}
                      max={fileDetectionResult?.rows_count || 1}
                      value={rangeEnd}
                      onChange={(e) => setRangeEnd(Math.max(rangeStart, parseInt(e.target.value) || rangeStart))}
                      className="w-20 px-3 py-2 text-center border border-warm-gray-300 rounded-lg
                        focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    />
                    <span className="text-warm-gray-500 text-sm">
                      из {fileDetectionResult?.rows_count || 0}
                    </span>
                  </div>
                )}

                {/* Информация о результате */}
                {useRange && rangeStart <= rangeEnd && (
                  <p className="text-sm text-emerald-600 flex items-center gap-1">
                    <Check className="w-4 h-4" />
                    Будет создано {rangeEnd - rangeStart + 1} этикеток (№{rangeStart}–{rangeEnd})
                  </p>
                )}
              </div>

              {/* Правая колонка: Нумерация */}
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Hash className="w-4 h-4 text-emerald-600" />
                  <span className="text-sm font-medium text-warm-gray-700">Нумерация</span>
                </div>

                {(() => {
                  const isPro = user?.plan === "pro" || user?.plan === "enterprise";
                  const hasGlobalHistory = globalNextNumber > 1;
                  const hasPerProductHistory = perProductNextNumber > 1;

                  return (
                    <div className="space-y-3">
                      <select
                        value={numberingMode}
                        onChange={(e) => {
                          const newMode = e.target.value as NumberingMode;
                          // Блокируем выбор PRO-опций для FREE
                          if (!isPro && (newMode === "per_product")) {
                            return;
                          }
                          setNumberingMode(newMode);
                          // Автоподстановка стартового номера
                          if (newMode === "continue") {
                            setStartNumber(globalNextNumber);
                          } else if (newMode === "continue_per_product") {
                            setStartNumber(perProductNextNumber);
                          }
                        }}
                        className="w-full px-3 py-2 border border-warm-gray-300 rounded-lg
                          focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                          bg-white text-warm-gray-700"
                      >
                        <option value="none">Без нумерации</option>
                        <option value="sequential">Сквозная (1, 2, 3...)</option>
                        <option value="per_product" disabled={!isPro}>
                          По товару {!isPro ? "🔒 PRO" : ""}
                        </option>
                        {hasGlobalHistory && (
                          <option value="continue">
                            Продолжить с {globalNextNumber} (общая)
                          </option>
                        )}
                        {isPro && hasPerProductHistory && perProductNextNumber !== globalNextNumber && (
                          <option value="continue_per_product">
                            Продолжить с {perProductNextNumber} (по товару)
                          </option>
                        )}
                        {!isPro && hasPerProductHistory && (
                          <option value="continue_per_product_locked" disabled>
                            Продолжить (по товару) 🔒 PRO
                          </option>
                        )}
                      </select>

                      {/* Input для стартового номера (показывается только для "continue") */}
                      {(numberingMode === "continue" || numberingMode === "continue_per_product") && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 p-3 bg-warm-gray-50 rounded-lg">
                            <span className="text-sm text-warm-gray-600">Начать с:</span>
                            <input
                              type="number"
                              min={1}
                              value={startNumber}
                              onChange={(e) => setStartNumber(Math.max(1, parseInt(e.target.value) || 1))}
                              className="w-24 px-3 py-2 text-center border border-warm-gray-300 rounded-lg
                                focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                            />
                          </div>
                          <p className="text-xs text-emerald-600">
                            {numberingMode === "continue"
                              ? "Глобальный счётчик"
                              : "Из карточек товаров"}
                          </p>
                        </div>
                      )}

                      {/* Подсказка для режима "По товару" */}
                      {numberingMode === "per_product" && (
                        <p className="text-xs text-warm-gray-500">
                          Нумерация сбрасывается для каждого баркода
                        </p>
                      )}
                    </div>
                  );
                })()}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* GTIN Matching Block — удалён отсюда, показывается рядом с загрузкой PDF */}

      {/* Text Overflow Warning */}
      {showTruncationWarning && textTruncations.length > 0 && (
        <TextOverflowWarning
          truncations={textTruncations}
          onContinue={() => {
            setShowTruncationWarning(false);
            // Продолжить генерацию
            handleGenerate();
          }}
          onDismiss={() => setShowTruncationWarning(false)}
          suggestedTemplate={
            labelSize === "58x30" ? "58x40" :
            labelSize === "58x40" ? "58x60" : undefined
          }
        />
      )}

      {/* Загрузка PDF с кодами маркировки (скрыто при генерации) */}
      {!isGenerating && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Коды маркировки Честного Знака</CardTitle>
                <p className="text-sm text-warm-gray-500 mt-1">
                  PDF из личного кабинета ЧЗ (crpt.ru)
                </p>
              </div>
              <span
                className={`text-sm font-medium px-3 py-1 rounded-lg ${
                  codesFile
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-warm-gray-100 text-warm-gray-600"
                }`}
              >
                {codesFile ? "PDF загружен" : "Не загружен"}
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Зона загрузки файла с кодами ЧЗ (PDF, CSV, Excel) */}
              <input
                ref={codesInputRef}
                type="file"
                accept=".pdf,.csv,.xlsx,.xls"
                onChange={handleCodesFileChange}
                className="hidden"
              />

              {!codesFile ? (
                <button
                  onClick={() => codesInputRef.current?.click()}
                  className="w-full border-2 border-dashed border-warm-gray-300 rounded-xl p-8
                    hover:border-emerald-400 hover:bg-emerald-50/50 transition-all duration-200
                    focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                      <FileText className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div className="text-center">
                      <p className="font-medium text-warm-gray-900">
                        Загрузите файл с кодами маркировки
                      </p>
                      <p className="text-sm text-warm-gray-500 mt-1">
                        PDF, CSV или Excel из Честного Знака (crpt.ru)
                      </p>
                    </div>
                  </div>
                </button>
              ) : (
                <div className="flex items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                      <p className="font-medium text-emerald-900">{codesFile.name}</p>
                      <p className="text-sm text-emerald-600">
                        {(codesFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={removeCodesFile}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              )}

              {/* Подсказка */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-sm text-amber-800">
                  <strong>Рекомендуем PDF</strong> — он содержит полные коды с криптохвостом.
                  CSV/Excel из ЧЗ часто без криптоподписи — такие коды не сканируются.
                </p>
              </div>

              {/* Блок матчинга GTIN (показывается после загрузки обоих файлов) */}
              {isPreflightLoading && (
                <div className="flex items-center gap-2 p-4 bg-warm-gray-50 rounded-lg">
                  <div className="w-4 h-4 border-2 border-warm-gray-300 border-t-warm-gray-600 rounded-full animate-spin" />
                  <span className="text-sm text-warm-gray-600">Проверка совместимости файлов...</span>
                </div>
              )}

              {gtinPreflightResponse && !isPreflightLoading && (
                <div className="space-y-2">
                  {/* Ошибка preflight — коды без криптохвоста */}
                  {gtinPreflightResponse.status === "error" ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="font-medium text-red-800">
                            Невозможно создать этикетки
                          </p>
                          <p className="text-sm text-red-700 mt-1">
                            {gtinPreflightResponse.message}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <>
                      <GtinMatchingBlock
                        status={gtinPreflightResponse.status}
                        gtins={gtinPreflightResponse.gtins}
                        excelItems={gtinPreflightResponse.excel_items}
                        mapping={gtinMapping}
                        onMappingChange={handleGtinMappingChange}
                        totalCodes={gtinPreflightResponse.total_codes}
                      />
                      {/* Подсказка для СНГ-селлеров */}
                      {gtinPreflightResponse.status === "manual_required" && (
                        <p className="text-xs text-warm-gray-500 px-1">
                          💡 Ручной матчинг нужен когда баркоды WB (20...) отличаются от GTIN в кодах ЧЗ (046, 047...).
                          Это часто бывает у селлеров из СНГ с несколькими товарами.
                        </p>
                      )}
                    </>
                  )}
                </div>
              )}
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
            onClick={() => handleGenerate()}
            disabled={
              !codesFile ||
              !uploadedFile ||
              (fileType === "excel" && !selectedColumn) ||
              !organizationName.trim() ||
              isPreflightLoading ||
              gtinPreflightResponse?.status === "error"
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
