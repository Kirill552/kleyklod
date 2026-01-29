'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { generateWbOnly, WbLabelItem, GenerateChzResponse } from '@/lib/api';
import { analytics } from '@/lib/analytics';
import { Download, Plus, Trash2 } from 'lucide-react';

type LabelSize = '58x40' | '58x30';

export function WbOnlyForm() {
  const [items, setItems] = useState<WbLabelItem[]>([{ barcode: '' }]);
  const [labelSize, setLabelSize] = useState<LabelSize>('58x40');
  const [showFields, setShowFields] = useState({
    barcode: true,
    name: false,
    article: false,
    size: false,
    color: false,
    brand: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateChzResponse | null>(null);

  const addItem = () => {
    setItems([...items, { barcode: '' }]);
  };

  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const updateItem = (index: number, field: keyof WbLabelItem, value: string) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], [field]: value };
    setItems(newItems);
  };

  const handleGenerate = async () => {
    const validItems = items.filter((item) => item.barcode.trim());
    if (validItems.length === 0) {
      setError('Добавьте хотя бы один товар с штрихкодом');
      return;
    }

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
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1. Данные товаров</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {items.map((item, index) => (
              <div key={index} className="flex gap-3 items-start">
                <div className="flex-1 grid grid-cols-2 gap-3">
                  <Input
                    placeholder="Штрихкод *"
                    value={item.barcode}
                    onChange={(e) => updateItem(index, 'barcode', e.target.value)}
                  />
                  <Input
                    placeholder="Артикул"
                    value={item.article || ''}
                    onChange={(e) => updateItem(index, 'article', e.target.value)}
                  />
                </div>
                {items.length > 1 && (
                  <Button variant="ghost" size="sm" onClick={() => removeItem(index)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
            <Button variant="secondary" onClick={addItem}>
              <Plus className="h-4 w-4 mr-2" />
              Добавить товар
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">2. Размер этикетки</CardTitle>
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

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">3. Поля на этикетке</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {[
              { key: 'barcode', label: 'Штрихкод', required: true },
              { key: 'name', label: 'Название' },
              { key: 'article', label: 'Артикул' },
              { key: 'size', label: 'Размер' },
              { key: 'color', label: 'Цвет' },
              { key: 'brand', label: 'Бренд' },
            ].map(({ key, label, required }) => (
              <label key={key} className="flex items-center gap-2 cursor-pointer">
                <Checkbox
                  checked={showFields[key as keyof typeof showFields]}
                  onChange={(e) =>
                    setShowFields({ ...showFields, [key]: e.target.checked })
                  }
                  disabled={required}
                />
                <span>{label}</span>
                {required && <span className="text-xs text-gray-400">(обязательно)</span>}
              </label>
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
        {loading ? 'Генерация...' : 'Создать этикетки'}
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
                className="inline-flex items-center gap-2 bg-emerald-600 text-white px-6 py-3 rounded-xl hover:bg-emerald-700 transition-colors"
              >
                <Download className="h-5 w-5" />
                Скачать PDF
              </a>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
