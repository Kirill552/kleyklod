import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from 'next/link';
import { Sparkles, ArrowRight } from 'lucide-react';
import { Article } from '@/types/api';

interface ArticleContentProps {
  article: Article;
}

export function ArticleContent({ article }: ArticleContentProps) {
  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: article.title,
    description: article.description,
    author: {
      '@type': 'Person',
      name: article.author,
    },
    datePublished: article.created_at,
    dateModified: article.updated_at,
    publisher: {
      '@type': 'Organization',
      name: 'KleyKod',
      url: 'https://kleykod.ru',
    },
  };

  return (
    <>
      {/* Article Schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />

      {/* Дополнительные structured data (FAQ, HowTo) */}
      {article.structured_data && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(article.structured_data),
          }}
        />
      )}

      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-sm border-b border-warm-gray-100">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-9 h-9 bg-emerald-600 rounded-xl flex items-center justify-center shadow-[2px_2px_0px_#047857]">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-lg text-warm-gray-800">
                KleyKod
              </span>
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
            >
              Попробовать бесплатно
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Breadcrumbs */}
      <div className="container mx-auto px-4 sm:px-6 py-4 bg-white">
        <nav className="flex items-center gap-2 text-sm text-warm-gray-500">
          <Link href="/" className="hover:text-emerald-600 transition-colors">
            Главная
          </Link>
          <span>/</span>
          <Link href="/articles" className="hover:text-emerald-600 transition-colors">
            Статьи
          </Link>
          <span>/</span>
          <span className="text-warm-gray-700 truncate max-w-[200px] sm:max-w-none">
            {article.title}
          </span>
        </nav>
      </div>

      {/* Hero секция */}
      <div className="bg-cream border-b border-warm-gray-200">
        <div className="max-w-3xl mx-auto px-4 py-12">
          <div className="flex items-center gap-2 text-sm mb-4">
            <span className="text-emerald-600 font-medium">{article.category}</span>
            <span className="text-warm-gray-400">•</span>
            <span className="text-warm-gray-500">{article.reading_time} мин чтения</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-warm-gray-900 leading-tight">
            {article.title}
          </h1>
          <p className="mt-4 text-lg text-warm-gray-600">
            {article.description}
          </p>
        </div>
      </div>

      <article className="max-w-3xl mx-auto px-4 py-8 bg-white">

        {/* Контент */}
        <div className="prose prose-emerald dark:prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{article.content}</ReactMarkdown>
        </div>

        {/* CTA блок */}
        <section className="mt-12 bg-emerald-700 rounded-xl p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-3">
            Готовы создать этикетки?
          </h2>
          <p className="text-emerald-100 mb-6">
            50 бесплатных этикеток в месяц
          </p>
          <Link
            href="/app/generate"
            className="inline-block px-6 py-3 bg-white text-emerald-700 font-semibold rounded-lg hover:bg-emerald-50 transition-colors"
          >
            Попробовать бесплатно
          </Link>
        </section>
      </article>
    </>
  );
}
