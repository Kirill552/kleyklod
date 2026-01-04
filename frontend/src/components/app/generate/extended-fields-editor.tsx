"use client";

import { Plus, X } from "lucide-react";

export interface CustomLine {
  id: string;
  label: string;   // "Название", "Состав", "Страна" - статичные варианты
  value: string;   // редактируемое значение
}

interface ExtendedFieldsEditorProps {
  lines: CustomLine[];
  onChange: (lines: CustomLine[]) => void;
  availableLabels?: string[];  // ["Название", "Состав", "Страна", "Бренд", "ГОСТ"]
  maxLines?: number;  // default: 5
  disabled?: boolean;
}

const DEFAULT_LABELS = ["Название", "Состав", "Страна", "Бренд", "ГОСТ"];

function generateId(): string {
  return `line-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

interface LineEditorProps {
  line: CustomLine;
  availableLabels: string[];
  usedLabels: string[];
  onUpdate: (id: string, updates: Partial<CustomLine>) => void;
  onRemove: (id: string) => void;
  disabled?: boolean;
}

function LineEditor({
  line,
  availableLabels,
  usedLabels,
  onUpdate,
  onRemove,
  disabled,
}: LineEditorProps) {
  // Доступные метки: все, кроме уже использованных (но включая текущую)
  const selectableLabels = availableLabels.filter(
    (label) => !usedLabels.includes(label) || label === line.label
  );

  return (
    <div className="flex items-center gap-2 p-3 rounded-xl border-2 bg-emerald-50 border-emerald-200 transition-all">
      {/* Выбор типа поля */}
      <select
        value={line.label}
        onChange={(e) => onUpdate(line.id, { label: e.target.value })}
        disabled={disabled}
        className="flex-shrink-0 w-28 px-2 py-1.5 text-sm font-medium bg-white border-2 border-emerald-200 rounded-lg focus:outline-none focus:border-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {selectableLabels.map((label) => (
          <option key={label} value={label}>
            {label}
          </option>
        ))}
      </select>

      {/* Значение поля */}
      <input
        type="text"
        value={line.value}
        onChange={(e) => onUpdate(line.id, { value: e.target.value })}
        placeholder="Введите значение..."
        disabled={disabled}
        className="flex-1 px-3 py-1.5 text-sm bg-white border-2 border-emerald-200 rounded-lg focus:outline-none focus:border-emerald-400 placeholder:text-warm-gray-400 disabled:opacity-50 disabled:cursor-not-allowed"
      />

      {/* Кнопка удаления */}
      <button
        type="button"
        onClick={() => onRemove(line.id)}
        disabled={disabled}
        className="flex-shrink-0 h-8 w-8 flex items-center justify-center rounded-lg bg-red-100 text-red-600 hover:bg-red-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Удалить строку"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function ExtendedFieldsEditor({
  lines,
  onChange,
  availableLabels = DEFAULT_LABELS,
  maxLines = 5,
  disabled = false,
}: ExtendedFieldsEditorProps) {
  const usedLabels = lines.map((line) => line.label);
  const canAddMore = lines.length < maxLines && lines.length < availableLabels.length;

  const handleAdd = () => {
    // Найти первую неиспользованную метку
    const unusedLabel = availableLabels.find((label) => !usedLabels.includes(label));
    if (!unusedLabel) return;

    const newLine: CustomLine = {
      id: generateId(),
      label: unusedLabel,
      value: "",
    };
    onChange([...lines, newLine]);
  };

  const handleUpdate = (id: string, updates: Partial<CustomLine>) => {
    onChange(
      lines.map((line) =>
        line.id === id ? { ...line, ...updates } : line
      )
    );
  };

  const handleRemove = (id: string) => {
    onChange(lines.filter((line) => line.id !== id));
  };

  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-warm-gray-700">
        Дополнительные строки на этикетке
      </div>

      {lines.length === 0 ? (
        <div className="p-4 rounded-xl border-2 border-dashed border-warm-gray-200 bg-warm-gray-50 text-center">
          <p className="text-sm text-warm-gray-500">
            Добавьте строки для отображения на этикетке
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {lines.map((line) => (
            <LineEditor
              key={line.id}
              line={line}
              availableLabels={availableLabels}
              usedLabels={usedLabels}
              onUpdate={handleUpdate}
              onRemove={handleRemove}
              disabled={disabled}
            />
          ))}
        </div>
      )}

      {/* Кнопка добавления */}
      {canAddMore && (
        <button
          type="button"
          onClick={handleAdd}
          disabled={disabled}
          className="w-full flex items-center justify-center gap-2 p-3 rounded-xl border-2 border-dashed border-emerald-300 bg-emerald-50 text-emerald-700 font-medium text-sm hover:bg-emerald-100 hover:border-emerald-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="h-4 w-4" />
          Добавить строку
        </button>
      )}

      {/* Подсказка о лимите */}
      <div className="text-xs text-warm-gray-500">
        {lines.length} из {Math.min(maxLines, availableLabels.length)} строк
      </div>
    </div>
  );
}
