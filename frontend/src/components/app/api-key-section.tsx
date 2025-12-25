"use client";

/**
 * Компонент для управления API ключами.
 *
 * Отображает:
 * - Информацию о текущем ключе (если есть)
 * - Кнопку создания нового ключа
 * - Кнопку отзыва ключа
 *
 * Только для Enterprise пользователей.
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getApiKeyInfo, createApiKey, revokeApiKey } from "@/lib/api";
import type { ApiKeyInfo } from "@/types/api";
import {
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
  AlertTriangle,
  Loader2,
  Clock,
  Calendar,
} from "lucide-react";

interface ApiKeySectionProps {
  /** Тарифный план пользователя */
  plan: string;
}

export function ApiKeySection({ plan }: ApiKeySectionProps) {
  const [keyInfo, setKeyInfo] = useState<ApiKeyInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Загружаем информацию о ключе
  const loadKeyInfo = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const info = await getApiKeyInfo();
      setKeyInfo(info);
    } catch (err) {
      console.error("Ошибка загрузки информации о ключе:", err);
      // Не показываем ошибку если просто нет ключа
      if (err instanceof Error && !err.message.includes("404")) {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (plan === "enterprise") {
      loadKeyInfo();
    } else {
      setLoading(false);
    }
  }, [plan, loadKeyInfo]);

  // Создание нового ключа
  const handleCreateKey = async () => {
    try {
      setCreating(true);
      setError(null);
      setNewKey(null);

      const result = await createApiKey();
      setNewKey(result.api_key);

      // Обновляем информацию о ключе
      await loadKeyInfo();
    } catch (err) {
      console.error("Ошибка создания ключа:", err);
      setError(err instanceof Error ? err.message : "Ошибка создания ключа");
    } finally {
      setCreating(false);
    }
  };

  // Отзыв ключа
  const handleRevokeKey = async () => {
    if (!confirm("Вы уверены? После отзыва ключ перестанет работать.")) {
      return;
    }

    try {
      setRevoking(true);
      setError(null);
      setNewKey(null);

      await revokeApiKey();
      setKeyInfo(null);
    } catch (err) {
      console.error("Ошибка отзыва ключа:", err);
      setError(err instanceof Error ? err.message : "Ошибка отзыва ключа");
    } finally {
      setRevoking(false);
    }
  };

  // Копирование ключа
  const handleCopyKey = async () => {
    if (!newKey) return;

    try {
      await navigator.clipboard.writeText(newKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Ошибка копирования:", err);
    }
  };

  // Форматирование даты
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Если не Enterprise — показываем CTA
  if (plan !== "enterprise") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5 text-purple-600" />
            API доступ
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-purple-900">
                  Доступно только для Enterprise
                </p>
                <p className="text-sm text-purple-700 mt-1">
                  API доступ позволяет автоматизировать генерацию этикеток
                  через REST API. Перейдите на тариф Enterprise для
                  использования.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Загрузка
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5 text-purple-600" />
            API ключ
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            <span className="ml-2 text-warm-gray-600">Загрузка...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Key className="w-5 h-5 text-purple-600" />
          API ключ
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Ошибка */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Новый ключ (показывается один раз после создания) */}
        {newKey && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div className="flex items-start gap-3">
              <Check className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-emerald-900 mb-2">
                  Ключ успешно создан!
                </p>
                <div className="flex items-center gap-2 mb-2">
                  <code className="flex-1 p-2 bg-white border border-emerald-300 rounded text-sm font-mono break-all">
                    {newKey}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopyKey}
                    className="flex-shrink-0"
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                <p className="text-sm text-emerald-700">
                  <AlertTriangle className="w-4 h-4 inline mr-1" />
                  Сохраните ключ! Он больше не будет показан.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Информация о существующем ключе */}
        {keyInfo?.prefix ? (
          <div className="space-y-3">
            <div className="p-4 bg-warm-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-warm-gray-600">Ваш ключ</span>
                <span className="font-mono text-warm-gray-900">
                  {keyInfo.prefix}...
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-warm-gray-400" />
                  <span className="text-warm-gray-600">Создан:</span>
                  <span className="text-warm-gray-900">
                    {formatDate(keyInfo.created_at)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-warm-gray-400" />
                  <span className="text-warm-gray-600">Использован:</span>
                  <span className="text-warm-gray-900">
                    {keyInfo.last_used_at
                      ? formatDate(keyInfo.last_used_at)
                      : "Никогда"}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleCreateKey}
                disabled={creating}
              >
                {creating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                Создать новый
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleRevokeKey}
                disabled={revoking}
              >
                {revoking ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                Отозвать
              </Button>
            </div>

            <p className="text-xs text-warm-gray-500">
              При создании нового ключа старый будет автоматически отозван.
            </p>
          </div>
        ) : (
          /* Нет ключа — предлагаем создать */
          <div className="text-center py-6">
            <Key className="w-12 h-12 text-warm-gray-300 mx-auto mb-3" />
            <p className="text-warm-gray-600 mb-4">
              У вас пока нет API ключа
            </p>
            <Button
              variant="primary"
              onClick={handleCreateKey}
              disabled={creating}
            >
              {creating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              Создать API ключ
            </Button>
          </div>
        )}

        {/* Документация */}
        <div className="pt-4 border-t border-warm-gray-100">
          <p className="text-sm text-warm-gray-600">
            Документация API:{" "}
            <a
              href="/docs/api"
              className="text-purple-600 hover:text-purple-700 font-medium"
            >
              Перейти к документации
            </a>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
