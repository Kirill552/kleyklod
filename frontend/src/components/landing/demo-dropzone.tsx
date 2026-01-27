"use client";

/**
 * Реальная демо-зона для лендинга — генерация БЕЗ регистрации.
 *
 * Флоу:
 * 1. Загрузка Excel с баркодами из ЛК Wildberries
 * 2. Загрузка PDF с кодами ЧЗ
 * 3. Вызов /api/demo/generate-full
 * 4. Показ результата с preflight + скачивание (с водяным знаком)
 * 5. CTA: "Войдите для полного доступа"
 */

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Download,
  Loader2,
  ArrowRight,
  X,
  RefreshCw,
  Shield,
} from "lucide-react";

interface DemoDropzoneProps {
  onLoginClick: () => void;
}

type DemoStep = "idle" | "excel_uploaded" | "processing" | "complete" | "error";

interface PreflightCheck {
  code: string;
  status: "ok" | "warning" | "error";
  message: string;
  recommendation?: string;
}

interface DemoResult {
  success: boolean;
  message: string;
  file_id?: string;
  preflight?: {
    passed: boolean;
    checks: PreflightCheck[];
  };
}

export function DemoDropzone({ onLoginClick }: DemoDropzoneProps) {
  // Шаг demo процесса
  const [step, setStep] = useState<DemoStep>("idle");

  // Загруженные файлы
  const [excelFile, setExcelFile] = useState<File | null>(null);

  // Результат генерации
  const [result, setResult] = useState<DemoResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");

  // Обработка загрузки Excel с баркодами WB
  const onExcelDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setExcelFile(acceptedFiles[0]);
      setStep("excel_uploaded");
      setErrorMessage("");
    }
  }, []);

  // Обработка загрузки кодов и запуск генерации
  const onCodesDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0 || !excelFile) return;

      const codes = acceptedFiles[0];
      setStep("processing");
      setErrorMessage("");

      try {
        const formData = new FormData();
        formData.append("barcodes_excel", excelFile);
        formData.append("codes_file", codes);
        formData.append("template", "58x40");

        const response = await fetch("/api/demo/generate-full", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();

        if (response.ok && data.success) {
          setResult(data);
          setStep("complete");
        } else {
          setErrorMessage(data.message || data.detail?.message || "Ошибка генерации");
          setStep("error");
        }
      } catch (error) {
        console.error("Demo error:", error);
        setErrorMessage("Ошибка соединения с сервером");
        setStep("error");
      }
    },
    [excelFile]
  );

  // Сброс состояния
  const resetDemo = useCallback(() => {
    setExcelFile(null);
    setResult(null);
    setErrorMessage("");
    setStep("idle");
  }, []);

  // Скачивание результата
  const handleDownload = useCallback(async () => {
    if (!result?.file_id) return;

    try {
      const response = await fetch(`/api/v1/demo/download/${result.file_id}`);
      if (!response.ok) throw new Error("Download failed");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `demo-labels-${Date.now()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download error:", error);
    }
  }, [result]);

  // Dropzone для Excel с баркодами WB
  const excelDropzone = useDropzone({
    onDrop: onExcelDrop,
    accept: {
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxFiles: 1,
    maxSize: 2 * 1024 * 1024, // 2MB для demo
    disabled: step !== "idle",
  });

  // Dropzone для кодов ЧЗ (только PDF)
  const codesDropzone = useDropzone({
    onDrop: onCodesDrop,
    accept: {
      "application/pdf": [".pdf"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB для PDF
    disabled: step !== "excel_uploaded",
  });

  // Рендер в зависимости от шага
  const renderContent = () => {
    switch (step) {
      case "idle":
        return (
          <div
            {...excelDropzone.getRootProps()}
            className={`
              relative p-8 rounded-xl border-2 border-dashed cursor-pointer
              transition-all duration-300 min-h-[280px]
              flex flex-col items-center justify-center
              ${excelDropzone.isDragActive
                ? "border-emerald-400 bg-emerald-50"
                : "border-warm-gray-300 bg-warm-gray-50 hover:border-emerald-400 hover:bg-emerald-50/30"
              }
            `}
          >
            <input {...excelDropzone.getInputProps()} aria-label="Загрузите Excel файл с баркодами Wildberries" />

            <FileSpreadsheet className="w-16 h-16 text-emerald-500 mb-4" />
            <p className="text-lg font-medium text-warm-gray-700 mb-2 text-center">
              Загрузите Excel с баркодами из ЛК WB
            </p>
            <p className="text-sm text-warm-gray-500 mb-4 text-center">
              Перетащите файл или нажмите для выбора
            </p>
            <a
              href="/examples/vk-barcodes-example.xlsx"
              download
              onClick={(e) => e.stopPropagation()}
              className="text-sm text-emerald-600 hover:text-emerald-700 underline"
            >
              Скачать пример файла
            </a>

            {/* Drag overlay */}
            <AnimatePresence>
              {excelDropzone.isDragActive && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-emerald-100/90 rounded-xl flex items-center justify-center"
                >
                  <div className="text-center">
                    <FileSpreadsheet className="w-12 h-12 text-emerald-500 mx-auto mb-2" />
                    <p className="text-emerald-700 font-medium">Отпустите Excel файл</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );

      case "excel_uploaded":
        return (
          <div
            {...codesDropzone.getRootProps()}
            className={`
              relative p-8 rounded-xl border-2 border-dashed cursor-pointer
              transition-all duration-300 min-h-[320px]
              ${codesDropzone.isDragActive
                ? "border-amber-400 bg-amber-50"
                : "border-emerald-400 bg-emerald-50/50 hover:bg-emerald-50"
              }
            `}
          >
            <input {...codesDropzone.getInputProps()} aria-label="Загрузите PDF или CSV с кодами маркировки Честный Знак" />

            <div className="flex flex-col items-center justify-center h-full">
              {/* Excel загружен */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 mb-6 px-4 py-2 bg-emerald-100 rounded-full"
              >
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span className="text-emerald-700 font-medium">{excelFile?.name}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    resetDemo();
                  }}
                  className="ml-2 p-1 hover:bg-emerald-200 rounded-full"
                  aria-label="Удалить загруженный файл"
                >
                  <X className="w-4 h-4 text-emerald-600" />
                </button>
              </motion.div>

              {/* Dropzone для кодов */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-center"
              >
                <FileText className="w-16 h-16 text-amber-500 mx-auto mb-4" />
                <p className="text-lg font-medium text-warm-gray-700 mb-2">
                  Теперь загрузите коды Честного Знака
                </p>
                <p className="text-sm text-warm-gray-500">
                  PDF из личного кабинета ЧЗ (markirovka.crpt.ru)
                </p>
              </motion.div>
            </div>

            {/* Drag overlay */}
            <AnimatePresence>
              {codesDropzone.isDragActive && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-amber-100/90 rounded-xl flex items-center justify-center"
                >
                  <div className="text-center">
                    <Upload className="w-12 h-12 text-amber-500 mx-auto mb-2" />
                    <p className="text-amber-700 font-medium">Отпустите файл с кодами</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );

      case "processing":
        return (
          <div className="relative p-8 rounded-xl border-2 border-emerald-400 bg-emerald-50/50 min-h-[320px] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center"
            >
              <Loader2 className="w-16 h-16 text-emerald-500 mx-auto mb-4 animate-spin" />
              <p className="text-lg font-medium text-warm-gray-700 mb-2">
                Генерируем этикетки...
              </p>
              <p className="text-sm text-warm-gray-500">
                Проверка качества DataMatrix включена
              </p>
            </motion.div>
          </div>
        );

      case "complete":
        return (
          <div className="relative p-6 rounded-xl border-2 border-emerald-400 bg-emerald-50/50 min-h-[320px]">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="h-full flex flex-col"
            >
              {/* Заголовок */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                  <span className="font-semibold text-warm-gray-800">
                    Этикетки готовы!
                  </span>
                </div>
                <button
                  onClick={resetDemo}
                  className="p-2 hover:bg-warm-gray-100 rounded-full"
                  title="Начать заново"
                >
                  <RefreshCw className="w-4 h-4 text-warm-gray-500" />
                </button>
              </div>

              {/* Preflight результаты */}
              {result?.preflight?.checks && result.preflight.checks.length > 0 && (
                <div className="mb-4 space-y-2">
                  <p className="text-sm font-medium text-warm-gray-600 mb-2">
                    <Shield className="w-4 h-4 inline mr-1" />
                    Проверка качества:
                  </p>
                  {result.preflight.checks.slice(0, 3).map((check, i) => (
                    <div
                      key={i}
                      className={`flex items-start gap-2 text-sm px-3 py-2 rounded-lg ${
                        check.status === "ok"
                          ? "bg-emerald-100 text-emerald-700"
                          : check.status === "warning"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-red-100 text-red-700"
                      }`}
                    >
                      {check.status === "ok" ? (
                        <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      )}
                      <span>{check.message}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Кнопки */}
              <div className="mt-auto space-y-3">
                <button
                  onClick={handleDownload}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-warm-gray-100 hover:bg-warm-gray-200 text-warm-gray-700 rounded-xl transition-colors"
                >
                  <Download className="w-5 h-5" />
                  Скачать демо-версию
                  <span className="text-xs text-warm-gray-500">(с водяным знаком)</span>
                </button>

                <button
                  onClick={onLoginClick}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition-colors"
                >
                  Войти для полного доступа
                  <ArrowRight className="w-5 h-5" />
                </button>

                <p className="text-center text-xs text-warm-gray-500">
                  7 дней бесплатно, тариф Про с накоплением до 10 000 этикеток
                </p>
              </div>
            </motion.div>
          </div>
        );

      case "error":
        return (
          <div className="relative p-8 rounded-xl border-2 border-red-300 bg-red-50/50 min-h-[320px] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center"
            >
              <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <p className="text-lg font-medium text-red-700 mb-2">Ошибка</p>
              <p className="text-sm text-red-600 mb-6 max-w-xs">{errorMessage}</p>
              <button
                onClick={resetDemo}
                className="px-6 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
              >
                Попробовать снова
              </button>
            </motion.div>
          </div>
        );
    }
  };

  return (
    <div className="relative">
      {renderContent()}

      {/* Статус */}
      <div className="mt-4 flex items-center justify-center gap-2 text-sm text-warm-gray-500">
        <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
        {step === "idle"
          ? "Попробуйте бесплатно — без регистрации"
          : step === "excel_uploaded"
            ? "Осталось загрузить коды ЧЗ"
            : step === "processing"
              ? "Генерация с проверкой качества..."
              : step === "complete"
                ? "Demo: до 5 этикеток, 3 раза в час"
                : "Попробуйте снова"
        }
      </div>
    </div>
  );
}
