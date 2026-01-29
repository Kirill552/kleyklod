'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { generateWbOnly, WbLabelItem, GenerateChzResponse } from '@/lib/api';
import { analytics } from '@/lib/analytics';
import { Download, Plus, Trash2, Upload, FileSpreadsheet, X } from 'lucide-react';
import * as XLSX from 'xlsx';

type LabelSize = '58x40' | '58x30';

// Максимальная длина текста для полей (символов)
const MAX_FIELD_LENGTH = {
  name: 50,
  article: 30,
  size: 15,
  color: 20,
  brand: 25,
};

export function WbOnlyForm() {
  const [items, setItems] = useState<WbLabelItem[]>([{ barcode: '', quantity: 1 }]);
  const [labelSize, setLabelSize] = useState<LabelSize>('58x40');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateChzResponse | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  // Парсинг Excel файла
  const parseExcelFile = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = e.target?.result;
        const workbook = XLSX.read(data, { type: 'binary' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json<Record<string, unknown>>(worksheet);

        if (jsonData.length === 0) {
          setError('Файл пустой или не содержит данных');
          return;
        }

        // Маппинг колонок (поддержка разных названий)
        const columnMappings: Record<string, string[]> = {
          barcode: ['barcode', 'штрихкод', 'баркод', 'ean', 'код', 'штрих-код'],
          article: ['article', 'артикул', 'арт', 'sku', 'артикл'],
          name: ['name', 'название', 'наименование', 'товар', 'имя'],
          size: ['size', 'размер', 'разм'],
          color: ['color', 'цвет'],
          brand: ['brand', 'бренд', 'марка', 'производитель'],
          quantity: ['quantity', 'количество', 'кол-во', 'колво', 'кол', 'qty'],
        };

        const findColumn = (row: Record<string, unknown>, mappings: string[]): string | undefined => {
          const keys = Object.keys(row).map((k) => k.toLowerCase().trim());
          for (const mapping of mappings) {
            const idx = keys.findIndex((k) => k.includes(mapping));
            if (idx !== -1) {
              const originalKey = Object.keys(row)[idx];
              const value = row[originalKey];
              return value !== undefined && value !== null ? String(value).trim() : undefined;
            }
          }
          return undefined;
        };

        // Парсим строки
        const parsedItems: WbLabelItem[] = jsonData
          .map((row) => {
            const barcode = findColumn(row, columnMappings.barcode) || '';
            const quantityStr = findColumn(row, columnMappings.quantity);
            const quantity = quantityStr ? parseInt(quantityStr) || 1 : 1;

            return {
              barcode,
              article: findColumn(row, columnMappings.article),
              name: findColumn(row, columnMappings.name),
              size: findColumn(row, columnMappings.size),
              color: findColumn(row, columnMappings.color),
              brand: findColumn(row, columnMappings.brand),
              quantity,
            };
          })
          .filter((item) => item.barcode); // Только с баркодом

        if (parsedItems.length === 0) {
          setError('Не найдено товаров с штрихкодом. Проверьте что в файле есть колонка "Штрихкод" или "Barcode".');
          return;
        }

        setItems(parsedItems);
        setFileName(file.name);
        setError(null);
        setResult(null);
      } catch {
        setError('Ошибка чтения файла. Убедитесь что это корректный Excel файл.');
      }
    };
    reader.readAsBinaryString(file);
  }, []);

  // Drag & Drop handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const file = e.dataTransfer.files?.[0];
      if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
        parseExcelFile(file);
      } else {
        setError('Загрузите файл в формате Excel (.xlsx или .xls)');
      }
    },
    [parseExcelFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        parseExcelFile(file);
      }
    },
    [parseExcelFile]
  );

  const clearFile = () => {
    setFileName(null);
    setItems([{ barcode: '', quantity: 1 }]);
    setResult(null);
  };

  const addItem = () => {
    setItems([...items, { barcode: '', quantity: 1 }]);
  };

  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const updateItem = (index: number, field: keyof WbLabelItem, value: string | number) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], [field]: value };
    setItems(newItems);
  };

  // Валидация длины полей
  const validateItems = (validItems: WbLabelItem[]): string | null => {
    for (let i = 0; i < validItems.length; i++) {
      const item = validItems[i];
      const rowNum = i + 1;

      if (item.name && item.name.length > MAX_FIELD_LENGTH.name) {
        return `Строка ${rowNum}: название слишком длинное (${item.name.length} символов, максимум ${MAX_FIELD_LENGTH.name})`;
      }
      if (item.article && item.article.length > MAX_FIELD_LENGTH.article) {
        return `Строка ${rowNum}: артикул слишком длинный (${item.article.length} символов, максимум ${MAX_FIELD_LENGTH.article})`;
      }
      if (item.size && item.size.length > MAX_FIELD_LENGTH.size) {
        return `Строка ${rowNum}: размер слишком длинный (${item.size.length} символов, максимум ${MAX_FIELD_LENGTH.size})`;
      }
      if (item.color && item.color.length > MAX_FIELD_LENGTH.color) {
        return `Строка ${rowNum}: цвет слишком длинный (${item.color.length} символов, максимум ${MAX_FIELD_LENGTH.color})`;
      }
      if (item.brand && item.brand.length > MAX_FIELD_LENGTH.brand) {
        return `Строка ${rowNum}: бренд слишком длинный (${item.brand.length} символов, максимум ${MAX_FIELD_LENGTH.brand})`;
      }
    }
    return null;
  };

  const handleGenerate = async () => {
    const validItems = items.filter((item) => item.barcode.trim());
    if (validItems.length === 0) {
      setError('Добавьте хотя бы один товар с штрихкодом');
      return;
    }

    // Валидация длины
    const validationError = validateItems(validItems);
    if (validationError) {
      setError(validationError);
      return;
    }

    // Автоматически определяем какие поля показывать
    const hasAnyField = (field: keyof WbLabelItem) =>
      validItems.some((item) => item[field] && String(item[field]).trim());

    const showFields = {
      barcode: true,
      name: hasAnyField('name'),
      article: hasAnyField('article'),
      size: hasAnyField('size'),
      color: hasAnyField('color'),
      brand: hasAnyField('brand'),
    };

    setLoading(true);
    setError(null);
    analytics.wbOnlyStart();

    try {
      const response = await generateWbOnly({
        items: validItems,
        labelSize,
        showFields,
      });
      setResult(response);
      analytics.wbOnlyComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка');
      analytics.generationError();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Загрузка Excel */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1. Загрузите Excel или введите вручную</CardTitle>
        </CardHeader>
        <CardContent>
          {!fileName ? (
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
                ${dragActive ? 'border-emerald-500 bg-emerald-50' : 'border-gray-300 hover:border-emerald-400'}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('excel-input')?.click()}
            >
              <input
                id="excel-input"
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileInput}
                className="hidden"
              />
              <Upload className="h-10 w-10 mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600 mb-1">Перетащите Excel файл сюда</p>
              <p className="text-sm text-gray-400">или нажмите для выбора</p>
              <p className="text-xs text-gray-400 mt-2">
                Колонки: Штрихкод, Артикул, Название, Размер, Цвет, Бренд, Количество
              </p>
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-xl">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="h-8 w-8 text-emerald-600" />
                <div>
                  <p className="font-medium text-emerald-800">{fileName}</p>
                  <p className="text-sm text-emerald-600">{items.length} товаров загружено</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={clearFile}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Список товаров */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">2. Данные товаров</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {items.map((item, index) => (
              <div key={index} className="p-4 border rounded-lg bg-gray-50 space-y-3">
                <div className="flex gap-3 items-start">
                  <div className="flex-1 grid grid-cols-3 gap-3">
                    <Input
                      placeholder="Штрихкод *"
                      value={item.barcode}
                      onChange={(e) => updateItem(index, 'barcode', e.target.value)}
                    />
                    <Input
                      placeholder="Артикул"
                      value={item.article || ''}
                      onChange={(e) => updateItem(index, 'article', e.target.value)}
                      maxLength={MAX_FIELD_LENGTH.article}
                    />
                    <Input
                      type="number"
                      min={1}
                      max={10000}
                      placeholder="Кол-во"
                      value={item.quantity || 1}
                      onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                    />
                  </div>
                  {items.length > 1 && (
                    <Button variant="ghost" size="sm" onClick={() => removeItem(index)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
                <div className="grid grid-cols-4 gap-3">
                  <Input
                    placeholder="Название"
                    value={item.name || ''}
                    onChange={(e) => updateItem(index, 'name', e.target.value)}
                    maxLength={MAX_FIELD_LENGTH.name}
                  />
                  <Input
                    placeholder="Размер"
                    value={item.size || ''}
                    onChange={(e) => updateItem(index, 'size', e.target.value)}
                    maxLength={MAX_FIELD_LENGTH.size}
                  />
                  <Input
                    placeholder="Цвет"
                    value={item.color || ''}
                    onChange={(e) => updateItem(index, 'color', e.target.value)}
                    maxLength={MAX_FIELD_LENGTH.color}
                  />
                  <Input
                    placeholder="Бренд"
                    value={item.brand || ''}
                    onChange={(e) => updateItem(index, 'brand', e.target.value)}
                    maxLength={MAX_FIELD_LENGTH.brand}
                  />
                </div>
              </div>
            ))}
          </div>
          <Button variant="secondary" onClick={addItem} className="mt-4">
            <Plus className="h-4 w-4 mr-2" />
            Добавить товар
          </Button>
        </CardContent>
      </Card>

      {/* Размер этикетки */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">3. Размер этикетки</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            {(['58x40', '58x30'] as const).map((size) => (
              <button
                key={size}
                onClick={() => setLabelSize(size)}
                className={`p-3 rounded-xl border-2 transition-colors text-center
                  ${labelSize === size
                    ? 'border-emerald-500 bg-emerald-50'
                    : 'border-gray-200 hover:border-emerald-300'}`}
              >
                <div className="font-medium">{size.replace('x', ' x ')} мм</div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
          {error}
        </div>
      )}

      <Button
        onClick={handleGenerate}
        disabled={loading || !items.some((i) => i.barcode.trim())}
        className="w-full"
        size="lg"
      >
        {loading ? 'Генерация...' : `Создать этикетки (${items.filter((i) => i.barcode.trim()).reduce((sum, i) => sum + (i.quantity || 1), 0)} шт)`}
      </Button>

      {result && (
        <Card className="bg-emerald-50 border-emerald-200">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-emerald-700 mb-2">
                Готово! {result.labels_count} этикеток
              </div>
              <a
                href={result.download_url}
                download
                onClick={() => analytics.downloadResult()}
                className="inline-flex items-center gap-2 bg-emerald-600 text-white px-6 py-3 rounded-xl hover:bg-emerald-700 transition-colors"
              >
                <Download className="h-5 w-5" />
                Скачать PDF
              </a>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upsell баннер */}
      {result && (
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-300 rounded-xl p-5">
          <p className="text-purple-900 font-semibold text-lg">
            🎯 Добавьте Честный Знак на этикетку!
          </p>
          <p className="text-sm text-purple-700 mt-2 mb-4">
            Объедините штрихкод WB и DataMatrix ЧЗ в одну наклейку — клеить в 2 раза быстрее, расходников в 2 раза меньше.
          </p>
          <a
            href="/app/generate?mode=combined"
            onClick={() => analytics.upsellToCombined()}
            className="inline-flex items-center gap-2 bg-purple-600 text-white px-5 py-2.5 rounded-lg hover:bg-purple-700 transition-colors font-medium"
          >
            Попробовать объединение →
          </a>
        </div>
      )}
    </div>
  );
}
