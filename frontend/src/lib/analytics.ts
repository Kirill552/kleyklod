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
 * Воронка конверсии (3 режима):
 * registration → file_upload → [режим]_start → [режим]_complete → download_result
 *                                    ↓
 *                            generation_error
 *
 * Режимы:
 * - wb_only: бесплатные этикетки WB
 * - chz_only: бесплатные этикетки ЧЗ
 * - combined: объединение WB+ЧЗ (платный)
 *
 * Апсейл:
 * [бесплатный режим] → upsell_to_combined → combined_start
 *
 * Монетизация:
 * pricing_view → plan_click → checkout_start → payment_success
 */
export const analytics = {
  // === Регистрация и авторизация ===
  registration: () => trackGoal("registration"),

  // === Генерация этикеток (общие, legacy) ===
  fileUpload: () => trackGoal("file_upload"),
  generationStart: () => trackGoal("generation_start"),
  generationComplete: () => trackGoal("generation_complete"),
  generationError: () => trackGoal("generation_error"),
  downloadResult: () => trackGoal("download_result"),
  downloadExample: () => trackGoal("download_example"),

  // === Режим "Только WB" (бесплатно) ===
  wbOnlyStart: () => trackGoal("wb_only_start"),
  wbOnlyComplete: () => trackGoal("wb_only_complete"),

  // === Режим "Только ЧЗ" (бесплатно) ===
  chzOnlyStart: () => trackGoal("chz_only_start"),
  chzOnlyComplete: () => trackGoal("chz_only_complete"),

  // === Режим "Объединение" (платный) ===
  combinedStart: () => trackGoal("combined_start"),
  combinedComplete: () => trackGoal("combined_complete"),

  // === Апсейл: переключение на платный режим ===
  upsellToCombined: () => trackGoal("upsell_to_combined"),

  // === Посещение SEO-лендингов ===
  visitWbLanding: () => trackGoal("visit_wb_landing"),
  visitChzLanding: () => trackGoal("visit_chz_landing"),

  // === Монетизация ===
  pricingView: () => trackGoal("pricing_view"),
  planClick: () => trackGoal("plan_click"),
  checkoutStart: () => trackGoal("checkout_start"),
  paymentSuccess: () => trackGoal("payment_success"),

  // === Engagement ===
  productSaved: () => trackGoal("product_saved"),
  botClick: () => trackGoal("bot_click"),
};
