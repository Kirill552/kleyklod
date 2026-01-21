/**
 * Dialog компонент (shadcn/ui стиль).
 * Fullscreen вариант для выбора товаров.
 */

"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  // Закрытие по Escape
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onOpenChange(false);
      }
    };

    if (open) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Content */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        {children}
      </div>
    </div>
  );
}

interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
  fullscreen?: boolean;
}

export function DialogContent({
  children,
  className,
  fullscreen = false,
}: DialogContentProps) {
  return (
    <div
      className={cn(
        "relative bg-white rounded-xl shadow-2xl",
        "flex flex-col",
        fullscreen
          ? "w-full h-full max-w-none max-h-none m-0 rounded-none"
          : "w-full max-w-2xl max-h-[90vh]",
        className
      )}
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </div>
  );
}

interface DialogHeaderProps {
  children: React.ReactNode;
  onClose?: () => void;
  className?: string;
}

export function DialogHeader({
  children,
  onClose,
  className,
}: DialogHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between px-6 py-4 border-b border-warm-gray-200",
        className
      )}
    >
      <div className="flex-1">{children}</div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-2 rounded-lg text-warm-gray-500 hover:text-warm-gray-700 hover:bg-warm-gray-100 transition-all"
        >
          <X className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}

interface DialogTitleProps {
  children: React.ReactNode;
  className?: string;
}

export function DialogTitle({ children, className }: DialogTitleProps) {
  return (
    <h2
      className={cn("text-xl font-semibold text-warm-gray-900", className)}
    >
      {children}
    </h2>
  );
}

interface DialogFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function DialogFooter({ children, className }: DialogFooterProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between px-6 py-4 border-t border-warm-gray-200 bg-warm-gray-50",
        className
      )}
    >
      {children}
    </div>
  );
}
