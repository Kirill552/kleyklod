"use client";

import { motion } from "framer-motion";
import { Check, X, Minus } from "lucide-react";

const competitors = [
  {
    name: "KleyKod",
    highlight: true,
    features: {
      price: { value: "0₽ / 50 в день", status: "best" },
      speed: { value: "5 секунд", status: "best" },
      preflight: { value: "Есть", status: "yes" },
      batchLimit: { value: "Без лимита", status: "best" },
      apiIntegration: { value: "Скоро", status: "partial" },
      transparency: { value: "100%", status: "yes" },
    },
  },
  {
    name: "wbarcode",
    highlight: false,
    features: {
      price: { value: "Скрыта", status: "no" },
      speed: { value: "Минуты", status: "partial" },
      preflight: { value: "Нет", status: "no" },
      batchLimit: { value: "500 шт", status: "partial" },
      apiIntegration: { value: "Есть", status: "yes" },
      transparency: { value: "Низкая", status: "no" },
    },
  },
  {
    name: "MarkZnak",
    highlight: false,
    features: {
      price: { value: "13-50₽/шт", status: "no" },
      speed: { value: "Неделя", status: "no" },
      preflight: { value: "Вручную", status: "partial" },
      batchLimit: { value: "По заказу", status: "partial" },
      apiIntegration: { value: "Нет", status: "no" },
      transparency: { value: "Средняя", status: "partial" },
    },
  },
];

const featureLabels: Record<string, string> = {
  price: "Цена",
  speed: "Скорость",
  preflight: "Pre-flight проверка",
  batchLimit: "Лимит партии",
  apiIntegration: "API интеграция",
  transparency: "Прозрачность",
};

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "yes":
    case "best":
      return (
        <div className={`w-5 h-5 rounded-full flex items-center justify-center ${status === "best" ? "bg-emerald-500" : "bg-emerald-100"}`}>
          <Check className={`w-3 h-3 ${status === "best" ? "text-white" : "text-emerald-600"}`} />
        </div>
      );
    case "no":
      return (
        <div className="w-5 h-5 rounded-full bg-rose-100 flex items-center justify-center">
          <X className="w-3 h-3 text-rose-500" />
        </div>
      );
    case "partial":
      return (
        <div className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center">
          <Minus className="w-3 h-3 text-amber-500" />
        </div>
      );
    default:
      return null;
  }
}

export function Comparison() {
  return (
    <section className="section" id="comparison">
      <div className="container mx-auto px-6">
        {/* Заголовок */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 bg-emerald-100 text-emerald-600 rounded-full text-sm font-medium mb-4">
            Альтернатива wbarcode и wbcon
          </span>
          <h2 className="heading-2 text-warm-gray-900 mb-4">
            Сравнение генераторов этикеток
          </h2>
          <p className="text-warm-gray-500 max-w-2xl mx-auto text-lg">
            KleyKod vs wbarcode vs MarkZnak — честное сравнение для селлеров Wildberries
          </p>
        </motion.div>

        {/* Таблица сравнения — десктоп */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="hidden md:block"
        >
          <div className="sticker overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-warm-gray-100">
                  <th className="p-4 text-left text-warm-gray-500 font-medium">
                    Параметр
                  </th>
                  {competitors.map((comp) => (
                    <th
                      key={comp.name}
                      className={`p-4 text-center ${
                        comp.highlight
                          ? "bg-emerald-50 text-emerald-700"
                          : "text-warm-gray-600"
                      }`}
                    >
                      <div className="font-bold text-lg">{comp.name}</div>
                      {comp.highlight && (
                        <span className="text-xs bg-emerald-500 text-white px-2 py-0.5 rounded-full">
                          Рекомендуем
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(featureLabels).map(([key, label], index) => (
                  <tr
                    key={key}
                    className={index % 2 === 0 ? "bg-warm-gray-50/50" : ""}
                  >
                    <td className="p-4 text-warm-gray-700 font-medium">
                      {label}
                    </td>
                    {competitors.map((comp) => {
                      const feature = comp.features[key as keyof typeof comp.features];
                      return (
                        <td
                          key={`${comp.name}-${key}`}
                          className={`p-4 text-center ${
                            comp.highlight ? "bg-emerald-50/50" : ""
                          }`}
                        >
                          <div className="flex items-center justify-center gap-2">
                            <StatusIcon status={feature.status} />
                            <span
                              className={`text-sm ${
                                feature.status === "best"
                                  ? "font-semibold text-emerald-700"
                                  : feature.status === "no"
                                  ? "text-warm-gray-400"
                                  : "text-warm-gray-600"
                              }`}
                            >
                              {feature.value}
                            </span>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Карточки сравнения — мобильные */}
        <div className="md:hidden space-y-6">
          {competitors.map((comp, index) => (
            <motion.div
              key={comp.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className={`sticker p-6 ${
                comp.highlight ? "ring-2 ring-emerald-500 ring-offset-2" : ""
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-lg text-warm-gray-800">
                  {comp.name}
                </h3>
                {comp.highlight && (
                  <span className="text-xs bg-emerald-500 text-white px-2 py-0.5 rounded-full">
                    Рекомендуем
                  </span>
                )}
              </div>
              <div className="space-y-3">
                {Object.entries(featureLabels).map(([key, label]) => {
                  const feature = comp.features[key as keyof typeof comp.features];
                  return (
                    <div
                      key={key}
                      className="flex items-center justify-between py-2 border-b border-warm-gray-100 last:border-0"
                    >
                      <span className="text-warm-gray-600 text-sm">{label}</span>
                      <div className="flex items-center gap-2">
                        <StatusIcon status={feature.status} />
                        <span
                          className={`text-sm ${
                            feature.status === "best"
                              ? "font-semibold text-emerald-700"
                              : "text-warm-gray-600"
                          }`}
                        >
                          {feature.value}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Призыв к действию */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="text-center mt-12"
        >
          <p className="text-warm-gray-600 mb-6">
            Убедитесь сами — попробуйте бесплатно уже сегодня
          </p>
          <button className="btn-primary">
            Начать бесплатно
          </button>
        </motion.div>
      </div>
    </section>
  );
}
