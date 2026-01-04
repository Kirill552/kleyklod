"use client";

import { Check } from "lucide-react";

export interface FieldConfig {
  id: string;
  label: string;
  preview: string | null;
  enabled: boolean;
}

interface FieldToggleProps {
  field: FieldConfig;
  onToggle: (id: string) => void;
}

function FieldToggle({ field, onToggle }: FieldToggleProps) {
  return (
    <div
      className={`flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${
        field.enabled
          ? "bg-emerald-50 border-emerald-200"
          : "bg-warm-gray-50 border-warm-gray-200"
      }`}
    >
      <button
        type="button"
        onClick={() => onToggle(field.id)}
        className={`h-5 w-5 rounded border-2 flex items-center justify-center transition-colors ${
          field.enabled
            ? "bg-emerald-500 border-emerald-500 text-white"
            : "bg-white border-warm-gray-300 hover:border-emerald-400"
        }`}
      >
        {field.enabled && <Check className="h-3 w-3" />}
      </button>

      <div className="flex-1">
        <div className={`font-medium text-sm ${field.enabled ? "text-emerald-900" : "text-warm-gray-600"}`}>
          {field.label}
        </div>
        {field.preview && (
          <div className="text-xs text-warm-gray-500 truncate">{field.preview}</div>
        )}
      </div>
    </div>
  );
}

interface FieldOrderEditorProps {
  fields: FieldConfig[];
  onChange: (fields: FieldConfig[]) => void;
}

export function FieldOrderEditor({ fields, onChange }: FieldOrderEditorProps) {
  const handleToggle = (id: string) => {
    onChange(
      fields.map((f) => (f.id === id ? { ...f, enabled: !f.enabled } : f))
    );
  };

  return (
    <div className="space-y-2">
      <div className="text-sm font-medium text-warm-gray-700 mb-2">
        Какие поля показывать на этикетке
      </div>
      <div className="space-y-2">
        {fields.map((field) => (
          <FieldToggle
            key={field.id}
            field={field}
            onToggle={handleToggle}
          />
        ))}
      </div>
    </div>
  );
}
