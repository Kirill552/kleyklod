import { Metadata } from 'next';
import Link from 'next/link';
import { Header } from '@/components/sections/header';
import { Footer } from '@/components/sections/footer';
import { Button } from '@/components/ui/button';
import { LandingTracker } from '@/components/analytics/landing-tracker';
import { Check, QrCode, FileSpreadsheet, Zap, Shield } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Этикетки для Честного знака бесплатно — генератор DataMatrix, печать PDF',
  description: 'Бесплатный генератор этикеток для Честного знака. Загрузите CSV из ЛК ЧЗ — получите PDF с DataMatrix 22×22мм по ГОСТу. Печать этикеток честный знак до 30 000 кодов.',
  keywords: 'этикетки для честного знака, печать этикеток честный знак, шаблон этикетки честный знак, datamatrix генератор, генератор честный знак бесплатно, размер этикетки 58 40, маркировка чз',
  alternates: {
    canonical: 'https://kleykod.ru/chz-labels',
  },
  openGraph: {
    title: 'Этикетки для Честного знака бесплатно — генератор DataMatrix',
    description: 'Загрузите CSV из ЛК ЧЗ — получите PDF с DataMatrix по ГОСТу. Печать до 30 000 кодов бесплатно.',
    url: 'https://kleykod.ru/chz-labels',
    siteName: 'KleyKod',
    locale: 'ru_RU',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Этикетки для Честного знака — генератор бесплатно',
    description: 'Бесплатный генератор DataMatrix для маркировки. Печать этикеток до 30 000 кодов.',
  },
};

export default function ChzLabelsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <LandingTracker landing="chz" />
      <Header />

      <main className="flex-1">
        {/* Hero */}
        <section className="py-20 px-4 bg-gradient-to-b from-emerald-50 to-white">
          <div className="max-w-6xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
                  <Zap className="h-4 w-4" />
                  Бесплатно, не тратит лимит
                </div>

                <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
                  Этикетки для
                  <span className="text-emerald-600"> Честного знака</span>
                </h1>

                <p className="text-xl text-gray-600 mb-8">
                  Бесплатный генератор этикеток для Честного знака. Загрузите CSV из ЛК ЧЗ — получите готовые этикетки с DataMatrix для термопринтера.
                </p>

                <ul className="space-y-3 mb-8">
                  {[
                    'DataMatrix 22×22мм по ГОСТу',
                    'До 30 000 кодов за раз',
                    'Формат 58×40 мм',
                    'Мгновенная генерация PDF',
                  ].map((item) => (
                    <li key={item} className="flex items-center gap-3 text-gray-700">
                      <Check className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>

                <Link href="/login?redirect=/app/generate?mode=chz">
                  <Button size="lg" className="text-lg px-8">
                    Создать этикетки бесплатно
                  </Button>
                </Link>
              </div>

              <div className="relative">
                {/* Визуализация: CSV → этикетка */}
                <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-16 h-16 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <FileSpreadsheet className="h-8 w-8 text-emerald-600" />
                    </div>
                    <div className="flex-1 h-2 bg-emerald-200 rounded-full">
                      <div className="h-full w-2/3 bg-emerald-500 rounded-full animate-pulse" />
                    </div>
                    <div className="w-16 h-16 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <QrCode className="h-8 w-8 text-emerald-600" />
                    </div>
                  </div>
                  <div className="text-center text-gray-500">
                    CSV из ЛК ЧЗ → Этикетки PDF
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
                { step: '1', title: 'Скачайте CSV', desc: 'Экспортируйте коды из личного кабинета Честного знака' },
                { step: '2', title: 'Загрузите файл', desc: 'Перетащите CSV в генератор (не открывайте в Excel!)' },
                { step: '3', title: 'Скачайте PDF', desc: 'Готовые этикетки для термопринтера' },
              ].map((item) => (
                <div key={item.step} className="text-center">
                  <div className="w-12 h-12 bg-emerald-500 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
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
                { icon: Zap, title: 'Мгновенно', desc: 'Генерация 10 000 этикеток за секунды' },
                { icon: Shield, title: 'По ГОСТу', desc: 'DataMatrix минимум 22×22мм, 100% сканируемость' },
                { icon: FileSpreadsheet, title: 'Большие объёмы', desc: 'До 30 000 кодов в одном файле' },
                { icon: Check, title: 'Бесплатно', desc: 'Не расходует месячный лимит' },
              ].map((item) => (
                <div key={item.title} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                  <item.icon className="h-8 w-8 text-emerald-500 mb-4" />
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
              Бесплатная печать этикеток для Честного знака. Регистрация займёт 10 секунд.
            </p>
            <Link href="/login?redirect=/app/generate?mode=chz">
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
