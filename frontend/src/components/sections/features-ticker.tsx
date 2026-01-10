"use client";

import { useCallback, useEffect } from "react";
import useEmblaCarousel from "embla-carousel-react";
import AutoScroll from "embla-carousel-auto-scroll";
import {
  Zap,
  Shield,
  FileSpreadsheet,
  Database,
  Bot,
  Sparkles,
  CheckCircle2,
  Clock,
  type LucideIcon,
} from "lucide-react";

interface FeatureItem {
  icon: LucideIcon;
  text: string;
  highlight?: string;
}

const featureItems: FeatureItem[] = [
  { icon: Zap, text: "В 50× быстрее", highlight: "ручной работы" },
  { icon: Shield, text: "Проверка качества", highlight: "DataMatrix" },
  { icon: FileSpreadsheet, text: "Загрузка из", highlight: "Excel" },
  { icon: Database, text: "База карточек", highlight: "товаров" },
  { icon: Bot, text: "Telegram", highlight: "бот" },
  { icon: Sparkles, text: "3 макета", highlight: "этикеток" },
  { icon: CheckCircle2, text: "Контрастность", highlight: ">80%" },
  { icon: Clock, text: "DataMatrix", highlight: ">22мм" },
];

export function FeaturesTicker() {
  const [emblaRef, emblaApi] = useEmblaCarousel(
    {
      loop: true,
      dragFree: true,
      containScroll: false,
      align: "start",
    },
    [
      AutoScroll({
        speed: 1,
        stopOnInteraction: false,
        stopOnMouseEnter: true,
        stopOnFocusIn: true,
      }),
    ]
  );

  // Обработчик для возобновления автоскролла после взаимодействия
  const onPointerUp = useCallback(() => {
    const autoScroll = emblaApi?.plugins()?.autoScroll;
    if (!autoScroll) return;

    const playOrStop = autoScroll.isPlaying() ? autoScroll.stop : autoScroll.play;
    playOrStop();
  }, [emblaApi]);

  useEffect(() => {
    if (!emblaApi) return;

    emblaApi.on("pointerUp", onPointerUp);

    return () => {
      emblaApi.off("pointerUp", onPointerUp);
    };
  }, [emblaApi, onPointerUp]);

  // Дублируем элементы для бесшовного цикла
  const duplicatedItems = [...featureItems, ...featureItems, ...featureItems];

  return (
    <section className="py-6 bg-gradient-to-r from-emerald-50 via-white to-emerald-50 border-y border-warm-gray-100 overflow-hidden">
      <div className="embla" ref={emblaRef}>
        <div className="embla__container flex">
          {duplicatedItems.map((item, index) => {
            const Icon = item.icon;
            return (
              <div
                key={`${item.text}-${index}`}
                className="embla__slide flex-shrink-0 px-4"
              >
                <div className="flex items-center gap-2 whitespace-nowrap">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-4 h-4 text-emerald-600" />
                  </div>
                  <span className="text-warm-gray-600 text-sm font-medium">
                    {item.text}{" "}
                    {item.highlight && (
                      <span className="text-emerald-600 font-semibold">
                        {item.highlight}
                      </span>
                    )}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
