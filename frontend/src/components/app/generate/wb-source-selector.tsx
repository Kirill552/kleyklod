/**
 * Выбор источника товаров для Enterprise пользователей.
 * Excel файл или WB API.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FileSpreadsheet,
  Link2,
  RefreshCw,
  Settings,
  Loader2,
  Check,
  AlertTriangle,
  Package,
} from "lucide-react";
import Link from "next/link";
import { ProductSearchModal, WBProductItem } from "./product-search-modal";

interface WBIntegration {
  marketplace: string;
  connected: boolean;
  products_count: number;
  last_synced_at: string | null;
}

interface WBSourceSelectorProps {
  onSourceChange: (source: "excel" | "wb_api") => void;
  onWBProductsLoaded?: (products: WBProduct[]) => void;
}

export interface WBProduct {
  id?: number;
  barcode: string;
  name: string | null;
  article?: string | null;
  size?: string | null;
  color?: string | null;
  brand?: string | null;
}

export function WBSourceSelector({
  onSourceChange,
  onWBProductsLoaded,
}: WBSourceSelectorProps) {
  const [source, setSource] = useState<"excel" | "wb_api">("excel");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [wbInfo, setWbInfo] = useState<WBIntegration | null>(null);
  const [error, setError] = useState<string | null>(null);

  // State для modal
  const [showProductModal, setShowProductModal] = useState(false);
  const [wbProducts, setWbProducts] = useState<WBProductItem[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

  /**
   * Загрузка информации об интеграции WB.
   */
  const fetchIntegration = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/integrations");
      if (!response.ok) {
        if (response.status === 403) {
          // Не Enterprise — не показываем
          setWbInfo(null);
          return;
        }
        throw new Error("Ошибка загрузки");
      }

      const data = await response.json();
      const wb = data.integrations?.find(
        (i: WBIntegration) => i.marketplace === "wb"
      );
      setWbInfo(wb || null);
    } catch {
      setError("Не удалось загрузить информацию об интеграции");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIntegration();
  }, [fetchIntegration]);

  /**
   * Синхронизация товаров с WB.
   */
  const handleSync = async () => {
    setSyncing(true);
    setError(null);

    try {
      const response = await fetch("/api/integrations/wb/sync", {
        method: "POST",
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Ошибка синхронизации");
      }

      await fetchIntegration();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка синхронизации");
    } finally {
      setSyncing(false);
    }
  };

  /**
   * Загрузка товаров для modal.
   */
  const fetchProductsForModal = useCallback(async () => {
    setLoadingProducts(true);
    try {
      const response = await fetch("/api/integrations/wb/products");
      if (!response.ok) throw new Error("Ошибка загрузки товаров");

      const data = await response.json();
      setWbProducts(data.products || []);
    } catch {
      setError("Не удалось загрузить товары из WB");
    } finally {
      setLoadingProducts(false);
    }
  }, []);

  /**
   * Загрузка товаров из WB при выборе источника (для legacy поведения).
   */
  const loadWBProducts = useCallback(async () => {
    if (!onWBProductsLoaded) return;

    try {
      const response = await fetch("/api/integrations/wb/products");
      if (!response.ok) throw new Error("Ошибка загрузки товаров");

      const data = await response.json();
      onWBProductsLoaded(data.products || []);
    } catch {
      setError("Не удалось загрузить товары из WB");
    }
  }, [onWBProductsLoaded]);

  /**
   * Обработчик смены источника.
   */
  const handleSourceChange = (newSource: "excel" | "wb_api") => {
    setSource(newSource);
    onSourceChange(newSource);

    if (newSource === "wb_api") {
      // Сразу загружаем товары для фоновой обработки, если нужно
      loadWBProducts();
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "никогда";
    return new Date(dateString).toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Загрузка
  if (loading) {
    return (
      <Card>
        <CardContent className="py-6">
          <div className="flex items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
            <span className="text-warm-gray-600">Загрузка...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // WB не подключён — показываем баннер
  if (!wbInfo?.connected) {
    return (
      <div className="bg-gradient-to-r from-purple-50 to-emerald-50 border border-purple-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Link2 className="w-5 h-5 text-purple-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-purple-900">
              Подключите Wildberries API
            </p>
            <p className="text-sm text-purple-700 mt-1">
              Загружайте товары автоматически — без Excel файлов
            </p>
            <Link
              href="/app/settings#integrations"
              className="inline-flex items-center gap-1 text-sm text-purple-600 hover:text-purple-800 mt-2"
            >
              <Settings className="w-4 h-4" />
              Настроить интеграцию
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // WB подключён — показываем переключатель
  return (
    <Card>
      <CardContent className="py-4">
        <div className="space-y-4">
          {/* Заголовок */}
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-warm-gray-700">
              Источник товаров
            </p>
            {error && (
              <div className="flex items-center gap-1 text-xs text-red-600">
                <AlertTriangle className="w-3 h-3" />
                {error}
              </div>
            )}
          </div>

          {/* Переключатель */}
          <div className="grid grid-cols-2 gap-3">
            {/* Excel */}
            <button
              onClick={() => handleSourceChange("excel")}
              className={`p-4 rounded-lg border-2 transition-all ${
                source === "excel"
                  ? "border-emerald-500 bg-emerald-50"
                  : "border-warm-gray-200 hover:border-warm-gray-300"
              }`}
            >
              <div className="flex items-center gap-3">
                <FileSpreadsheet
                  className={`w-5 h-5 ${
                    source === "excel" ? "text-emerald-600" : "text-warm-gray-400"
                  }`}
                />
                <div className="text-left">
                  <p
                    className={`font-medium ${
                      source === "excel"
                        ? "text-emerald-900"
                        : "text-warm-gray-700"
                    }`}
                  >
                    Excel файл
                  </p>
                  <p className="text-xs text-warm-gray-500">Загрузить вручную</p>
                </div>
                {source === "excel" && (
                  <Check className="w-4 h-4 text-emerald-600 ml-auto" />
                )}
              </div>
            </button>

            {/* WB API */}
            <button
              onClick={() => handleSourceChange("wb_api")}
              className={`p-4 rounded-lg border-2 transition-all ${
                source === "wb_api"
                  ? "border-emerald-500 bg-emerald-50"
                  : "border-warm-gray-200 hover:border-warm-gray-300"
              }`}
            >
              <div className="flex items-center gap-3">
                <Link2
                  className={`w-5 h-5 ${
                    source === "wb_api"
                      ? "text-emerald-600"
                      : "text-warm-gray-400"
                  }`}
                />
                <div className="text-left">
                  <p
                    className={`font-medium ${
                      source === "wb_api"
                        ? "text-emerald-900"
                        : "text-warm-gray-700"
                    }`}
                  >
                    Wildberries API
                  </p>
                  <p className="text-xs text-warm-gray-500">
                    {wbInfo.products_count.toLocaleString()} товаров
                  </p>
                </div>
                {source === "wb_api" && (
                  <Check className="w-4 h-4 text-emerald-600 ml-auto" />
                )}
              </div>
            </button>
          </div>

          {/* Информация о WB при выборе */}
          {source === "wb_api" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-warm-gray-50 rounded-lg">
                <div className="text-sm text-warm-gray-600">
                  Синхронизация: {formatDate(wbInfo.last_synced_at)}
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleSync}
                  disabled={syncing}
                >
                  {syncing ? (
                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4 mr-1" />
                  )}
                  Обновить
                </Button>
              </div>

              {/* Кнопка выбора товаров */}
              <Button
                variant="primary"
                className="w-full"
                onClick={() => {
                  fetchProductsForModal();
                  setShowProductModal(true);
                }}
              >
                <Package className="w-4 h-4 mr-2" />
                Выбрать товары ({wbInfo.products_count.toLocaleString()})
              </Button>
            </div>
          )}
        </div>

        {/* Modal выбора товаров */}
        <ProductSearchModal
          isOpen={showProductModal}
          onClose={() => setShowProductModal(false)}
          onSelect={(selectedProducts) => {
            if (onWBProductsLoaded) {
              // Приводим типы
              const mappedProducts: WBProduct[] = selectedProducts.map(p => ({
                id: p.id,
                barcode: p.barcode,
                name: p.name,
                article: p.article,
                size: p.size,
                color: p.color,
                brand: p.brand
              }));
              onWBProductsLoaded(mappedProducts);
            }
          }}
          products={wbProducts}
          loading={loadingProducts}
        />
      </CardContent>
    </Card>
  );
}