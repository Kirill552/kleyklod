"use client";

/**
 * Компонент анимации демо-процесса.
 *
 * Показывает 5 фаз обработки этикеток:
 * 1. Загрузка PDF
 * 2. Парсинг страниц
 * 3. Генерация DataMatrix
 * 4. Pre-flight проверка
 * 5. Готовый результат
 */

import { motion, AnimatePresence } from "framer-motion";
import { FileText, Scan, QrCode, CheckCircle, Download } from "lucide-react";
import { DEMO_DATA, ANIMATION_PHASES } from "./demo-assets";

export type DemoPhase =
  | "idle"
  | "uploading"
  | "parsing"
  | "generating"
  | "preflight"
  | "complete";

interface DemoAnimationProps {
  phase: DemoPhase;
}

export function DemoAnimation({ phase }: DemoAnimationProps) {
  return (
    <div className="relative w-full h-full min-h-[280px] flex items-center justify-center">
      <AnimatePresence mode="wait">
        {phase === "idle" && <IdleState key="idle" />}
        {phase === "uploading" && <UploadingState key="uploading" />}
        {phase === "parsing" && <ParsingState key="parsing" />}
        {phase === "generating" && <GeneratingState key="generating" />}
        {phase === "preflight" && <PreflightState key="preflight" />}
        {phase === "complete" && <CompleteState key="complete" />}
      </AnimatePresence>
    </div>
  );
}

// Статическое состояние (ожидание)
function IdleState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="text-center"
    >
      <motion.div
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
        className="w-20 h-20 mx-auto mb-4 bg-emerald-100 rounded-2xl flex items-center justify-center"
      >
        <FileText className="w-10 h-10 text-emerald-600" />
      </motion.div>
      <p className="text-warm-gray-700 font-medium mb-2">
        Перетащите PDF от Wildberries
      </p>
      <p className="text-sm text-warm-gray-400">
        или наведите для демо
      </p>
    </motion.div>
  );
}

// Фаза 1: Загрузка PDF
function UploadingState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="text-center"
    >
      {/* Анимация падающего PDF */}
      <motion.div
        initial={{ y: -100, opacity: 0, scale: 0.8 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-20 h-20 mx-auto mb-4 bg-red-100 rounded-2xl flex items-center justify-center"
      >
        <FileText className="w-10 h-10 text-red-500" />
      </motion.div>

      {/* Progress bar */}
      <div className="w-48 h-2 mx-auto bg-warm-gray-200 rounded-full overflow-hidden mb-4">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: "100%" }}
          transition={{ duration: 1.2 }}
          className="h-full bg-emerald-500 rounded-full"
        />
      </div>

      <p className="text-warm-gray-600 font-medium">Загрузка PDF...</p>
      <p className="text-sm text-warm-gray-400 mt-1">wb_labels.pdf</p>
    </motion.div>
  );
}

// Фаза 2: Парсинг страниц
function ParsingState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="text-center"
    >
      {/* Веер страниц */}
      <div className="relative w-32 h-24 mx-auto mb-4">
        {[0, 1, 2, 3, 4].map((i) => (
          <motion.div
            key={i}
            initial={{ rotate: 0, x: 0 }}
            animate={{ rotate: (i - 2) * 8, x: (i - 2) * 12 }}
            transition={{ delay: i * 0.1, duration: 0.3 }}
            className="absolute top-0 left-1/2 -translate-x-1/2 w-16 h-20 bg-white border-2 border-warm-gray-200 rounded-lg shadow-sm flex items-center justify-center"
            style={{ zIndex: 5 - i }}
          >
            <Scan className="w-6 h-6 text-warm-gray-400" />
          </motion.div>
        ))}
      </div>

      {/* Счётчик */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.5, type: "spring" }}
        className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-100 rounded-full mb-2"
      >
        <CheckCircle className="w-4 h-4 text-emerald-600" />
        <span className="text-emerald-700 font-medium">
          Найдено {DEMO_DATA.labelsCount} этикетки
        </span>
      </motion.div>

      <p className="text-sm text-warm-gray-400">Извлечение штрихкодов WB...</p>
    </motion.div>
  );
}

