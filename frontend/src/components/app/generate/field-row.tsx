"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Check, Ban, AlertTriangle, Pencil, Scissors, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLongPress } from "@/hooks/use-long-press";

/** Быстрое действие для исправления ошибки */
export type FieldRowQuickAction = "truncate" | "change_template";

export interface FieldRowProps {
  id: string;
  /** Field label ("Article", "Size", etc.) */
  label: string;
  /** Field value */
  value: string;
  /** Is field checked/enabled */
  checked: boolean;
  /** Is field disabled (plan limit) */
  disabled: boolean;
  /** Preflight error message */
  error?: string;
  /** Suggestion for fixing the error */
  errorSuggestion?: string;
  /** Is custom field (label is editable) */
  isCustom?: boolean;
  /** Callback when checkbox is toggled */
  onToggle: () => void;
  /** Callback when label changes (only for custom fields) */
  onLabelChange: (newLabel: string) => void;
  /** Callback when value changes */
  onValueChange: (newValue: string) => void;
  /** Tooltip for disabled state */
  disabledHint?: string;
  /** Callback for quick actions */
  onQuickAction?: (action: FieldRowQuickAction) => void;
  /** Show quick action buttons */
  showQuickActions?: boolean;
}

type EditingField = "label" | "value" | null;

/**
 * FieldRow component for label field editing.
 *
 * Features:
 * - Checkbox toggle for enabling/disabling field
 * - Inline editing of label (custom fields) and value
 * - Desktop: double-click to edit
 * - Mobile: long press (500ms) or tap pencil icon to edit
 * - Preflight error display
 * - Disabled state with hint
 */
export function FieldRow({
  id,
  label,
  value,
  checked,
  disabled,
  error,
  isCustom = false,
  onToggle,
  onLabelChange,
  onValueChange,
  disabledHint,
}: FieldRowProps) {
  const [editing, setEditing] = useState<EditingField>(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when editing starts
  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  // Start editing a field
  const startEditing = useCallback(
    (field: EditingField) => {
      if (disabled || !field) return;
      // Don't allow editing label for non-custom fields
      if (field === "label" && !isCustom) return;

      setEditing(field);
      setEditValue(field === "label" ? label : value);
    },
    [disabled, isCustom, label, value]
  );

  // Save edited value
  const saveEdit = useCallback(() => {
    if (!editing) return;

    const trimmedValue = editValue.trim();

    if (editing === "label") {
      if (trimmedValue && trimmedValue !== label) {
        onLabelChange(trimmedValue);
      }
    } else {
      if (trimmedValue !== value) {
        onValueChange(trimmedValue);
      }
    }

    setEditing(null);
    setEditValue("");
  }, [editing, editValue, label, value, onLabelChange, onValueChange]);

  // Cancel editing
  const cancelEdit = useCallback(() => {
    setEditing(null);
    setEditValue("");
  }, []);

  // Handle keyboard events in input
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        saveEdit();
      } else if (e.key === "Escape") {
        e.preventDefault();
        cancelEdit();
      }
    },
    [saveEdit, cancelEdit]
  );

  // Handle double-click on label area
  const handleLabelDoubleClick = useCallback(() => {
    if (isCustom && !disabled) {
      startEditing("label");
    }
  }, [isCustom, disabled, startEditing]);

  // Handle double-click on value area
  const handleValueDoubleClick = useCallback(() => {
    if (!disabled) {
      startEditing("value");
    }
  }, [disabled, startEditing]);

  // Long press handlers for label
  const labelLongPressHandlers = useLongPress({
    threshold: 500,
    onLongPress: () => startEditing("label"),
  });

  // Long press handlers for value
  const valueLongPressHandlers = useLongPress({
    threshold: 500,
    onLongPress: () => startEditing("value"),
  });

  // Mobile edit button handler
  const handleMobileEdit = useCallback(() => {
    // If custom field and value is empty, edit label first
    // Otherwise, edit value
    if (isCustom && !value) {
      startEditing("label");
    } else {
      startEditing("value");
    }
  }, [isCustom, value, startEditing]);

  // Container styles based on state
  const getContainerStyles = () => {
    if (disabled) {
      return "bg-warm-gray-100 border-warm-gray-200 opacity-60 cursor-not-allowed";
    }
    if (error && checked) {
      return "bg-red-50 border-red-400";
    }
    if (checked) {
      return "bg-emerald-50 border-emerald-200";
    }
    return "bg-white border-warm-gray-200 hover:border-warm-gray-300";
  };

  // Checkbox styles
  const getCheckboxStyles = () => {
    if (disabled) {
      return "bg-warm-gray-200 border-warm-gray-300 cursor-not-allowed";
    }
    if (checked) {
      return "bg-emerald-500 border-emerald-500 text-white";
    }
    return "bg-white border-warm-gray-300 hover:border-emerald-400";
  };

  // Label text styles
  const getLabelStyles = () => {
    if (disabled) {
      return "text-warm-gray-400";
    }
    if (checked) {
      return "text-emerald-900 font-medium";
    }
    return "text-warm-gray-600";
  };

  // Value text styles
  const getValueStyles = () => {
    if (disabled) {
      return "text-warm-gray-400";
    }
    if (checked) {
      return "text-emerald-700";
    }
    return "text-warm-gray-500";
  };

  return (
    <div
      id={`field-${id}`}
      className={cn(
        "flex items-start gap-3 p-3 rounded-xl border-2 transition-all min-h-[56px]",
        getContainerStyles()
      )}
      title={disabled ? disabledHint : undefined}
    >
      {/* Checkbox */}
      <button
        type="button"
        onClick={() => !disabled && onToggle()}
        disabled={disabled}
        className={cn(
          "flex-shrink-0 h-5 w-5 mt-0.5 rounded border-2 flex items-center justify-center transition-colors",
          "min-w-[20px] min-h-[20px]", // Touch-friendly size
          getCheckboxStyles()
        )}
        aria-label={checked ? "Disable field" : "Enable field"}
      >
        {disabled ? (
          <Ban className="h-3 w-3 text-warm-gray-400" />
        ) : checked ? (
          <Check className="h-3 w-3" />
        ) : null}
      </button>

      {/* Content area */}
      <div className="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3">
        {/* Label */}
        <div
          className={cn(
            "flex-shrink-0 sm:w-32",
            isCustom && !disabled && "cursor-pointer",
            getLabelStyles()
          )}
          onDoubleClick={handleLabelDoubleClick}
          {...(isCustom && !disabled ? labelLongPressHandlers : {})}
        >
          {editing === "label" ? (
            <input
              ref={inputRef}
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={saveEdit}
              onKeyDown={handleKeyDown}
              placeholder="Custom field"
              className={cn(
                "w-full px-2 py-1 text-sm font-medium",
                "bg-white border-2 border-emerald-400 rounded-lg",
                "focus:outline-none focus:border-emerald-500",
                "placeholder:text-warm-gray-400"
              )}
            />
          ) : (
            <span className="text-sm select-none">
              {label || (isCustom ? "Custom field" : "")}
            </span>
          )}
        </div>

        {/* Separator (desktop only) */}
        <div className="hidden sm:block w-px h-4 bg-warm-gray-200 flex-shrink-0" />

        {/* Value */}
        <div
          className={cn(
            "flex-1 min-w-0",
            !disabled && "cursor-pointer",
            getValueStyles()
          )}
          onDoubleClick={handleValueDoubleClick}
          {...(!disabled ? valueLongPressHandlers : {})}
        >
          {editing === "value" ? (
            <input
              ref={inputRef}
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={saveEdit}
              onKeyDown={handleKeyDown}
              placeholder="Enter value..."
              className={cn(
                "w-full px-2 py-1 text-sm",
                "bg-white border-2 border-emerald-400 rounded-lg",
                "focus:outline-none focus:border-emerald-500",
                "placeholder:text-warm-gray-400"
              )}
            />
          ) : (
            <span className="text-sm truncate block select-none">
              {value || (
                <span className="text-warm-gray-400 italic">
                  {disabled ? "" : "Double-click to edit"}
                </span>
              )}
            </span>
          )}
        </div>
      </div>

      {/* Mobile edit button */}
      {!disabled && !editing && (
        <button
          type="button"
          onClick={handleMobileEdit}
          className={cn(
            "flex-shrink-0 sm:hidden",
            "h-11 w-11 flex items-center justify-center",
            "rounded-lg transition-colors",
            checked
              ? "text-emerald-600 hover:bg-emerald-100"
              : "text-warm-gray-400 hover:bg-warm-gray-100"
          )}
          aria-label="Edit field"
        >
          <Pencil className="h-4 w-4" />
        </button>
      )}

      {/* Error/warning indicator */}
      {error && checked && !disabled && (
        <AlertTriangle className="flex-shrink-0 h-4 w-4 text-red-500 mt-1" />
      )}
    </div>
  );
}

