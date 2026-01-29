'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { analytics } from '@/lib/analytics';

type Mode = 'wb' | 'chz' | 'combined';

interface GeneratorTabsProps {
  defaultMode?: Mode;
  children: (mode: Mode) => React.ReactNode;
}

const TABS: { id: Mode; label: string; description: string }[] = [
  { id: 'wb', label: 'Только WB', description: 'Генерация этикеток Wildberries' },
  { id: 'chz', label: 'Только ЧЗ', description: 'Генерация этикеток Честного знака' },
  { id: 'combined', label: 'Объединение', description: 'WB + ЧЗ в одной наклейке' },
];

export function GeneratorTabs({ defaultMode = 'combined', children }: GeneratorTabsProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [mode, setMode] = useState<Mode>(defaultMode);

  // Инициализация из URL
  useEffect(() => {
    const urlMode = searchParams.get('mode') as Mode | null;
    if (urlMode && ['wb', 'chz', 'combined'].includes(urlMode)) {
      setMode(urlMode);
    }
  }, [searchParams]);

  const handleModeChange = (newMode: Mode) => {
    // Апсейл: переключение с бесплатного режима на платный
    if (newMode === 'combined' && (mode === 'wb' || mode === 'chz')) {
      analytics.upsellToCombined();
    }
    setMode(newMode);
    const params = new URLSearchParams(searchParams.toString());
    params.set('mode', newMode);
    router.push(`?${params.toString()}`, { scroll: false });
  };

  return (
    <div className="space-y-6">
      {/* Табы */}
      <div className="flex gap-2 p-1 bg-gray-100 rounded-xl">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleModeChange(tab.id)}
            className={`flex-1 px-4 py-3 rounded-lg text-sm font-medium transition-colors
              ${mode === tab.id
                ? 'bg-white text-emerald-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'}`}
          >
            <div>{tab.label}</div>
            <div className={`text-xs mt-0.5 ${mode === tab.id ? 'text-emerald-600' : 'text-gray-400'}`}>
              {tab.description}
            </div>
          </button>
        ))}
      </div>

      {/* Бейдж для бесплатных режимов */}
      {(mode === 'wb' || mode === 'chz') && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2 text-center">
          <span className="text-emerald-700 font-medium">Бесплатно и без ограничений</span>
        </div>
      )}

      {/* Контент */}
      {children(mode)}
    </div>
  );
}
