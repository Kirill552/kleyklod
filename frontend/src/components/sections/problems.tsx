"use client";

import { motion } from "framer-motion";
import { Banknote, AlertTriangle, Clock } from "lucide-react";

const problems = [
  {
    icon: Banknote,
    title: "2 стикера на товаре = двойные расходы",
    description: "Клеите две наклейки — штрихкод WB и код Честного Знака отдельно? Это 30-50 копеек с каждого товара на материалы и время.",
    highlight: "1000 товаров = 500₽ на ветер",
    color: "amber",
  },
  {
    icon: AlertTriangle,
    title: "Штрафы за маркировку",
    description: "DataMatrix не читается сканером? Штраф за отсутствие маркировки до 300,000₽ для ИП. Возврат товара + простой склада на FBS.",
    highlight: "Штраф за нарушение маркировки",
    color: "rose",
  },
  {
    icon: Clock,
    title: "wbcon и wbarcode — дорого и медленно",
    description: "Генераторы этикеток конкурентов: wbarcode скрывает цены, wbcon требует ручной работы. Печать этикеток 58x40 занимает часы.",
    highlight: "Есть альтернатива лучше",
    color: "warm-gray",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
    },
  },
};

export function Problems() {
  return (
    <section className="section section-alt" id="problems">
      <div className="container mx-auto px-6">
        {/* Заголовок секции */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 bg-rose-100 text-rose-600 rounded-full text-sm font-medium mb-4">
            Знакомо селлерам?
          </span>
          <h2 className="heading-2 text-warm-gray-900 mb-4">
            Проблемы маркировки Честный Знак + WB
          </h2>
          <p className="text-warm-gray-500 max-w-2xl mx-auto text-lg">
            Каждый селлер маркетплейсов сталкивается с этим при печати этикеток для Wildberries и Ozon
          </p>
        </motion.div>

        {/* Карточки проблем */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid md:grid-cols-3 gap-6"
        >
          {problems.map((problem, index) => {
            const Icon = problem.icon;
            const colorClasses = {
              amber: {
                bg: "bg-amber-50",
                icon: "bg-amber-100 text-amber-600",
                highlight: "bg-amber-100 text-amber-700",
              },
              rose: {
                bg: "bg-rose-50",
                icon: "bg-rose-100 text-rose-600",
                highlight: "bg-rose-100 text-rose-700",
              },
              "warm-gray": {
                bg: "bg-warm-gray-50",
                icon: "bg-warm-gray-200 text-warm-gray-600",
                highlight: "bg-warm-gray-200 text-warm-gray-700",
              },
            };
            const colors = colorClasses[problem.color as keyof typeof colorClasses];

            return (
              <motion.div
                key={problem.title}
                variants={itemVariants}
                className="sticker p-6 relative group"
              >
                {/* Номер */}
                <div className="absolute top-4 right-4 text-6xl font-bold text-warm-gray-100 group-hover:text-warm-gray-200 transition-colors">
                  {index + 1}
                </div>

                {/* Иконка */}
                <div className={`w-12 h-12 rounded-xl ${colors.icon} flex items-center justify-center mb-4`}>
                  <Icon className="w-6 h-6" />
                </div>

                {/* Контент */}
                <h3 className="heading-3 text-warm-gray-800 mb-3 relative z-10">
                  {problem.title}
                </h3>
                <p className="text-warm-gray-500 mb-4 relative z-10">
                  {problem.description}
                </p>

                {/* Выделение */}
                <div className={`inline-block px-3 py-1.5 ${colors.highlight} rounded-lg text-sm font-medium`}>
                  {problem.highlight}
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Призыв к действию */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="text-center mt-12"
        >
          <p className="text-warm-gray-600 text-lg">
            <span className="font-semibold text-emerald-600">KleyKod</span> решает все эти проблемы одним кликом
          </p>
        </motion.div>
      </div>
    </section>
  );
}
