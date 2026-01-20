"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Простой Select компонент, совместимый с shadcn/ui API.
 * Использует нативный <select> для простоты.
 */

interface SelectContextValue {
  value?: string;
  onValueChange?: (value: string) => void;
}

const SelectContext = React.createContext<SelectContextValue>({});

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
}

export function Select({ value, onValueChange, children }: SelectProps) {
  return (
    <SelectContext.Provider value={{ value, onValueChange }}>
      {children}
    </SelectContext.Provider>
  );
}

interface SelectTriggerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const SelectTrigger = React.forwardRef<HTMLDivElement, SelectTriggerProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-lg border border-warm-gray-300 bg-white px-3 py-2 text-sm",
          "focus-within:outline-none focus-within:ring-2 focus-within:ring-emerald-500 focus-within:border-emerald-500",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
SelectTrigger.displayName = "SelectTrigger";

export function SelectValue({ placeholder }: { placeholder?: string }) {
  const { value } = React.useContext(SelectContext);
  return <span className="text-warm-gray-700">{value || placeholder}</span>;
}

interface SelectContentProps {
  children: React.ReactNode;
}

export function SelectContent({ children }: SelectContentProps) {
  const { onValueChange } = React.useContext(SelectContext);

  return (
    <select
      onChange={(e) => onValueChange?.(e.target.value)}
      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
    >
      {children}
    </select>
  );
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
}

export function SelectItem({ value, children }: SelectItemProps) {
  return <option value={value}>{children}</option>;
}