/**
 * FieldRow with inline error display and quick actions.
 * Wraps FieldRow and adds error message + action buttons below.
 */
export function FieldRowWithError(props: FieldRowProps) {
  const { error, errorSuggestion, checked, disabled, onQuickAction, showQuickActions } = props;
  const showError = error && checked && !disabled;

  // Determine which quick actions to show based on error message
  const showTruncate = showQuickActions && error?.toLowerCase().includes("текст");
  const showChangeTemplate = showQuickActions && error?.toLowerCase().includes("полей");

  return (
    <div className="space-y-1">
      <FieldRow {...props} />
      {showError && (
        <div className="ml-8 space-y-2">
          {/* Error message */}
          <div className="flex items-start gap-2 text-xs text-red-600">
            <AlertTriangle className="h-3 w-3 flex-shrink-0 mt-0.5" />
            <div>
              <span>{error}</span>
              {errorSuggestion && (
                <span className="text-red-500 ml-1">{errorSuggestion}</span>
              )}
            </div>
          </div>
          {/* Quick action buttons */}
          {(showTruncate || showChangeTemplate) && onQuickAction && (
            <div className="flex gap-2 pl-5">
              {showTruncate && (
                <button
                  type="button"
                  onClick={() => onQuickAction("truncate")}
                  className={cn(
                    "inline-flex items-center gap-1 px-2 py-1 text-xs font-medium",
                    "bg-white border border-red-200 rounded-lg text-red-700",
                    "hover:bg-red-50 hover:border-red-300 transition-colors"
                  )}
                >
                  <Scissors className="h-3 w-3" />
                  Сократить
                </button>
              )}
              {showChangeTemplate && (
                <button
                  type="button"
                  onClick={() => onQuickAction("change_template")}
                  className={cn(
                    "inline-flex items-center gap-1 px-2 py-1 text-xs font-medium",
                    "bg-white border border-red-200 rounded-lg text-red-700",
                    "hover:bg-red-50 hover:border-red-300 transition-colors"
                  )}
                >
                  <ArrowRight className="h-3 w-3" />
                  Extended
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
