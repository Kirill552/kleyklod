/**
 * Секция интеграции Wildberries для страницы настроек.
 * Показывается всем, но функционал только для Enterprise.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Loader2,
  Link2,
  Check,
  AlertTriangle,
  RefreshCw,
  Unlink,
  ExternalLink,
  Lock,
  Crown,
} from "lucide-react";
import Link from "next/link";

interface IntegrationInfo {
  marketplace: string;
  connected: boolean;
  products_count: number;
  connected_at: string | null;
  last_synced_at: string | null;
}

interface WBIntegrationSectionProps {
  userPlan: "free" | "pro" | "enterprise";
}

export function WBIntegrationSection({ userPlan }: WBIntegrationSectionProps) {
  const isEnterprise = userPlan === "enterprise";
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const [wbInfo, setWbInfo] = useState<IntegrationInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Форма подключения
  const [showConnectForm, setShowConnectForm] = useState(false);
  const [apiKey, setApiKey] = useState("");

  /**
   * Загрузка информации об интеграциях.
   */
  const fetchIntegrations = useCallback(async () => {
    // Для не-Enterprise не загружаем данные
    if (!isEnterprise) {
      setLoading(false);
      setWbInfo({
        marketplace: "wb",
        connected: false,
        products_count: 0,
        connected_at: null,
        last_synced_at: null,
      });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/integrations");
      if (!response.ok) {
        throw new Error("Ошибка загрузки");
      }

      const data = await response.json();
      const wb = data.integrations?.find((i: IntegrationInfo) => i.marketplace === "wb");
      // Если WB не найден в списке — устанавливаем дефолтное "не подключено"
      setWbInfo(wb || {
        marketplace: "wb",
        connected: false,
        products_count: 0,
        connected_at: null,
        last_synced_at: null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Неизвестная ошибка");
    } finally {
      setLoading(false);
    }
  }, [isEnterprise]);

  useEffect(() => {
    fetchIntegrations();
  }, [fetchIntegrations]);

  /**
   * Подключение WB.
   */
  const handleConnect = async () => {
    if (!apiKey.trim()) {
      setError("Введите API ключ");
      return;
    }

    setConnecting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/integrations/wb/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Ошибка подключения");
      }

      setSuccess(data.message);
      setApiKey("");
      setShowConnectForm(false);
      await fetchIntegrations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Неизвестная ошибка");
    } finally {
      setConnecting(false);
    }
  };

  /**
   * Синхронизация товаров.
   */
  const handleSync = async () => {
    setSyncing(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/integrations/wb/sync", {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Ошибка синхронизации");
      }

      setSuccess(`Синхронизировано ${data.synced_count} товаров (${data.new_count} новых)`);
      await fetchIntegrations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Неизвестная ошибка");
    } finally {
      setSyncing(false);
    }
  };

  /**
   * Отключение WB.
   */
  const handleDisconnect = async () => {
    if (!confirm("Отключить Wildberries? Сохранённые товары останутся в базе.")) {
      return;
    }

    setDisconnecting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/integrations/wb", {
        method: "DELETE",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Ошибка отключения");
      }

      setSuccess("Wildberries отключён");
      await fetchIntegrations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Неизвестная ошибка");
    } finally {
      setDisconnecting(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "—";
    return new Date(dateString).toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Не показываем если загрузка или нет данных (не Enterprise)
  if (loading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!wbInfo) {
    return null; // Ошибка — не показываем
  }

  // Заблокированный UI для не-Enterprise
  if (!isEnterprise) {
    return (
      <Card className="relative overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link2 className="w-5 h-5 text-warm-gray-400" />
            Интеграция Wildberries
            <span className="ml-auto flex items-center gap-1 text-sm font-normal text-amber-600">
              <Crown className="w-4 h-4" />
              Enterprise
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-warm-gray-100 flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-warm-gray-400" />
            </div>
            <p className="text-warm-gray-600 mb-2">
              Автоматическая загрузка товаров из Wildberries
            </p>
            <p className="text-sm text-warm-gray-500 mb-6">
              Доступно только на тарифе <span className="font-semibold text-amber-600">Enterprise</span>
            </p>
            <Link href="/app/subscription">
              <Button className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700">
                <Crown className="w-4 h-4 mr-2" />
                Перейти на Enterprise
              </Button>
            </Link>
          </div>

          {/* Информация о возможностях */}
          <div className="mt-4 p-4 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
            <p className="text-sm text-warm-gray-600">
              <strong>С Enterprise вы получите:</strong>
            </p>
            <ul className="mt-2 space-y-1 text-sm text-warm-gray-500">
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-500" />
                Автоматическая синхронизация товаров
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-500" />
                Выбор товаров из базы WB при генерации
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-500" />
                Безлимитная генерация этикеток
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Link2 className="w-5 h-5 text-emerald-600" />
          Интеграция Wildberries
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Ошибка */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Успех */}
        {success && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-center gap-3">
            <Check className="w-5 h-5 text-emerald-600" />
            <p className="text-sm text-emerald-800">{success}</p>
          </div>
        )}

        {wbInfo.connected ? (
          // WB подключён
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-emerald-600">
              <Check className="w-5 h-5" />
              <span className="font-medium">Подключено</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                  Товаров
                </label>
                <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                  <p className="text-warm-gray-900 font-medium">
                    {wbInfo.products_count.toLocaleString()}
                  </p>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                  Подключено
                </label>
                <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                  <p className="text-warm-gray-900">
                    {formatDate(wbInfo.connected_at)}
                  </p>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-warm-gray-600 mb-1 block">
                  Синхронизация
                </label>
                <div className="px-4 py-3 bg-warm-gray-50 rounded-lg border border-warm-gray-200">
                  <p className="text-warm-gray-900">
                    {formatDate(wbInfo.last_synced_at)}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                onClick={handleSync}
                disabled={syncing}
              >
                {syncing ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                Синхронизировать
              </Button>
              <Button
                variant="secondary"
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                {disconnecting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Unlink className="w-4 h-4 mr-2" />
                )}
                Отключить
              </Button>
            </div>
          </div>
        ) : showConnectForm ? (
          // Форма подключения
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-warm-gray-700 mb-2">
                API ключ Wildberries
              </label>
              <Input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Вставьте API ключ"
                className="font-mono"
              />
              <p className="text-xs text-warm-gray-500 mt-2">
                Создайте ключ в{" "}
                <a
                  href="https://seller.wildberries.ru/supplier-settings/access-to-api"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-600 hover:underline inline-flex items-center gap-1"
                >
                  Настройки → Доступ к API
                  <ExternalLink className="w-3 h-3" />
                </a>
                {" "}с правами «Контент»
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button
                onClick={handleConnect}
                disabled={connecting || !apiKey.trim()}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {connecting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Link2 className="w-4 h-4 mr-2" />
                )}
                Подключить
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setShowConnectForm(false);
                  setApiKey("");
                  setError(null);
                }}
              >
                Отмена
              </Button>
            </div>
          </div>
        ) : (
          // WB не подключён
          <div className="text-center py-6">
            <Link2 className="w-12 h-12 text-warm-gray-300 mx-auto mb-4" />
            <p className="text-warm-gray-600 mb-4">
              Подключите Wildberries для автоматической загрузки товаров
            </p>
            <Button
              onClick={() => setShowConnectForm(true)}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <Link2 className="w-4 h-4 mr-2" />
              Подключить Wildberries
            </Button>
          </div>
        )}

        {/* Информация */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
          <p className="text-sm text-blue-800">
            После подключения товары будут автоматически загружены в вашу базу
            для быстрой генерации этикеток.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
