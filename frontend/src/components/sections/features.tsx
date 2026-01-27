"use client";

import { motion } from "framer-motion";
import { Link2, Shield, Printer, Database } from "lucide-react";

const features = [
  {
    icon: Link2,
    title: "Автоматический матчинг",
    description: "Сопоставляем товары и коды по штрихкоду GTIN — не нужно вручную искать соответствия",
  },
  {
    icon: Shield,
    title: "Проверка DataMatrix",
    description: "Preflight-проверка перед печатью — 99.9% кодов проходят сканер на приёмке WB",
  },
  {
    icon: Printer,
    title: "Любой термопринтер",
    description: "Готовый PDF для этикеток 58×40 мм, оптимизирован под 203 DPI",
  },
  {
    icon: Database,
    title: "База товаров",
    description: "Сохраняйте карточки — не нужно загружать Excel каждый раз",
  },
];

export function Features() {
  return (
    <section className="py-20 bg-cream" id="features">
      <div className="container mx-auto px-6">
        {/* Заголовок */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-warm-gray-900">
            Что умеет сервис
          </h2>
        </motion.div>

        {/* Карточки 2×2 */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon;

            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: index * 0.1 }}
                className="bg-white border-2 border-warm-gray-200 rounded-xl p-6 shadow-[2px_2px_0px_#E7E5E4] hover:border-emerald-600 hover:shadow-[3px_3px_0px_#047857] transition-all duration-200"
              >
                {/* Иконка */}
                <div className="w-12 h-12 bg-emerald-50 border-2 border-emerald-600 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-emerald-600" />
                </div>

                {/* Текст */}
                <h3 className="text-lg font-semibold text-warm-gray-800 mb-2">
                  {feature.title}
                </h3>
                <p className="text-warm-gray-600">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
