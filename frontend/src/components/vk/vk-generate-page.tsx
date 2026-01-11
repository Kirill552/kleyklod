"use client";

/**
 * Страница генерации этикеток для VK Mini App.
 *
 * Упрощённая версия основной страницы генерации:
 * - Только Basic шаблон (58x40)
 * - Настройки: организация, ИНН, диапазон, нумерация
 * - Скачивание через VK Bridge
 * - Ссылка на сайт для расширенных настроек
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getUserStats,
  generateFromExcel,
  getUserPreferences,
  type LabelLayout,
  type LabelSize,
  type FileDetectionResult,
  type NumberingMode,
} from "@/lib/api";
import type { UserStats, User } from "@/types/api";
import { LabelCanvas } from "@/components/app/generate/label-canvas";
import { UnifiedDropzone } from "@/components/app/generate/unified-dropzone";
import { useToast } from "@/components/ui/toast";
import { downloadFile } from "@/lib/vk-bridge";
import { useVKAuth } from "@/contexts/vk-auth-context";
import {
  Loader2,
  Download,
  FileSpreadsheet,
  FileText,
  X,
  Building2,
  Scissors,
  Hash,
  ExternalLink,
  Check,
} from "lucide-react";
import { SubscriptionBanner } from "./subscription-banner";

interface VKGeneratePageProps {
  user: User | null;
}

/** Дневные лимиты по планам */
const dailyLimits: Record<string, number> = {
  free: 50,
  pro: 500,
  enterprise: 10000,
};

