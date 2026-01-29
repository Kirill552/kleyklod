'use client';

import { useEffect } from 'react';
import { analytics } from '@/lib/analytics';

type LandingType = 'wb' | 'chz';

interface LandingTrackerProps {
  landing: LandingType;
}

/**
 * Клиентский компонент для трекинга посещения SEO-лендингов.
 * Вставляется в Server Component для отправки события в Метрику.
 */
export function LandingTracker({ landing }: LandingTrackerProps) {
  useEffect(() => {
    if (landing === 'wb') {
      analytics.visitWbLanding();
    } else if (landing === 'chz') {
      analytics.visitChzLanding();
    }
  }, [landing]);

  return null;
}
