"use client";

/**
 * Интерактивная демо-зона для лендинга.
 *
 * Функционал:
 * - Hover: запуск анимации демо-процесса
 * - Click: открытие Telegram Login
 * - Drag & Drop: показ подсказки о необходимости авторизации
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { AlertCircle } from "lucide-react";
import { DemoAnimation, type DemoPhase } from "./demo-animation";
import { ANIMATION_PHASES } from "./demo-assets";

interface DemoDropzoneProps {
  onLoginClick: () => void;
}

export function DemoDropzone({ onLoginClick }: DemoDropzoneProps) {
  const [phase, setPhase] = useState<DemoPhase>("idle");
  const [showLoginTooltip, setShowLoginTooltip] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const phaseTimeoutsRef = useRef<NodeJS.Timeout[]>([]);

  // Очистка таймеров при размонтировании
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      phaseTimeoutsRef.current.forEach(clearTimeout);
    };
  }, []);

  // Запуск анимации при наведении (только если не играет)
  const startAnimation = useCallback(() => {
    // Если анимация уже идёт — не перезапускаем
    if (isAnimating) return;

    setIsAnimating(true);

    // Очищаем предыдущие таймеры
    phaseTimeoutsRef.current.forEach(clearTimeout);
    phaseTimeoutsRef.current = [];

    // Фаза 1: Загрузка
    setPhase("uploading");

    // Фаза 2: Парсинг
    const t1 = setTimeout(() => {
      setPhase("parsing");
    }, ANIMATION_PHASES.parse.start);
    phaseTimeoutsRef.current.push(t1);

    // Фаза 3: Генерация
    const t2 = setTimeout(() => {
      setPhase("generating");
    }, ANIMATION_PHASES.generate.start);
    phaseTimeoutsRef.current.push(t2);

    // Фаза 4: Pre-flight
    const t3 = setTimeout(() => {
      setPhase("preflight");
    }, ANIMATION_PHASES.preflight.start);
    phaseTimeoutsRef.current.push(t3);

    // Фаза 5: Готово
    const t4 = setTimeout(() => {
      setPhase("complete");
    }, ANIMATION_PHASES.complete.start);
    phaseTimeoutsRef.current.push(t4);
  }, [isAnimating]);

  // Остановка анимации при уходе курсора
  const stopAnimation = useCallback(() => {
    phaseTimeoutsRef.current.forEach(clearTimeout);
    phaseTimeoutsRef.current = [];

    // Сбрасываем флаг анимации
    setIsAnimating(false);

    // Плавный возврат к начальному состоянию
    timeoutRef.current = setTimeout(() => {
      setPhase("idle");
    }, 300);
  }, []);

  // Обработка drag & drop (показ подсказки)
  const onDrop = useCallback(() => {
    setShowLoginTooltip(true);
    setTimeout(() => setShowLoginTooltip(false), 3000);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true, // Клик обрабатываем отдельно
    accept: {
      "application/pdf": [".pdf"],
    },
  });

  // Обработка клика — открытие Telegram Login
  const handleClick = useCallback(() => {
    onLoginClick();
  }, [onLoginClick]);

  return (
    <div className="relative">
      {/* Основная зона */}
      <div
        {...getRootProps()}
        onMouseEnter={startAnimation}
        onMouseLeave={stopAnimation}
        onClick={handleClick}
        className={`
          relative p-8 rounded-2xl border-2 border-dashed cursor-pointer
          transition-all duration-300 min-h-[320px]
          ${isDragActive
            ? "border-amber-400 bg-amber-50"
            : phase !== "idle"
              ? "border-emerald-400 bg-emerald-50/50"
              : "border-warm-gray-300 bg-warm-gray-50 hover:border-emerald-400 hover:bg-emerald-50/30"
          }
        `}
      >
        <input {...getInputProps()} />

        {/* Анимация демо */}
        <DemoAnimation phase={phase} />

        {/* Подсказка при drag */}
        <AnimatePresence>
          {isDragActive && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-amber-100/90 rounded-2xl flex items-center justify-center"
            >
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-2" />
                <p className="text-amber-700 font-medium">
                  Отпустите файл для загрузки
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Tooltip при попытке загрузки */}
      <AnimatePresence>
        {showLoginTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute -bottom-16 left-1/2 -translate-x-1/2 z-10"
          >
            <div className="bg-warm-gray-800 text-white px-4 py-2 rounded-lg shadow-lg whitespace-nowrap">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-400" />
                <span>Войдите через Telegram чтобы загрузить файлы</span>
              </div>
              {/* Стрелка */}
              <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-0 h-0 border-l-8 border-r-8 border-b-8 border-transparent border-b-warm-gray-800" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Индикатор безопасности */}
      <div className="mt-4 flex items-center justify-center gap-2 text-sm text-warm-gray-400">
        <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
        Pre-flight проверка включена
      </div>

      {/* Подсказка о клике */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="text-center text-sm text-warm-gray-400 mt-2"
      >
        Нажмите для входа через Telegram
      </motion.p>
    </div>
  );
}