export default function VKGeneratePage({ user }: VKGeneratePageProps) {
  const { showToast } = useToast();
  const { insets, vkUser } = useVKAuth();

  // Состояние
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  // Файлы
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [codesFile, setCodesFile] = useState<File | null>(null);
  const [excelData, setExcelData] = useState<FileDetectionResult | null>(null);

  // Настройки этикетки (только basic, 58x40)
  const layout: LabelLayout = "basic";
  const labelSize: LabelSize = "58x40";

  // Организация и ИНН
  const [organizationName, setOrganizationName] = useState("");
  const [inn, setInn] = useState("");
  const [showInn, setShowInn] = useState(true);

  // Диапазон печати
  const [useRange, setUseRange] = useState(false);
  const [rangeStart, setRangeStart] = useState<number>(1);
  const [rangeEnd, setRangeEnd] = useState<number>(1);

  // Нумерация
  const [numberingMode, setNumberingMode] = useState<NumberingMode>("none");
  const [startNumber, setStartNumber] = useState<number>(1);

  // Refs
  const codesInputRef = useRef<HTMLInputElement>(null);

  // Загрузка статистики и настроек
  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, prefs] = await Promise.all([
          getUserStats(),
          getUserPreferences(),
        ]);
        setStats(statsData);

        // Применяем сохранённые настройки организации
        if (prefs.organization_name) {
          setOrganizationName(prefs.organization_name);
        }
        if (prefs.inn) {
          setInn(prefs.inn);
        }
      } catch (error) {
        console.error("Ошибка загрузки данных:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Автообновление rangeEnd при изменении количества строк
  useEffect(() => {
    const totalCount = excelData?.rows_count || 0;
    if (totalCount > 0) {
      setRangeEnd(totalCount);
    }
  }, [excelData?.rows_count]);

  // Обработка автодетекта Excel файла
  const handleFileDetected = useCallback(
    (result: FileDetectionResult, file: File) => {
      setExcelFile(file);
      setExcelData(result);
      setDownloadUrl(null);
    },
    []
  );

  // Обработка загрузки кодов PDF
  const handleCodesFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        setCodesFile(file);
        setDownloadUrl(null);
      }
    },
    []
  );

  // Удаление PDF файла
  const removeCodesFile = useCallback(() => {
    setCodesFile(null);
    if (codesInputRef.current) {
      codesInputRef.current.value = "";
    }
  }, []);

  // Сброс файлов
  const handleReset = useCallback(() => {
    setExcelFile(null);
    setCodesFile(null);
    setExcelData(null);
    setDownloadUrl(null);
  }, []);

  // Генерация
  const handleGenerate = useCallback(async () => {
    if (!excelFile) {
      showToast({
        message: "Ошибка",
        description: "Загрузите Excel файл с товарами",
        type: "error",
      });
      return;
    }

    if (!codesFile) {
      showToast({
        message: "Ошибка",
        description: "Загрузите PDF файл с кодами маркировки",
        type: "error",
      });
      return;
    }

    if (!organizationName.trim()) {
      showToast({
        message: "Ошибка",
        description: "Введите название организации",
        type: "error",
      });
      return;
    }

    try {
      setGenerating(true);
      setDownloadUrl(null);

      const result = await generateFromExcel({
        excelFile,
        codesFile,
        layout,
        labelSize,
        labelFormat: "combined",
        // Организация
        organizationName: organizationName || undefined,
        inn: inn || undefined,
        showInn: showInn && !!inn.trim(),
        // Флаги отображения
        showArticle: true,
        showSize: true,
        showColor: true,
        showName: true,
        showOrganization: true,
        // Диапазон
        rangeStart: useRange ? rangeStart : undefined,
        rangeEnd: useRange ? rangeEnd : undefined,
        // Нумерация
        numberingMode: numberingMode,
        startNumber: numberingMode === "continue" ? startNumber : undefined,
      });

      if (result.success && result.download_url) {
        setDownloadUrl(result.download_url);
        showToast({
          message: "Готово!",
          description: `Сгенерировано ${result.labels_count} этикеток`,
          type: "success",
        });

        // Обновляем статистику
        const newStats = await getUserStats();
        setStats(newStats);
      } else {
        showToast({
          message: "Ошибка",
          description: result.message || "Не удалось сгенерировать этикетки",
          type: "error",
        });
      }
    } catch (error) {
      console.error("Ошибка генерации:", error);
      showToast({
        message: "Ошибка",
        description:
          error instanceof Error ? error.message : "Ошибка генерации",
        type: "error",
      });
    } finally {
      setGenerating(false);
    }
  }, [
    excelFile,
    codesFile,
    layout,
    labelSize,
    organizationName,
    inn,
    showInn,
    useRange,
    rangeStart,
    rangeEnd,
    numberingMode,
    startNumber,
    showToast,
  ]);

  // Скачивание через VK Bridge
  const handleDownload = useCallback(async () => {
    if (!downloadUrl) return;

    try {
      const fullUrl = downloadUrl.startsWith("http")
        ? downloadUrl
        : `${window.location.origin}${downloadUrl}`;

      await downloadFile(fullUrl, "labels.pdf");

      showToast({
        message: "Скачивание",
        description: "Файл скачивается...",
        type: "info",
      });
    } catch (error) {
      console.error("Ошибка скачивания:", error);
      window.open(downloadUrl, "_blank");
    }
  }, [downloadUrl, showToast]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const plan = user?.plan || "free";
  const dailyLimit = dailyLimits[plan] || 50;
  const usedToday = stats?.today_used || 0;
  const remaining = Math.max(0, dailyLimit - usedToday);
  const totalRows = excelData?.rows_count || 0;

  // Высота нижней панели с учётом insets
  const bottomBarHeight = 64 + insets.bottom;

  return (
    <div
      className="container mx-auto p-4"
      style={{ paddingBottom: bottomBarHeight + 16 }}
    >
      {/* Заголовок */}
      <h1 className="text-2xl font-bold mb-4">KleyKod</h1>

      {/* Баннер подписки */}
      <SubscriptionBanner
        user={user}
        stats={stats}
        vkUserId={vkUser?.id ?? null}
      />

      {/* Ссылка на сайт */}
      <a
        href="https://kleykod.ru/app/generate"
        target="_blank"
        rel="noopener noreferrer"
        className="w-full mb-6 p-3 bg-blue-50 border border-blue-200 rounded-xl
          flex items-center justify-center gap-2 text-blue-700 hover:bg-blue-100 transition-colors"
      >
        <ExternalLink className="w-4 h-4" />
        <span className="text-sm font-medium">
          Больше настроек на сайте kleykod.ru
        </span>
      </a>

      {/* Загрузка Excel */}
      {!excelFile && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-emerald-600" />
              Excel с баркодами
            </CardTitle>
          </CardHeader>
          <CardContent>
            <UnifiedDropzone onFileDetected={handleFileDetected} />
          </CardContent>
        </Card>
      )}

      {/* Показ загруженного Excel */}
      {excelFile && (
        <Card className="mb-6 border-emerald-200 bg-emerald-50/50">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="w-5 h-5 text-emerald-600" />
                <div>
                  <span className="font-medium">{excelFile.name}</span>
                  <p className="text-sm text-emerald-600">
                    {totalRows} товаров
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={handleReset}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Загрузка PDF с кодами */}
      {excelFile && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" />
              PDF с кодами маркировки
            </CardTitle>
          </CardHeader>
          <CardContent>
            <input
              type="file"
              ref={codesInputRef}
              accept=".pdf"
              onChange={handleCodesFileChange}
              className="hidden"
            />
            {!codesFile ? (
              <button
                onClick={() => codesInputRef.current?.click()}
                className="w-full border-2 border-dashed border-warm-gray-300 rounded-xl p-6
                  hover:border-emerald-400 hover:bg-emerald-50/50 transition-all"
              >
                <div className="text-center">
                  <p className="font-medium text-warm-gray-900">
                    Загрузите PDF с кодами
                  </p>
                  <p className="text-sm text-warm-gray-500 mt-1">
                    Скачайте из личного кабинета Честного Знака
                  </p>
                </div>
              </button>
            ) : (
              <div className="flex items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-emerald-600" />
                  <span className="font-medium text-emerald-900">
                    {codesFile.name}
                  </span>
                </div>
                <Button variant="ghost" size="sm" onClick={removeCodesFile}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Настройки организации */}
      {excelFile && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-600" />
              Организация
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Название организации */}
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
            </div>

            {/* ИНН */}
            <div>
              <label className="block text-sm font-medium text-warm-gray-700 mb-1">
                ИНН
                <span className="text-warm-gray-400 font-normal ml-1">
                  (опционально)
                </span>
              </label>
              <input
                type="text"
                value={inn}
                onChange={(e) =>
                  setInn(e.target.value.replace(/\D/g, "").slice(0, 12))
                }
                placeholder="123456789012"
                maxLength={12}
                className="w-full px-4 py-2.5 rounded-xl border border-warm-gray-300 bg-white
                  focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>

            {/* Toggle показа ИНН */}
            {inn.trim() && (
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showInn}
                  onChange={(e) => setShowInn(e.target.checked)}
                  className="w-4 h-4 rounded border-warm-gray-300 text-emerald-600 focus:ring-emerald-500"
                />
                <span className="text-sm text-warm-gray-700">
                  Показывать ИНН на этикетке
                </span>
              </label>
            )}
          </CardContent>
        </Card>
      )}

      {/* Диапазон печати и нумерация */}
      {excelFile && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Scissors className="w-5 h-5 text-emerald-600" />
              Диапазон и нумерация
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Диапазон печати */}
            <div className="space-y-3">
              <p className="text-sm font-medium text-warm-gray-700">
                Диапазон печати
              </p>

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

              {useRange && (
                <div className="flex items-center gap-3 p-3 bg-warm-gray-50 rounded-lg">
                  <span className="text-warm-gray-600 text-sm">с</span>
                  <input
                    type="number"
                    min={1}
                    max={rangeEnd}
                    value={rangeStart}
                    onChange={(e) =>
                      setRangeStart(Math.max(1, parseInt(e.target.value) || 1))
                    }
                    className="w-16 px-2 py-1.5 text-center border border-warm-gray-300 rounded-lg
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                  <span className="text-warm-gray-600 text-sm">по</span>
                  <input
                    type="number"
                    min={rangeStart}
                    max={totalRows}
                    value={rangeEnd}
                    onChange={(e) =>
                      setRangeEnd(
                        Math.max(rangeStart, parseInt(e.target.value) || rangeStart)
                      )
                    }
                    className="w-16 px-2 py-1.5 text-center border border-warm-gray-300 rounded-lg
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                  <span className="text-warm-gray-500 text-sm">из {totalRows}</span>
                </div>
              )}

              {useRange && rangeStart <= rangeEnd && (
                <p className="text-sm text-emerald-600 flex items-center gap-1">
                  <Check className="w-4 h-4" />
                  Будет создано {rangeEnd - rangeStart + 1} этикеток
                </p>
              )}
            </div>

            {/* Разделитель */}
            <hr className="border-warm-gray-200" />

            {/* Нумерация */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-emerald-600" />
                <span className="text-sm font-medium text-warm-gray-700">
                  Нумерация
                </span>
              </div>

              <select
                value={numberingMode}
                onChange={(e) => setNumberingMode(e.target.value as NumberingMode)}
                className="w-full px-3 py-2.5 border border-warm-gray-300 rounded-xl
                  focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                  bg-white text-warm-gray-700"
              >
                <option value="none">Без нумерации</option>
                <option value="sequential">Сквозная (1, 2, 3...)</option>
                <option value="per_product">По товару</option>
                <option value="continue">Продолжить с №...</option>
              </select>

              {numberingMode === "continue" && (
                <div className="flex items-center gap-2 p-3 bg-warm-gray-50 rounded-lg">
                  <span className="text-sm text-warm-gray-600">Начать с:</span>
                  <input
                    type="number"
                    min={1}
                    value={startNumber}
                    onChange={(e) =>
                      setStartNumber(Math.max(1, parseInt(e.target.value) || 1))
                    }
                    className="w-20 px-2 py-1.5 text-center border border-warm-gray-300 rounded-lg
                      focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
              )}

              {numberingMode === "per_product" && (
                <p className="text-xs text-warm-gray-500">
                  Нумерация сбрасывается для каждого баркода
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Превью этикетки */}
      {excelData && excelData.sample_items && excelData.sample_items.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Превью</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-center">
              <LabelCanvas
                layout={layout}
                size={labelSize}
                scale={0.5}
                data={{
                  barcode: excelData.sample_items[0].barcode,
                  article: excelData.sample_items[0].article ?? undefined,
                  size: excelData.sample_items[0].size ?? undefined,
                  color: excelData.sample_items[0].color ?? undefined,
                  name: excelData.sample_items[0].name ?? undefined,
                  organization: organizationName || "ИП Иванов И.И.",
                  inn: showInn && inn ? inn : undefined,
                  country: excelData.sample_items[0].country ?? undefined,
                  composition: excelData.sample_items[0].composition ?? undefined,
                }}
                showOrganization={true}
                showInn={showInn && !!inn.trim()}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Кнопки действий — fixed панель */}
      <div
        className="fixed bottom-0 left-0 right-0 bg-background border-t"
        style={{ paddingBottom: insets.bottom }}
      >
        <div className="container mx-auto flex gap-4 p-4">
          {downloadUrl ? (
            <Button onClick={handleDownload} className="flex-1" size="lg">
              <Download className="mr-2 h-5 w-5" />
              Скачать PDF
            </Button>
          ) : (
            <Button
              onClick={handleGenerate}
              disabled={
                !excelFile ||
                !codesFile ||
                generating ||
                remaining === 0 ||
                !organizationName.trim()
              }
              className="flex-1"
              size="lg"
            >
              {generating ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Генерация...
                </>
              ) : (
                <>
                  <FileSpreadsheet className="mr-2 h-5 w-5" />
                  Создать этикетки
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
