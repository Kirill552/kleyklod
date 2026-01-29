import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getArticle, getArticles } from '@/lib/api';
import { ArticleContent } from '@/components/articles/article-content';

// ISR: перегенерация каждые 10 минут
export const revalidate = 600;

interface PageProps {
  params: Promise<{ slug: string }>;
}

// Генерация статических путей при билде
export async function generateStaticParams() {
  try {
    const articles = await getArticles();
    return articles.map((a) => ({ slug: a.slug }));
  } catch {
    return [];
  }
}

// Динамические метаданные для SEO
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const article = await getArticle(slug);

  if (!article) {
    return {
      title: 'Статья не найдена | KleyKod',
    };
  }

  return {
    title: `${article.title} | KleyKod`,
    description: article.description,
    keywords: article.keywords || undefined,
    openGraph: {
      title: article.title,
      description: article.description,
      images: article.og_image ? [article.og_image] : [],
      type: 'article',
      publishedTime: article.created_at,
      modifiedTime: article.updated_at,
      authors: [article.author],
    },
    alternates: {
      canonical: article.canonical_url || undefined,
    },
  };
}

export default async function ArticlePage({ params }: PageProps) {
  const { slug } = await params;
  const article = await getArticle(slug);

  if (!article) {
    notFound();
  }

  return <ArticleContent article={article} />;
}
