"""Pydantic схемы для статей."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ArticleBase(BaseModel):
    """Базовые поля статьи."""

    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9-]+$")
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=300)
    content: str
    keywords: str | None = Field(None, max_length=500)
    og_image: str | None = Field(None, max_length=300)
    canonical_url: str | None = Field(None, max_length=300)
    author: str = Field(default="KleyKod", max_length=100)
    category: str = Field(..., max_length=50)
    tags: str | None = Field(None, max_length=300)
    reading_time: int = Field(default=5, ge=1, le=60)
    structured_data: dict | None = None
    is_published: bool = False


class ArticleCreate(ArticleBase):
    """Схема для создания статьи."""

    pass


class ArticleUpdate(BaseModel):
    """Схема для обновления статьи (все поля опциональны)."""

    slug: str | None = Field(None, max_length=100, pattern=r"^[a-z0-9-]+$")
    title: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=300)
    content: str | None = None
    keywords: str | None = Field(None, max_length=500)
    og_image: str | None = Field(None, max_length=300)
    canonical_url: str | None = Field(None, max_length=300)
    author: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=50)
    tags: str | None = Field(None, max_length=300)
    reading_time: int | None = Field(None, ge=1, le=60)
    structured_data: dict | None = None
    is_published: bool | None = None


class ArticleResponse(ArticleBase):
    """Схема ответа со статьёй."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArticleListItem(BaseModel):
    """Краткая информация о статье для списка."""

    slug: str
    title: str
    description: str
    category: str
    reading_time: int
    created_at: datetime

    class Config:
        from_attributes = True
