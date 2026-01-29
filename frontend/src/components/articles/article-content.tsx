import ReactMarkdown from 'react-markdown';
import Link from 'next/link';
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

      <article className="max-w-3xl mx-auto px-4 py-8">
        {/* Шапка */}
        <header className="mb-8">
          <div className="flex items-center gap-2 text-sm text-emerald-600 mb-3">
            <span>{article.category}</span>
            <span>•</span>
            <span>{article.reading_time} мин чтения</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {article.title}
          </h1>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
            {article.description}
          </p>
        </header>

        {/* Контент */}
        <div className="prose prose-emerald dark:prose-invert max-w-none">
          <ReactMarkdown>{article.content}</ReactMarkdown>
        </div>

        {/* CTA блок */}
        <div className="mt-12 p-6 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl text-center">
          <p className="font-semibold text-gray-900 dark:text-white">
            Готовы создать этикетки?
          </p>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            50 бесплатных этикеток каждый день
          </p>
          <Link
            href="/app/generate"
            className="inline-block mt-4 px-6 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Попробовать бесплатно
          </Link>
        </div>
      </article>
    </>
  );
}
