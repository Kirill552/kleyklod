"""Репозиторий для работы со статьями."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article
from app.schemas.article import ArticleCreate, ArticleUpdate


class ArticleRepository:
    """Репозиторий статей."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_slug(self, slug: str) -> Article | None:
        """Получить статью по slug."""
        result = await self.session.execute(select(Article).where(Article.slug == slug))
        return result.scalar_one_or_none()

    async def get_by_id(self, article_id: UUID) -> Article | None:
        """Получить статью по ID."""
        result = await self.session.execute(select(Article).where(Article.id == article_id))
        return result.scalar_one_or_none()

    async def get_published(self) -> list[Article]:
        """Получить все опубликованные статьи."""
        result = await self.session.execute(
            select(Article)
            .where(Article.is_published == True)  # noqa: E712
            .order_by(Article.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[Article]:
        """Получить все статьи (для админки)."""
        result = await self.session.execute(select(Article).order_by(Article.created_at.desc()))
        return list(result.scalars().all())

    async def create(self, data: ArticleCreate) -> Article:
        """Создать статью."""
        article = Article(**data.model_dump())
        self.session.add(article)
        await self.session.commit()
        await self.session.refresh(article)
        return article

    async def update(self, article: Article, data: ArticleUpdate) -> Article:
        """Обновить статью."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(article, field, value)
        await self.session.commit()
        await self.session.refresh(article)
        return article

    async def delete(self, article: Article) -> None:
        """Удалить статью."""
        await self.session.delete(article)
        await self.session.commit()
