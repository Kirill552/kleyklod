"use client";

/**
 * Страница управления карточками товаров.
 *
 * Позволяет сохранять товары для автоматического продолжения нумерации.
 * Доступна только для PRO и ENTERPRISE планов.
 */

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import {
  getProducts,
  upsertProduct,
  deleteProduct,
  type ProductCard,
  type ProductCardCreate,
  type ProductListResponse,
} from "@/lib/api";
import { ProductTable } from "@/components/app/products/product-table";
import { ProductModal } from "@/components/app/products/product-modal";
import {
  Package,
  Plus,
  Search,
  Loader2,
  AlertTriangle,
  Crown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { analytics } from "@/lib/analytics";

export default function ProductsPage() {
  const { user, loading: authLoading } = useAuth();

  const [products, setProducts] = useState<ProductCard[]>([]);
  const [total, setTotal] = useState(0);
  const [canCreateMore, setCanCreateMore] = useState(true);
  const [maxAllowed, setMaxAllowed] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Модалка
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<ProductCard | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<ProductCard | null>(null);

  const limit = 20;
  const totalPages = Math.ceil(total / limit);

  /**
   * Загрузка карточек.
   */
  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data: ProductListResponse = await getProducts({
        search: searchQuery || undefined,
        limit,
        offset: (page - 1) * limit,
      });

      setProducts(data.items);
      setTotal(data.total);
      setCanCreateMore(data.can_create_more);
      setMaxAllowed(data.max_allowed);
    } catch (err) {
      console.error("Ошибка загрузки карточек:", err);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Ошибка загрузки");
      }
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery]);

  useEffect(() => {
    if (!authLoading && user) {
      loadProducts();
    }
  }, [authLoading, user, loadProducts]);

  // Debounce поиска
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!authLoading && user) {
        setPage(1); // Сбрасываем на первую страницу при поиске
        loadProducts();
      }
    }, 300);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  /**
   * Открыть модалку создания.
   */
  const handleCreate = () => {
    setEditingProduct(null);
    setIsModalOpen(true);
  };

  /**
   * Открыть модалку редактирования.
   */
  const handleEdit = (product: ProductCard) => {
    setEditingProduct(product);
    setIsModalOpen(true);
  };

  /**
   * Подтверждение удаления.
   */
  const handleDeleteClick = (product: ProductCard) => {
    setDeleteConfirm(product);
  };

  /**
   * Сохранение карточки.
   */
  const handleSave = async (data: ProductCardCreate) => {
    await upsertProduct(data.barcode, data);
    // Трекинг сохранения товара
    analytics.productSaved();
    loadProducts();
  };

  /**
   * Удаление карточки.
   */
  const handleConfirmDelete = async () => {
    if (!deleteConfirm) return;

    try {
      await deleteProduct(deleteConfirm.barcode);
      setDeleteConfirm(null);
      loadProducts();
    } catch (err) {
      console.error("Ошибка удаления:", err);
    }
  };

  // Загрузка
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-warm-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  // Проверка тарифа
  if (user?.plan === "free") {
    return (
      <div className="space-y-8">
        {/* Заголовок */}
        <div>
          <h1 className="text-3xl font-bold text-warm-gray-900 mb-2">
            База карточек товаров
          </h1>
          <p className="text-warm-gray-600">
            Сохраняйте товары для автоматического продолжения нумерации
          </p>
        </div>

        {/* Блок для FREE плана */}
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="py-12">
            <div className="text-center max-w-md mx-auto">
              <Crown className="w-16 h-16 text-amber-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-warm-gray-900 mb-2">
                Доступно на PRO
              </h2>
              <p className="text-warm-gray-600 mb-6">
                База карточек товаров позволяет сохранять информацию о ваших товарах
                и автоматически продолжать нумерацию этикеток.
              </p>
              <ul className="text-left space-y-2 mb-6">
                <li className="flex items-center gap-2 text-warm-gray-700">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                  До 100 карточек товаров
                </li>
                <li className="flex items-center gap-2 text-warm-gray-700">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                  Автоматическая нумерация
                </li>
                <li className="flex items-center gap-2 text-warm-gray-700">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                  Быстрая генерация этикеток
                </li>
              </ul>
              <Link href="/app/subscription">
                <Button variant="primary" size="md">
                  <Crown className="w-5 h-5" />
                  Перейти на PRO
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Заголовок */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-warm-gray-900 mb-2">
            База карточек товаров
          </h1>
          <p className="text-warm-gray-600">
            Сохраняйте товары для автоматического продолжения нумерации
          </p>
        </div>
        <Button
          variant="primary"
          onClick={handleCreate}
          disabled={!canCreateMore}
        >
          <Plus className="w-5 h-5" />
          Добавить карточку
        </Button>
      </div>

      {/* Счётчик для PRO */}
      {maxAllowed && (
        <div className="flex items-center gap-2 text-sm text-warm-gray-600">
          <Package className="w-4 h-4" />
          <span>
            {total} из {maxAllowed} карточек
          </span>
          {!canCreateMore && (
            <span className="text-amber-600">
              (лимит достигнут)
            </span>
          )}
        </div>
      )}

      {/* Ошибка */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Карточка с таблицей */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="flex items-center gap-2">
              <Package className="w-5 h-5 text-emerald-600" />
              Карточки товаров
              {total > 0 && (
                <span className="text-sm font-normal text-warm-gray-500">
                  ({total})
                </span>
              )}
            </CardTitle>

            {/* Поиск */}
            <div className="relative max-w-xs w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-warm-gray-400" />
              <input
                type="text"
                placeholder="Поиск по баркоду, названию..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-warm-gray-300 bg-white
                  text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
            </div>
          ) : products.length === 0 ? (
            <div className="border-2 border-dashed border-warm-gray-300 rounded-lg p-12">
              <div className="text-center">
                <Package className="w-16 h-16 text-warm-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-warm-gray-700 mb-2">
                  {searchQuery ? "Ничего не найдено" : "Нет карточек"}
                </h3>
                <p className="text-warm-gray-500 mb-6">
                  {searchQuery
                    ? "Попробуйте изменить запрос"
                    : "Добавьте первую карточку товара"}
                </p>
                {!searchQuery && (
                  <Button
                    variant="primary"
                    onClick={handleCreate}
                  >
                    <Plus className="w-5 h-5" />
                    Добавить карточку
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <>
              <ProductTable
                products={products}
                onEdit={handleEdit}
                onDelete={handleDeleteClick}
              />

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
            </>
          )}
        </CardContent>
      </Card>

      {/* Модалка создания/редактирования */}
      <ProductModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        product={editingProduct}
      />

      {/* Диалог подтверждения удаления */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setDeleteConfirm(null)}
          />
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold text-warm-gray-900 mb-2">
              Удалить карточку?
            </h3>
            <p className="text-warm-gray-600 mb-6">
              Карточка с баркодом{" "}
              <span className="font-mono font-medium">{deleteConfirm.barcode}</span>{" "}
              будет удалена. Это действие нельзя отменить.
            </p>
            <div className="flex items-center justify-end gap-3">
              <Button
                variant="secondary"
                onClick={() => setDeleteConfirm(null)}
              >
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={handleConfirmDelete}
              >
                Удалить
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
