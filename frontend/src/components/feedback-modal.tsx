"use client";

/**
 * Модальное окно для сбора обратной связи.
 *
 * Показывается после 3-й успешной генерации этикеток.
 */

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { X, Loader2, MessageSquare } from "lucide-react";

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (text: string) => Promise<void>;
}

export function FeedbackModal({ isOpen, onClose, onSubmit }: FeedbackModalProps) {
  const [text, setText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Фокус на textarea при открытии
  useEffect(() => {
    if (isOpen && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isOpen]);

  // Закрытие по Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Блокировка скролла при открытом модале
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const handleSubmit = async () => {
    if (!text.trim()) {
      setError("Введите ваш отзыв");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit(text.trim());
      setText("");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка отправки");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = () => {
    setText("");
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleSkip}
      />

      {/* Modal */}
      <div
        className={cn(
          "relative z-10 w-full max-w-md mx-4",
          "bg-white rounded-xl shadow-[6px_6px_0px_#374151]",
          "animate-in fade-in-0 zoom-in-95 duration-200",
          "border-2 border-warm-gray-300"
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <MessageSquare className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-warm-gray-900">
                Вы сгенерировали уже 3 партии этикеток!
              </h2>
              <p className="text-sm text-warm-gray-600 mt-1">
                Что бы вы хотели улучшить в сервисе?
              </p>
            </div>
          </div>
          <button
            onClick={handleSkip}
            className="p-1 text-warm-gray-400 hover:text-warm-gray-600 transition-colors"
            aria-label="Закрыть"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 pb-4">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ваши идеи и пожелания..."
            className={cn(
              "w-full h-32 p-4 rounded-xl resize-none",
              "border-2 border-warm-gray-300",
              "focus:outline-none focus:border-2 focus:border-emerald-500",
              "text-warm-gray-900 placeholder:text-warm-gray-400"
            )}
            disabled={isSubmitting}
          />

          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 pt-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSkip}
            disabled={isSubmitting}
          >
            Пропустить
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Отправка...
              </>
            ) : (
              "Отправить"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
