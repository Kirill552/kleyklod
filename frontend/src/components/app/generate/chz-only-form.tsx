'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { generateChzOnly, GenerateChzResponse } from '@/lib/api';
import { analytics } from '@/lib/analytics';
import { Download, Upload, FileText, AlertCircle } from 'lucide-react';

type LabelSize = '58x40';

interface ChzOnlyFormProps {
  onSuccess?: (result: GenerateChzResponse) => void;
}

export function ChzOnlyForm({ onSuccess }: ChzOnlyFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [labelSize, setLabelSize] = useState<LabelSize>('58x40');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateChzResponse | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
      setResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
  });

  const handleGenerate = async () => {
    if (!file) {
      setError('Загрузите CSV файл');
      return;
    }

    setLoading(true);
    setError(null);
    analytics.chzOnlyStart();

    try {
      const response = await generateChzOnly({
        csvFile: file,
        labelSize,
      });
      setResult(response);
      analytics.chzOnlyComplete();
      onSuccess?.(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка');
      analytics.generationError();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Предупреждение про Excel */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
        <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-amber-800">
          <p className="font-medium">Важно!</p>
          <p>Не открывайте CSV в Excel — структура кодов испортится. Скачайте файл из ЛК Честного знака и загрузите сюда напрямую.</p>
        </div>
      </div>

      {/* Dropzone */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1. Загрузите CSV с кодами</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
              ${isDragActive ? 'border-emerald-500 bg-emerald-50' : 'border-gray-300 hover:border-emerald-400'}
              ${file ? 'bg-emerald-50 border-emerald-500' : ''}`}
          >
            <input {...getInputProps()} />
            {file ? (
              <div className="flex items-center justify-center gap-2 text-emerald-700">
                <FileText className="h-5 w-5" />
                <span>{file.name}</span>
              </div>
            ) : (
              <div className="text-gray-500">
                <Upload className="h-8 w-8 mx-auto mb-2" />
                <p>Перетащите CSV файл сюда или нажмите для выбора</p>
                <p className="text-sm mt-1">Только .csv файлы из ЛК Честного знака</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Размер этикетки (фиксированный) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">2. Размер этикетки</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 rounded-xl border-2 border-emerald-500 bg-emerald-50">
            <div className="font-medium">58 × 40 мм</div>
            <div className="text-sm text-gray-500">DataMatrix 22×22 мм по ГОСТу</div>
          </div>
        </CardContent>
      </Card>

      {/* Ошибка */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Кнопка генерации */}
      <Button
        onClick={handleGenerate}
        disabled={!file || loading}
        className="w-full"
        size="lg"
      >
        {loading ? 'Генерация...' : 'Создать этикетки'}
      </Button>

      {/* Результат */}
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

      {/* Upsell баннер */}
      {result && (
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-4">
          <p className="text-purple-800 font-medium">
            А хотите объединить этикетки WB и Честного знака в одну наклейку?
          </p>
          <p className="text-sm text-purple-600 mt-1">
            Переключитесь на вкладку «Объединение» — это экономит время и материал.
          </p>
        </div>
      )}
    </div>
  );
}
