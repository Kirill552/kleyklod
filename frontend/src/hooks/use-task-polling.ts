/**
 * Hook для polling статуса фоновых задач Celery.
 *
 * Используется для отслеживания прогресса долгих операций
 * (генерация 50+ этикеток) с реальным прогресс-баром.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { getTaskStatus, type TaskStatusResponse, type TaskStatusValue } from "@/lib/api";

/** Интервал polling в миллисекундах */
const POLL_INTERVAL = 3000;

/** Состояние hook */
export interface TaskPollingState {
  /** Текущий статус задачи */
  status: TaskStatusValue | null;
  /** Прогресс 0-100 */
  progress: number;
  /** URL для скачивания результата (когда completed) */
  resultUrl: string | null;
  /** Сообщение об ошибке (когда failed) */
  error: string | null;
  /** Количество этикеток в результате */
  labelsCount: number | null;
  /** Идёт ли сейчас polling */
  isPolling: boolean;
}

/** Опции hook */
export interface UseTaskPollingOptions {
  /** Callback при завершении задачи */
  onComplete?: (status: TaskStatusResponse) => void;
  /** Callback при ошибке */
  onError?: (error: string) => void;
  /** Интервал polling (по умолчанию 3 сек) */
  interval?: number;
}

/**
 * Hook для polling статуса фоновой задачи.
 *
 * @param taskId - ID задачи (null = не начинать polling)
 * @param options - Опции (callbacks, interval)
 * @returns Текущее состояние задачи
 *
 * @example
 * ```tsx
 * const { status, progress, resultUrl, error, isPolling } = useTaskPolling(taskId, {
 *   onComplete: (result) => console.log("Готово!", result.labels_count),
 *   onError: (err) => console.error("Ошибка:", err),
 * });
 * ```
 */
export function useTaskPolling(
  taskId: string | null,
  options: UseTaskPollingOptions = {}
): TaskPollingState {
  const { onComplete, onError, interval = POLL_INTERVAL } = options;

  // Состояние
  const [state, setState] = useState<TaskPollingState>({
    status: null,
    progress: 0,
    resultUrl: null,
    error: null,
    labelsCount: null,
    isPolling: false,
  });

  // Ref для отмены polling при unmount
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  /**
   * Остановить polling.
   */
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearTimeout(pollingRef.current);
      pollingRef.current = null;
    }
    if (mountedRef.current) {
      setState((prev) => ({ ...prev, isPolling: false }));
    }
  }, []);

  /**
   * Выполнить один запрос статуса.
   */
  const poll = useCallback(async () => {
    if (!taskId || !mountedRef.current) return;

    try {
      const result = await getTaskStatus(taskId);

      if (!mountedRef.current) return;

      // Обновляем состояние
      setState({
        status: result.status,
        progress: result.progress,
        resultUrl: result.result_url,
        error: result.error,
        labelsCount: result.labels_count,
        isPolling: result.status === "pending" || result.status === "processing",
      });

      // Обработка завершения
      if (result.status === "completed") {
        stopPolling();
        onComplete?.(result);
      } else if (result.status === "failed") {
        stopPolling();
        onError?.(result.error || "Неизвестная ошибка");
      } else {
        // Продолжаем polling
        pollingRef.current = setTimeout(poll, interval);
      }
    } catch (err) {
      if (!mountedRef.current) return;

      const errorMessage = err instanceof Error ? err.message : "Ошибка получения статуса";
      setState((prev) => ({
        ...prev,
        status: "failed",
        error: errorMessage,
        isPolling: false,
      }));
      stopPolling();
      onError?.(errorMessage);
    }
  }, [taskId, interval, onComplete, onError, stopPolling]);

  // Эффект для запуска/остановки polling
  useEffect(() => {
    mountedRef.current = true;

    if (taskId) {
      // Сбрасываем состояние и начинаем polling
      setState({
        status: "pending",
        progress: 0,
        resultUrl: null,
        error: null,
        labelsCount: null,
        isPolling: true,
      });
      poll();
    } else {
      // Останавливаем polling и сбрасываем состояние
      stopPolling();
      setState({
        status: null,
        progress: 0,
        resultUrl: null,
        error: null,
        labelsCount: null,
        isPolling: false,
      });
    }

    return () => {
      mountedRef.current = false;
      stopPolling();
    };
  }, [taskId, poll, stopPolling]);

  return state;
}
