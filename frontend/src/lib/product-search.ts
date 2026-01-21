/**
 * Двухуровневый поиск товаров.
 * Уровень 1: uFuzzy — мгновенный fuzzy match
 * Уровень 2: EmbeddingGemma — семантический поиск (lazy load)
 */

import uFuzzy from "@leeoniya/ufuzzy";

export interface SearchableProduct {
  id: number;
  barcode: string;
  name: string;
  article: string | null;
  size: string | null;
  color: string | null;
  brand: string | null;
  searchText: string; // Склеенные поля для поиска
}

/**
 * Подготовить товар для поиска.
 */
export function prepareForSearch(product: {
  id: number;
  barcode: string;
  name: string | null;
  article: string | null;
  size: string | null;
  color: string | null;
  brand: string | null;
}): SearchableProduct {
  return {
    id: product.id,
    barcode: product.barcode,
    name: product.name || "",
    article: product.article,
    size: product.size,
    color: product.color,
    brand: product.brand,
    searchText: [
      product.name,
      product.article,
      product.barcode,
      product.size,
      product.color,
      product.brand,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase(),
  };
}

/**
 * Класс для двухуровневого поиска.
 */
export class ProductSearch {
  private ufuzzy: uFuzzy;
  
  // Lazy-loaded embedder
  private embedder: unknown = null;
  private productEmbeddings: Map<number, number[]> = new Map();
  private embeddingsLoading: boolean = false;

  constructor() {
    this.ufuzzy = new uFuzzy({
      intraMode: 1, // Разрешить пропуски внутри слов
      intraIns: 1,
    });
  }

  /**
   * Уровень 1: Быстрый fuzzy search.
   * Возвращает до maxResults результатов.
   */
  fuzzySearch(
    products: SearchableProduct[],
    query: string,
    maxResults: number = 50
  ): SearchableProduct[] {
    if (!query.trim()) {
      return products.slice(0, maxResults);
    }

    const haystack = products.map((p) => p.searchText);
    const result = this.ufuzzy.search(haystack, query.toLowerCase());

    if (!result || !result[0] || !result[2]) {
      return [];
    }

    const [idxs, , order] = result;
    return order.slice(0, maxResults).map((i) => products[idxs[i]]);
  }

  /**
   * Уровень 2: Семантический поиск с EmbeddingGemma.
   * Загружает модель при первом использовании (~50-100MB).
   */
  async semanticSearch(
    products: SearchableProduct[],
    query: string,
    maxResults: number = 50
  ): Promise<SearchableProduct[]> {
    if (!query.trim()) {
      return products.slice(0, maxResults);
    }

    // Lazy load модели
    if (!this.embedder && !this.embeddingsLoading) {
      this.embeddingsLoading = true;
      try {
        // Динамический импорт для code splitting
        const { pipeline } = await import("@xenova/transformers");
        this.embedder = await pipeline(
          "feature-extraction",
          "Xenova/all-MiniLM-L6-v2" // Лёгкая модель (~23MB)
        );
      } catch (error) {
        console.error("Ошибка загрузки модели:", error);
        this.embeddingsLoading = false;
        // Fallback на fuzzy search
        return this.fuzzySearch(products, query, maxResults);
      }
      this.embeddingsLoading = false;
    }

    if (!this.embedder) {
      return this.fuzzySearch(products, query, maxResults);
    }

    try {
      // Получаем embedding запроса
      const embedderFn = this.embedder as (text: string, options: Record<string, unknown>) => Promise<{ data: Float32Array }>;
      const queryResult = await embedderFn(query, {
        pooling: "mean",
        normalize: true,
      });
      const queryEmbedding = Array.from(queryResult.data);

      // Создаём embeddings для товаров (батчами)
      const BATCH_SIZE = 10;
      for (let i = 0; i < products.length; i += BATCH_SIZE) {
        const batch = products.slice(i, i + BATCH_SIZE);
        for (const product of batch) {
          if (!this.productEmbeddings.has(product.id)) {
            const result = await embedderFn(product.searchText, {
              pooling: "mean",
              normalize: true,
            });
            this.productEmbeddings.set(product.id, Array.from(result.data));
          }
        }
      }

      // Cosine similarity
      const scored = products.map((p) => ({
        product: p,
        score: this.cosineSimilarity(
          queryEmbedding,
          this.productEmbeddings.get(p.id) || []
        ),
      }));

      return scored
        .sort((a, b) => b.score - a.score)
        .slice(0, maxResults)
        .map((s) => s.product);
    } catch (error) {
      console.error("Ошибка семантического поиска:", error);
      return this.fuzzySearch(products, query, maxResults);
    }
  }

  /**
   * Cosine similarity между двумя векторами.
   */
  private cosineSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length || a.length === 0) return 0;

    let dot = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }

    const denominator = Math.sqrt(normA) * Math.sqrt(normB);
    return denominator === 0 ? 0 : dot / denominator;
  }

  /**
   * Проверить загружена ли модель.
   */
  isSemanticReady(): boolean {
    return this.embedder !== null;
  }

  /**
   * Проверить загружается ли модель.
   */
  isSemanticLoading(): boolean {
    return this.embeddingsLoading;
  }
}