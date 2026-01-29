"""API endpoints для статей."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_admin_api_key, get_db
from app.repositories.article_repository import ArticleRepository
from app.schemas.article import (
    ArticleCreate,
    ArticleListItem,
    ArticleResponse,
    ArticleUpdate,
)

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=list[ArticleListItem])
async def get_articles(
    db: AsyncSession = Depends(get_db),
) -> list[ArticleListItem]:
    """
    Получить список опубликованных статей.

    Публичный endpoint без авторизации.
    """
    repo = ArticleRepository(db)
    articles = await repo.get_published()
    return [ArticleListItem.model_validate(a) for a in articles]


@router.get("/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> ArticleResponse:
    """
    Получить статью по slug.

    Публичный endpoint. Возвращает только опубликованные статьи.
    """
    repo = ArticleRepository(db)
    article = await repo.get_by_slug(slug)

    if not article or not article.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена",
        )

    return ArticleResponse.model_validate(article)


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_admin_api_key),
) -> ArticleResponse:
    """
    Создать статью.

    Требуется X-API-Key с правами админа.
    """
    repo = ArticleRepository(db)

    # Проверяем уникальность slug
    existing = await repo.get_by_slug(data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Статья со slug '{data.slug}' уже существует",
        )

    article = await repo.create(data)
    return ArticleResponse.model_validate(article)


@router.put("/{slug}", response_model=ArticleResponse)
async def update_article(
    slug: str,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_admin_api_key),
) -> ArticleResponse:
    """
    Обновить статью.

    Требуется X-API-Key с правами админа.
    """
    repo = ArticleRepository(db)
    article = await repo.get_by_slug(slug)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена",
        )

    # Если меняется slug, проверяем уникальность
    if data.slug and data.slug != slug:
        existing = await repo.get_by_slug(data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Статья со slug '{data.slug}' уже существует",
            )

    updated = await repo.update(article, data)
    return ArticleResponse.model_validate(updated)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_admin_api_key),
) -> None:
    """
    Удалить статью.

    Требуется X-API-Key с правами админа.
    """
    repo = ArticleRepository(db)
    article = await repo.get_by_slug(slug)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена",
        )

    await repo.delete(article)
