"use client";

import { useCallback, useRef } from "react";

interface LongPressOptions {
  /** Duration in ms before long press triggers (default: 500) */
  threshold?: number;
  /** Callback when long press is detected */
  onLongPress: () => void;
  /** Optional callback for short press/click */
  onClick?: () => void;
}

interface LongPressHandlers {
  onMouseDown: (e: React.MouseEvent) => void;
  onMouseUp: (e: React.MouseEvent) => void;
  onMouseLeave: (e: React.MouseEvent) => void;
  onTouchStart: (e: React.TouchEvent) => void;
  onTouchEnd: () => void;
  onTouchMove: (e: React.TouchEvent) => void;
}

/**
 * Hook for detecting long press gestures on touch/mouse devices.
 * Returns event handlers to attach to the target element.
 */
export function useLongPress({
  threshold = 500,
  onLongPress,
  onClick,
}: LongPressOptions): LongPressHandlers {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isLongPressRef = useRef(false);
  const startPosRef = useRef<{ x: number; y: number } | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startPressTimer = useCallback(() => {
    isLongPressRef.current = false;
    timerRef.current = setTimeout(() => {
      isLongPressRef.current = true;
      onLongPress();
    }, threshold);
  }, [threshold, onLongPress]);

  // Mouse handlers
  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // Only respond to left mouse button
      if (e.button !== 0) return;
      startPressTimer();
    },
    [startPressTimer]
  );

  const onMouseUp = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      clearTimer();
      // If it wasn't a long press and we have an onClick handler
      if (!isLongPressRef.current && onClick) {
        onClick();
      }
    },
    [clearTimer, onClick]
  );

  const onMouseLeave = useCallback(() => {
    clearTimer();
  }, [clearTimer]);

  // Touch handlers
  const onTouchStart = useCallback(
    (e: React.TouchEvent) => {
      const touch = e.touches[0];
      startPosRef.current = { x: touch.clientX, y: touch.clientY };
      startPressTimer();
    },
    [startPressTimer]
  );

  const onTouchEnd = useCallback(() => {
    clearTimer();
    // If it wasn't a long press and we have an onClick handler
    if (!isLongPressRef.current && onClick) {
      onClick();
    }
    startPosRef.current = null;
  }, [clearTimer, onClick]);

  const onTouchMove = useCallback(
    (e: React.TouchEvent) => {
      // Cancel long press if user moves finger more than 10px
      if (startPosRef.current && e.touches[0]) {
        const touch = e.touches[0];
        const moveThreshold = 10;
        const deltaX = Math.abs(touch.clientX - startPosRef.current.x);
        const deltaY = Math.abs(touch.clientY - startPosRef.current.y);

        if (deltaX > moveThreshold || deltaY > moveThreshold) {
          clearTimer();
        }
      }
    },
    [clearTimer]
  );

  return {
    onMouseDown,
    onMouseUp,
    onMouseLeave,
    onTouchStart,
    onTouchEnd,
    onTouchMove,
  };
}
