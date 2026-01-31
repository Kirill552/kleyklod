import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from 'next/link';
import { Article } from '@/types/api';
import { Footer } from '@/components/sections/footer';

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

      {/* Hero секция */}
      <div className="bg-gray-900 text-white">
        <div className="max-w-3xl mx-auto px-4 py-12">
          <div className="flex items-center gap-2 text-sm text-emerald-400 mb-4">
            <span>{article.category}</span>
            <span>•</span>
            <span>{article.reading_time} мин чтения</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-white leading-tight">
            {article.title}
          </h1>
          <p className="mt-4 text-lg text-gray-300">
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
        <div className="mt-12 p-6 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl text-center border border-emerald-200 dark:border-emerald-800">
          <p className="font-semibold text-gray-900 dark:text-white text-lg">
            Готовы создать этикетки?
          </p>
          <p className="text-gray-700 dark:text-gray-200 mt-2">
            50 бесплатных этикеток в месяц
          </p>
          <Link
            href="/app/generate"
            className="inline-block mt-4 px-6 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Попробовать бесплатно
          </Link>
        </div>
      </article>

      {/* Footer */}
      <Footer />
    </>
  );
}
