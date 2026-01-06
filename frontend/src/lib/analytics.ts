/**
 * Яндекс Метрика - трекинг целей
 *
 * Цели настроены в кабинете Метрики (ID: 106055873)
 */

// Типы для window.ym
declare global {
  interface Window {
    ym?: (id: number, action: string, goal?: string) => void;
  }
}

// ID счётчика из env
const METRIKA_ID = process.env.NEXT_PUBLIC_METRIKA_ID
  ? parseInt(process.env.NEXT_PUBLIC_METRIKA_ID, 10)
  : null;

/**
 * Отправить достижение цели в Яндекс Метрику
 */
export function trackGoal(goal: string) {
  if (typeof window !== "undefined" && window.ym && METRIKA_ID) {
    window.ym(METRIKA_ID, "reachGoal", goal);
    // Debug в development
    if (process.env.NODE_ENV === "development") {
      console.log(`[Metrika] Goal: ${goal}`);
    }
  }
}

/**
 * Готовые цели для трекинга
 *
 * Воронка конверсии:
 * registration → file_upload → generation_start → generation_complete → download_result
 *                                    ↓
 *                            generation_error
 *
 * Монетизация:
 * pricing_view → plan_click → checkout_start → payment_success
 */
export const analytics = {
  // === Регистрация и авторизация ===
  registration: () => trackGoal("registration"),

  // === Генерация этикеток ===
  fileUpload: () => trackGoal("file_upload"),
  generationStart: () => trackGoal("generation_start"),
  generationComplete: () => trackGoal("generation_complete"),
  generationError: () => trackGoal("generation_error"),
  downloadResult: () => trackGoal("download_result"),
  downloadExample: () => trackGoal("download_example"),

  // === Монетизация ===
  pricingView: () => trackGoal("pricing_view"),
  planClick: () => trackGoal("plan_click"),
  checkoutStart: () => trackGoal("checkout_start"),
  paymentSuccess: () => trackGoal("payment_success"),

  // === Engagement ===
  productSaved: () => trackGoal("product_saved"),
  botClick: () => trackGoal("bot_click"),
};
