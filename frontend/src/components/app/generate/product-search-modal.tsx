/**
 * Fullscreen modal для выбора товаров из WB API.
 * Двухуровневый поиск: uFuzzy (мгновенный) + EmbeddingGemma (семантический).
 */

"use client";

import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Search,
  ArrowLeft,
  Loader2,
  Package,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import {
  ProductSearch,
  SearchableProduct,
  prepareForSearch,
} from "@/lib/product-search";

export interface WBProductItem {
  id: number;
  barcode: string;
  name: string | null;
  article: string | null;
  size: string | null;
  color: string | null;
  brand: string | null;
}

interface ProductSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (products: WBProductItem[]) => void;
  products: WBProductItem[];
  loading?: boolean;
}

const ITEMS_PER_PAGE = 20;

export function ProductSearchModal({
  isOpen,
  onClose,
  onSelect,
  products,
  loading = false,
}: ProductSearchModalProps) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  
  // Semantic search state
  const [isSemanticLoading, setIsSemanticLoading] = useState(false);
  const [useSemanticSearch, setUseSemanticSearch] = useState(false);

  // Filters state
  const [sizeFilter, setSizeFilter] = useState<string>("");
  const [colorFilter, setColorFilter] = useState<string>("");

  // Подготовленные для поиска товары
  const searchableProducts = useMemo(
    () => products.map(prepareForSearch),
    [products]
  );

  // Уникальные размеры и цвета для фильтров
  const uniqueSizes = useMemo(() => {
    const sizes = new Set<string>();
    products.forEach((p) => {
      if (p.size) sizes.add(p.size);
    });
    return Array.from(sizes).sort();
  }, [products]);

  const uniqueColors = useMemo(() => {
    const colors = new Set<string>();
    products.forEach((p) => {
      if (p.color) colors.add(p.color);
    });
    return Array.from(colors).sort();
  }, [products]);

  // Инстанс поиска
  const searchRef = useRef(new ProductSearch());

  // Результаты поиска
  const [results, setResults] = useState<SearchableProduct[]>([]);

  // Debounced search с двухуровневой логикой
  useEffect(() => {
    const timer = setTimeout(async () => {
      // Уровень 1: Fuzzy search
      const fuzzyResults = searchRef.current.fuzzySearch(
        searchableProducts,
        query,
        1000
      );
      setResults(fuzzyResults);
      setCurrentPage(1);

      // Уровень 2: Semantic search только если fuzzy ничего не нашёл
      if (query.trim() && fuzzyResults.length === 0 && useSemanticSearch) {
        setIsSemanticLoading(true);
        try {
          const semanticResults = await searchRef.current.semanticSearch(
            searchableProducts,
            query,
            1000
          );
          setResults(semanticResults);
        } catch (error) {
          console.error("Ошибка semantic search:", error);
        } finally {
          setIsSemanticLoading(false);
        }
      }
    }, 150);

    return () => clearTimeout(timer);
  }, [query, searchableProducts, useSemanticSearch]);

  // Инициализация результатов
  useEffect(() => {
    if (!query.trim()) {
      setResults(searchableProducts);
    }
  }, [searchableProducts, query]);

  // Отфильтрованные результаты
  const filteredResults = useMemo(() => {
    return results.filter((p) => {
      if (sizeFilter && p.size !== sizeFilter) return false;
      if (colorFilter && p.color !== colorFilter) return false;
      return true;
    });
  }, [results, sizeFilter, colorFilter]);

  // Пагинация
  const totalPages = Math.ceil(filteredResults.length / ITEMS_PER_PAGE);
  const paginatedResults = filteredResults.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // Toggle выбора товара
  const toggleProduct = useCallback((id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  // Toggle всех на текущей странице
  const toggleAllOnPage = useCallback(() => {
    const pageIds = paginatedResults.map((p) => p.id);
    const allSelected = pageIds.every((id) => selected.has(id));

    setSelected((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        pageIds.forEach((id) => next.delete(id));
      } else {
        pageIds.forEach((id) => next.add(id));
      }
      return next;
    });
  }, [paginatedResults, selected]);

  // Подтверждение выбора
  const handleConfirm = () => {
    const selectedProducts = products.filter((p) => selected.has(p.id));
    onSelect(selectedProducts);
    onClose();
  };

  // Сброс при закрытии
  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setSelected(new Set());
      setCurrentPage(1);
      setUseSemanticSearch(false);
      setSizeFilter("");
      setColorFilter("");
    }
  }, [isOpen]);

  // Проверка состояния чекбокса "Выбрать все"
  const pageIds = paginatedResults.map((p) => p.id);
  const allOnPageSelected = pageIds.length > 0 && pageIds.every((id) => selected.has(id));
  const someOnPageSelected = pageIds.some((id) => selected.has(id)) && !allOnPageSelected;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent fullscreen>
        {/* Header */}
        <DialogHeader onClose={onClose}>
          <div className="flex items-center gap-4">
            <button
              onClick={onClose}
              className="p-2 -ml-2 rounded-lg text-warm-gray-500 hover:text-warm-gray-700 hover:bg-warm-gray-100 transition-all"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <DialogTitle>Выбор товаров из Wildberries</DialogTitle>
          </div>
        </DialogHeader>

        {/* Search + Filters */}
        <div className="px-6 py-4 border-b border-warm-gray-200 bg-warm-gray-50">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-4">
              {/* Поиск */}
              <div className="relative flex-1 max-w-xl">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-warm-gray-400" />
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Поиск по названию, артикулу, баркоду..."
                  className="pl-10"
                />
              </div>

              {/* Toggle умного поиска */}
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <Checkbox
                  checked={useSemanticSearch}
                  onChange={(e) => setUseSemanticSearch((e.target as HTMLInputElement).checked)}
                />
                <span className="text-sm text-warm-gray-700 font-medium">
                  Умный поиск
                  {isSemanticLoading && (
                    <Loader2 className="inline w-3 h-3 ml-1 animate-spin text-emerald-600" />
                  )}
                </span>
                <span className="text-xs text-warm-gray-500">
                  (понимает синонимы)
                </span>
              </label>

              {/* Счётчик выбранных */}
              <div className="text-sm text-warm-gray-600 ml-auto">
                Выбрано:{" "}
                <span className="font-semibold text-emerald-600">
                  {selected.size}
                </span>{" "}
                товаров
              </div>
            </div>

            {/* Фильтры */}
            <div className="flex items-center gap-3">
              {/* Фильтр по размеру */}
              {uniqueSizes.length > 0 && (
                <select
                  value={sizeFilter}
                  onChange={(e) => {
                    setSizeFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-3 py-2 rounded-xl border border-warm-gray-300 bg-white text-sm
                    focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Все размеры</option>
                  {uniqueSizes.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              )}

              {/* Фильтр по цвету */}
              {uniqueColors.length > 0 && (
                <select
                  value={colorFilter}
                  onChange={(e) => {
                    setColorFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-3 py-2 rounded-xl border border-warm-gray-300 bg-white text-sm
                    focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Все цвета</option>
                  {uniqueColors.map((color) => (
                    <option key={color} value={color}>
                      {color}
                    </option>
                  ))}
                </select>
              )}

              {/* Сброс фильтров */}
              {(sizeFilter || colorFilter) && (
                <button
                  onClick={() => {
                    setSizeFilter("");
                    setColorFilter("");
                    setCurrentPage(1);
                  }}
                  className="text-sm text-emerald-600 hover:text-emerald-800 transition-colors"
                >
                  Сбросить
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
              <span className="ml-3 text-warm-gray-600">
                Загрузка товаров...
              </span>
            </div>
          ) : filteredResults.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-warm-gray-500">
              <Package className="w-12 h-12 mb-3 text-warm-gray-300" />
              <p className="font-medium">Товары не найдены</p>
              <p className="text-sm mt-1">
                {sizeFilter || colorFilter
                  ? "Попробуйте сбросить фильтры"
                  : "Попробуйте изменить запрос или синхронизировать товары"}
              </p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="sticky top-0 bg-white border-b border-warm-gray-200">
                <tr>
                  <th className="py-3 px-4 text-left w-12">
                    <Checkbox
                      checked={allOnPageSelected}
                      indeterminate={someOnPageSelected}
                      onChange={toggleAllOnPage}
                    />
                  </th>
                  <th className="py-3 px-4 text-left text-sm font-semibold text-warm-gray-700">
                    Название
                  </th>
                  <th className="py-3 px-4 text-left text-sm font-semibold text-warm-gray-700">
                    Артикул
                  </th>
                  <th className="py-3 px-4 text-left text-sm font-semibold text-warm-gray-700">
                    Размер
                  </th>
                  <th className="py-3 px-4 text-left text-sm font-semibold text-warm-gray-700">
                    Цвет
                  </th>
                  <th className="py-3 px-4 text-left text-sm font-semibold text-warm-gray-700">
                    Баркод
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedResults.map((product) => (
                  <tr
                    key={product.id}
                    onClick={() => toggleProduct(product.id)}
                    className={`border-b border-warm-gray-100 cursor-pointer transition-all ${
                      selected.has(product.id)
                        ? "bg-emerald-50"
                        : "hover:bg-warm-gray-50"
                    }`}
                  >
                    <td className="py-3 px-4">
                      <Checkbox
                        checked={selected.has(product.id)}
                        onChange={() => toggleProduct(product.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-medium text-warm-gray-900">
                        {product.name || "—"}
                      </span>
                      {product.brand && (
                        <span className="ml-2 text-xs text-emerald-600">
                          {product.brand}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm text-warm-gray-700">
                      {product.article || "—"}
                    </td>
                    <td className="py-3 px-4 text-sm text-warm-gray-700">
                      {product.size || "—"}
                    </td>
                    <td className="py-3 px-4 text-sm text-warm-gray-700">
                      {product.color || "—"}
                    </td>
                    <td className="py-3 px-4">
                      <code className="text-xs bg-warm-gray-100 px-2 py-1 rounded font-mono">
                        {product.barcode}
                      </code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-3 border-t border-warm-gray-200 flex items-center justify-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>

            <span className="text-sm text-warm-gray-600 mx-4">
              Страница {currentPage} из {totalPages}
            </span>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}

        {/* Footer */}
        <DialogFooter>
          <div className="flex items-center gap-2 text-sm text-warm-gray-600">
            <Package className="w-4 h-4" />
            Найдено: {filteredResults.length} товаров
          </div>

          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={onClose}>
              Отмена
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirm}
              disabled={selected.size === 0}
            >
              Выбрать {selected.size > 0 && `(${selected.size})`}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