// Фаза 3: Генерация DataMatrix
function GeneratingState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full"
    >
      <div className="flex items-center justify-center gap-8">
        {/* WB этикетки слева */}
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={`wb-${i}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.15 }}
              className="w-16 h-10 bg-warm-gray-100 rounded border border-warm-gray-200 flex items-center justify-center"
            >
              <div className="flex gap-0.5">
                {[...Array(6)].map((_, j) => (
                  <div key={j} className="w-0.5 h-4 bg-warm-gray-400" />
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Соединительные линии */}
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={`line-${i}`}
              className="w-12 h-10 flex items-center"
            >
              <svg className="w-full h-2" viewBox="0 0 48 8">
                <motion.path
                  d="M0 4 L48 4"
                  stroke="#10B981"
                  strokeWidth="2"
                  strokeDasharray="4 2"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ delay: 0.3 + i * 0.15, duration: 0.5 }}
                />
              </svg>
            </motion.div>
          ))}
        </div>

        {/* DataMatrix коды справа */}
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={`dm-${i}`}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + i * 0.15 }}
              className="w-10 h-10 bg-emerald-100 rounded border border-emerald-300 flex items-center justify-center"
            >
              <QrCode className="w-6 h-6 text-emerald-600" />
            </motion.div>
          ))}
        </div>
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="text-center text-warm-gray-600 font-medium mt-6"
      >
        Добавление кодов ЧЗ...
      </motion.p>
    </motion.div>
  );
}

// Фаза 4: Pre-flight проверка
function PreflightState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full max-w-xs mx-auto"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-emerald-50 rounded-xl p-4 border border-emerald-200"
      >
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle className="w-5 h-5 text-emerald-600" />
          <span className="font-semibold text-emerald-700">Pre-flight Check</span>
        </div>

        <div className="space-y-3">
          {DEMO_DATA.preflightChecks.map((check, i) => (
            <motion.div
              key={check.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.2 }}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.3 + i * 0.2, type: "spring" }}
                  className="w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center"
                >
                  <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none">
                    <path d="M5 12l5 5L20 7" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </motion.div>
                <span className="text-sm text-warm-gray-600">{check.name}</span>
              </div>
              <span className="text-sm font-medium text-emerald-600">{check.value}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

// Фаза 5: Готовый результат
function CompleteState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="text-center"
    >
      {/* Итоговая этикетка */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200 }}
        className="w-48 h-32 mx-auto mb-4 bg-white rounded-xl border-2 border-emerald-500 shadow-lg flex items-center p-3 gap-3"
      >
        {/* WB штрихкод */}
        <div className="flex-1 h-full bg-warm-gray-100 rounded flex flex-col items-center justify-center">
          <div className="flex gap-0.5 mb-1">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="w-0.5 h-8 bg-warm-gray-600" />
            ))}
          </div>
          <span className="text-[8px] text-warm-gray-400">WB</span>
        </div>

        {/* DataMatrix */}
        <div className="w-16 h-16 bg-emerald-100 rounded flex items-center justify-center">
          <QrCode className="w-10 h-10 text-emerald-600" />
        </div>
      </motion.div>

      {/* Метка размера */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="inline-flex items-center gap-2 px-3 py-1 bg-warm-gray-100 rounded-full text-sm text-warm-gray-600 mb-4"
      >
        58x40мм
      </motion.div>

      {/* Текст результата */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <p className="text-lg font-semibold text-warm-gray-800 mb-2">
          {DEMO_DATA.labelsCount} этикетки готовы
        </p>
        <p className="text-sm text-warm-gray-500 mb-4">
          Время обработки: {DEMO_DATA.processingTime}
        </p>
      </motion.div>

      {/* Кнопка скачать (декоративная) */}
      <motion.button
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 text-white rounded-xl font-medium opacity-75 cursor-default"
      >
        <Download className="w-5 h-5" />
        Скачать PDF
      </motion.button>
    </motion.div>
  );
}
