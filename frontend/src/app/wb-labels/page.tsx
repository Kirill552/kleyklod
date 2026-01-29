import { Metadata } from 'next';
import Link from 'next/link';
import { Header } from '@/components/sections/header';
import { Footer } from '@/components/sections/footer';
import { Button } from '@/components/ui/button';
import { LandingTracker } from '@/components/analytics/landing-tracker';
import { Check, BarChart3, Printer, FileSpreadsheet, Zap } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Генератор этикеток для Вайлдберриз онлайн бесплатно — штрихкоды WB',
  description: 'Бесплатный генератор этикеток для Вайлдберриз онлайн. Создайте этикетки со штрихкодами для термопринтера за 2 клика. Форматы 58×40, 58×30 мм. До 10 000 штук.',
  keywords: 'генератор этикеток для вайлдберриз, этикетки вб онлайн бесплатно, штрихкоды wildberries, генератор штрихкодов вб, печать этикеток для вайлдберриз, для термопринтера, этикетки wb',
  alternates: {
    canonical: 'https://kleykod.ru/wb-labels',
  },
  openGraph: {
    title: 'Генератор этикеток для Вайлдберриз онлайн бесплатно',
    description: 'Создайте этикетки со штрихкодами для ВБ за 2 клика. Форматы 58×40, 58×30 мм. Бесплатно.',
    url: 'https://kleykod.ru/wb-labels',
    siteName: 'KleyKod',
    locale: 'ru_RU',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Генератор этикеток для Вайлдберриз бесплатно',
    description: 'Бесплатный генератор штрихкодов для ВБ онлайн. Термопринтер и А4.',
  },
};

export default function WbLabelsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <LandingTracker landing="wb" />
      <Header />

      <main className="flex-1">
        {/* Hero */}
        <section className="py-20 px-4 bg-gradient-to-b from-blue-50 to-white">
          <div className="max-w-6xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
                  <Zap className="h-4 w-4" />
                  Бесплатно, не тратит лимит
                </div>

                <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
                  Генератор этикеток для
                  <span className="text-blue-600"> Вайлдберриз</span>
                </h1>

                <p className="text-xl text-gray-600 mb-8">
                  Создайте этикетки со штрихкодами для Вайлдберриз онлайн за 2 клика. Для термопринтера любого формата.
                </p>

                <ul className="space-y-3 mb-8">
                  {[
                    'Штрихкоды EAN-13 и Code-128',
                    'Форматы 58×40, 58×30 мм',
                    'Мгновенная генерация PDF',
                    'До 10 000 этикеток за раз',
                  ].map((item) => (
                    <li key={item} className="flex items-center gap-3 text-gray-700">
                      <Check className="h-5 w-5 text-blue-500 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>

                <Link href="/login?redirect=/app/generate?mode=wb">
                  <Button size="lg" className="text-lg px-8">
                    Создать этикетки бесплатно
                  </Button>
                </Link>
              </div>

              <div className="relative">
                {/* Визуализация: данные → этикетка */}
                <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center">
                      <FileSpreadsheet className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="flex-1 h-2 bg-blue-200 rounded-full">
                      <div className="h-full w-2/3 bg-blue-500 rounded-full animate-pulse" />
                    </div>
                    <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center">
                      <Printer className="h-8 w-8 text-blue-600" />
                    </div>
                  </div>
                  <div className="text-center text-gray-500">
                    Данные товара → Этикетки PDF
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Как это работает */}
        <section className="py-16 px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">Как это работает</h2>

            <div className="grid md:grid-cols-3 gap-8">
              {[
                { step: '1', title: 'Введите данные', desc: 'Укажите штрихкод и артикул товара' },
                { step: '2', title: 'Выберите формат', desc: 'Выберите размер этикетки для вашего принтера' },
                { step: '3', title: 'Скачайте PDF', desc: 'Готовые этикетки для печати' },
              ].map((item) => (
                <div key={item.step} className="text-center">
                  <div className="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                    {item.step}
                  </div>
                  <h3 className="font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-600 text-sm">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Преимущества */}
        <section className="py-16 px-4 bg-gray-50">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">Почему выбирают нас</h2>

            <div className="grid md:grid-cols-2 gap-6">
              {[
                { icon: Zap, title: 'Мгновенно', desc: 'Генерация 1000 этикеток за секунды' },
                { icon: BarChart3, title: 'Все форматы', desc: 'Поддержка 58×40, 58×30 мм' },
                { icon: Printer, title: 'Для любого принтера', desc: 'PDF подходит для всех термопринтеров' },
                { icon: Check, title: 'Бесплатно', desc: 'Не расходует месячный лимит' },
              ].map((item) => (
                <div key={item.title} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                  <item.icon className="h-8 w-8 text-blue-500 mb-4" />
                  <h3 className="font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-600 text-sm">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 px-4">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-6">Готовы начать?</h2>
            <p className="text-gray-600 mb-8">
              Бесплатная генерация этикеток для Вайлдберриз онлайн. Регистрация займёт 10 секунд.
            </p>
            <Link href="/login?redirect=/app/generate?mode=wb">
              <Button size="lg" className="text-lg px-8">
                Создать этикетки
              </Button>
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
