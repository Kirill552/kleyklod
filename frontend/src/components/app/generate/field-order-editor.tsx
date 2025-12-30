"use client";

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Check } from "lucide-react";

export interface FieldConfig {
  id: string;
  label: string;
  preview: string | null;
  enabled: boolean;
}

interface SortableFieldProps {
  field: FieldConfig;
  onToggle: (id: string) => void;
}

function SortableField({ field, onToggle }: SortableFieldProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: field.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${
        field.enabled
          ? "bg-emerald-50 border-emerald-200"
          : "bg-warm-gray-50 border-warm-gray-200"
      } ${isDragging ? "shadow-lg ring-2 ring-emerald-400" : ""}`}
    >
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing text-emerald-400 hover:text-emerald-600"
        type="button"
      >
        <GripVertical className="h-5 w-5" />
      </button>

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
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = fields.findIndex((f) => f.id === active.id);
      const newIndex = fields.findIndex((f) => f.id === over.id);
      onChange(arrayMove(fields, oldIndex, newIndex));
    }
  };

  const handleToggle = (id: string) => {
    onChange(
      fields.map((f) => (f.id === id ? { ...f, enabled: !f.enabled } : f))
    );
  };

  return (
    <div className="space-y-2">
      <div className="text-sm font-medium text-warm-gray-700 mb-2">
        Какие поля показывать (перетащите для изменения порядка)
      </div>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={fields} strategy={verticalListSortingStrategy}>
          <div className="space-y-2">
            {fields.map((field) => (
              <SortableField
                key={field.id}
                field={field}
                onToggle={handleToggle}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
}
