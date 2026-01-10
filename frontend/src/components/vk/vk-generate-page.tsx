"use client";

/**
 * Страница генерации этикеток для VK Mini App.
 *
 * Упрощённая версия основной страницы генерации:
 * - Без навигации (мы внутри Mini App)
 * - Скачивание через VK Bridge
 * - Оплата через редирект на сайт
 * - Адаптация под мобильный VK (Safe Area Insets)
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
} from "@/lib/api";
import type { UserStats, User, LabelFormat } from "@/types/api";
import { LayoutSelector } from "@/components/app/generate/layout-selector";
import { LabelCanvas } from "@/components/app/generate/label-canvas";
import { UnifiedDropzone } from "@/components/app/generate/unified-dropzone";
import { useToast } from "@/components/ui/toast";
import { downloadFile } from "@/lib/vk-bridge";
import { useVKAuth } from "@/contexts/vk-auth-context";
import { Loader2, Download, FileSpreadsheet, FileText, X } from "lucide-react";
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

  // Настройки этикетки
  const [layout, setLayout] = useState<LabelLayout>("basic");
  const [labelSize, setLabelSize] = useState<LabelSize>("58x40");
  const [labelFormat, setLabelFormat] = useState<LabelFormat>("combined");

  // Refs
  const codesInputRef = useRef<HTMLInputElement>(null);

  // Загрузка статистики
  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, prefs] = await Promise.all([
          getUserStats(),
          getUserPreferences(),
        ]);
        setStats(statsData);

        // Применяем сохранённые настройки
        if (prefs.preferred_layout) {
          setLayout(prefs.preferred_layout);
        }
        if (prefs.preferred_label_size) {
          setLabelSize(prefs.preferred_label_size);
        }
        if (prefs.preferred_format) {
          setLabelFormat(prefs.preferred_format);
        }
      } catch (error) {
        console.error("Ошибка загрузки данных:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

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

    try {
      setGenerating(true);
      setDownloadUrl(null);

      const result = await generateFromExcel({
        excelFile,
        codesFile,
        layout,
        labelSize,
        labelFormat,
        showArticle: true,
        showSize: true,
        showColor: true,
        showName: true,
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
  }, [excelFile, codesFile, layout, labelSize, labelFormat, showToast]);

  // Скачивание через VK Bridge
  const handleDownload = useCallback(async () => {
    if (!downloadUrl) return;

    try {
      // Формируем полный URL
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
      // Fallback: открываем ссылку
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

  // Высота нижней панели с учётом insets (16px padding + 48px button + inset)
  const bottomBarHeight = 64 + insets.bottom;

  return (
    <div
      className="container mx-auto p-4"
      style={{ paddingBottom: bottomBarHeight + 16 }}
    >
      {/* Заголовок */}
      <h1 className="text-2xl font-bold mb-4">KleyKod</h1>

      {/* Баннер подписки с использованием и апгрейдом */}
      <SubscriptionBanner
        user={user}
        stats={stats}
        vkUserId={vkUser?.id ?? null}
      />

      {/* Выбор шаблона */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Шаблон этикетки</CardTitle>
        </CardHeader>
        <CardContent>
          <LayoutSelector
            value={layout}
            onChange={setLayout}
            size={labelSize}
          />
        </CardContent>
      </Card>

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
                <span className="font-medium">{excelFile.name}</span>
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
                  <span className="font-medium text-emerald-900">{codesFile.name}</span>
                </div>
                <Button variant="ghost" size="sm" onClick={removeCodesFile}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            )}
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
            <LabelCanvas
              layout={layout}
              size={labelSize}
              data={{
                barcode: excelData.sample_items[0].barcode,
                article: excelData.sample_items[0].article ?? undefined,
                size: excelData.sample_items[0].size ?? undefined,
                color: excelData.sample_items[0].color ?? undefined,
                name: excelData.sample_items[0].name ?? undefined,
                country: excelData.sample_items[0].country ?? undefined,
                composition: excelData.sample_items[0].composition ?? undefined,
                brand: excelData.sample_items[0].brand ?? undefined,
                manufacturer: excelData.sample_items[0].manufacturer ?? undefined,
                productionDate: excelData.sample_items[0].production_date ?? undefined,
                importer: excelData.sample_items[0].importer ?? undefined,
                certificate: excelData.sample_items[0].certificate_number ?? undefined,
                address: excelData.sample_items[0].address ?? undefined,
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Кнопки действий — fixed панель с учётом safe area */}
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
              disabled={!excelFile || !codesFile || generating || remaining === 0}
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
