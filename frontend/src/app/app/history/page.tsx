"use client";

/**
 * Страница истории генераций.
 *
 * Отображает список всех созданных этикеток с возможностью
 * скачивания и удаления.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getGenerations, downloadGeneration } from "@/lib/api";
import type { Generation } from "@/types/api";
import {
  History,
  Download,
  FileText,
  Loader2,
  CheckCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export default function HistoryPage() {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const limit = 10;
  const totalPages = Math.ceil(total / limit);

  /**
   * Загрузка истории генераций.
   */
  useEffect(() => {
    async function loadGenerations() {
      try {
        setLoading(true);
        setError(null);
        const data = await getGenerations(page, limit);
        setGenerations(data.items);
        setTotal(data.total);
      } catch (err) {
        console.error("Ошибка загрузки истории:", err);
        setError(err instanceof Error ? err.message : "Ошибка загрузки");
      } finally {
        setLoading(false);
      }
    }

    loadGenerations();
  }, [page]);

  /**
   * Скачивание файла генерации.
   */
  const handleDownload = async (generation: Generation) => {
    try {
      setDownloadingId(generation.id);
      const blob = await downloadGeneration(generation.id);

      // Создаём ссылку для скачивания
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `labels_${generation.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Ошибка скачивания:", err);
    } finally {
      setDownloadingId(null);
    }
  };

  /**
   * Форматирование даты.
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Загрузка
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-warm-gray-600">Загрузка истории...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold text-warm-gray-900 mb-2">
          История генераций
        </h1>
        <p className="text-warm-gray-600">
          Все ваши созданные этикетки доступны здесь
        </p>
      </div>

      {/* Ошибка */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Таблица с историей */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5 text-emerald-600" />
            Последние генерации
            {total > 0 && (
              <span className="text-sm font-normal text-warm-gray-500">
                ({total} всего)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {generations.length === 0 ? (
            // Пустое состояние
            <div className="border-2 border-dashed border-warm-gray-300 rounded-lg p-12">
              <div className="text-center">
                <FileText className="w-16 h-16 text-warm-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-warm-gray-700 mb-2">
                  История пуста
                </h3>
                <p className="text-warm-gray-500 mb-6">
                  Вы еще не создали ни одной этикетки. Начните прямо сейчас!
                </p>
                <Link href="/app/generate">
                  <Button variant="primary" size="md">
                    Создать этикетки
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            // Таблица
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-warm-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
                      Дата
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
                      Количество
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-warm-gray-700">
                      Статус
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-warm-gray-700">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {generations.map((generation) => (
                    <tr
                      key={generation.id}
                      className="border-b border-warm-gray-100 hover:bg-warm-gray-50 transition-colors"
                    >
                      <td className="py-4 px-4 text-sm text-warm-gray-600">
                        {formatDate(generation.created_at)}
                      </td>
                      <td className="py-4 px-4 text-sm text-warm-gray-900 font-medium">
                        {generation.labels_count} этикеток
                      </td>
                      <td className="py-4 px-4">
                        {generation.preflight_passed ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                            <CheckCircle className="w-3 h-3" />
                            Готово
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                            <AlertTriangle className="w-3 h-3" />
                            С предупреждениями
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(generation)}
                            disabled={
                              !generation.file_path ||
                              downloadingId === generation.id
                            }
                          >
                            {downloadingId === generation.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Download className="w-4 h-4" />
                            )}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Пагинация */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-warm-gray-200">
                  <p className="text-sm text-warm-gray-600">
                    Страница {page} из {totalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Назад
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      Вперёд
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
