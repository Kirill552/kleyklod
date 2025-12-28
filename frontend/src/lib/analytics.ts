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

export function trackGoal(goal: string) {
  if (typeof window !== 'undefined' && window.ym && METRIKA_ID) {
    window.ym(METRIKA_ID, 'reachGoal', goal);
  }
}

// Готовые цели
export const analytics = {
  openPricing: () => trackGoal('open_pricing'),
  clickBuyPro: () => trackGoal('click_buy_pro'),
  paymentSuccess: () => trackGoal('payment_success'),
  feedbackSubmit: () => trackGoal('feedback_submit'),
  generateLabels: () => trackGoal('generate_labels'),
};
