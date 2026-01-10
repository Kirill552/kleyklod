"""
Репозиторий карточек товаров.

Обеспечивает CRUD операции для таблицы product_cards.
"""

from uuid import UUID

from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProductCard


class ProductRepository:
    """Репозиторий для работы с карточками товаров."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ProductCard]:
        """
        Получить все карточки пользователя.

        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
            offset: Смещение для пагинации

        Returns:
            Список карточек товаров
        """
        result = await self.session.execute(
            select(ProductCard)
            .where(ProductCard.user_id == user_id)
            .order_by(ProductCard.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_barcode(self, user_id: UUID, barcode: str) -> ProductCard | None:
        """
        Получить карточку по баркоду.

        Args:
            user_id: ID пользователя
            barcode: EAN-13/Code128 баркод

        Returns:
            Карточка товара или None
        """
        result = await self.session.execute(
            select(ProductCard).where(
                ProductCard.user_id == user_id,
                ProductCard.barcode == barcode,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_barcodes(self, user_id: UUID, barcodes: list[str]) -> list[ProductCard]:
        """
        Получить карточки по списку баркодов.

        Args:
            user_id: ID пользователя
            barcodes: Список баркодов

        Returns:
            Список найденных карточек
        """
        if not barcodes:
            return []

        result = await self.session.execute(
            select(ProductCard).where(
                ProductCard.user_id == user_id,
                ProductCard.barcode.in_(barcodes),
            )
        )
        return list(result.scalars().all())

    async def upsert(self, user_id: UUID, barcode: str, **data) -> ProductCard:
        """
        Создать или обновить карточку.

        Использует INSERT ... ON CONFLICT DO UPDATE для атомарного upsert.

        Args:
            user_id: ID пользователя
            barcode: Баркод товара
            **data: Данные карточки (name, article, size, color и т.д.)

        Returns:
            Созданная или обновлённая карточка
        """
        # Убираем None значения, чтобы не перезаписывать существующие
        update_data = {k: v for k, v in data.items() if v is not None}

        # PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        stmt = insert(ProductCard).values(
            user_id=user_id,
            barcode=barcode,
            **update_data,
        )

        # При конфликте обновляем только переданные поля
        if update_data:
            stmt = stmt.on_conflict_do_update(
                constraint="uq_user_barcode",
                set_=update_data,
            )
        else:
            # Если нет данных для обновления — ничего не делаем
            stmt = stmt.on_conflict_do_nothing(constraint="uq_user_barcode")

        await self.session.execute(stmt)
        await self.session.flush()

        # Возвращаем актуальную карточку
        return await self.get_by_barcode(user_id, barcode)  # type: ignore

    async def bulk_upsert(self, user_id: UUID, items: list[dict]) -> dict:
        """
        Массовый upsert карточек.

        Args:
            user_id: ID пользователя
            items: Список словарей с данными карточек (barcode обязателен)

        Returns:
            Статистика: {"created": N, "updated": M, "skipped": K}
        """
        if not items:
            return {"created": 0, "updated": 0, "skipped": 0}

        # Получаем существующие карточки
        barcodes = [item.get("barcode") for item in items if item.get("barcode")]
        existing = await self.get_by_barcodes(user_id, barcodes)
        existing_barcodes = {card.barcode for card in existing}

        created = 0
        updated = 0
        skipped = 0

        for item in items:
            barcode = item.get("barcode")
            if not barcode:
                skipped += 1
                continue

            # Подготавливаем данные для upsert
            data = {k: v for k, v in item.items() if k != "barcode" and v is not None}

            if barcode in existing_barcodes:
                # Обновляем существующую
                if data:
                    await self.session.execute(
                        update(ProductCard)
                        .where(
                            ProductCard.user_id == user_id,
                            ProductCard.barcode == barcode,
                        )
                        .values(**data)
                    )
                    updated += 1
                else:
                    skipped += 1
            else:
                # Создаём новую
                new_card = ProductCard(
                    user_id=user_id,
                    barcode=barcode,
                    **data,
                )
                self.session.add(new_card)
                created += 1
                existing_barcodes.add(barcode)  # Предотвращаем дубликаты в batch

        await self.session.flush()
        return {"created": created, "updated": updated, "skipped": skipped}

    async def update_serial(self, user_id: UUID, barcode: str, serial: int) -> None:
        """
        Обновить последний серийный номер.

        Args:
            user_id: ID пользователя
            barcode: Баркод товара
            serial: Новый серийный номер
        """
        await self.session.execute(
            update(ProductCard)
            .where(
                ProductCard.user_id == user_id,
                ProductCard.barcode == barcode,
            )
            .values(last_serial_number=serial)
        )
        await self.session.flush()

    async def increment_serial(self, user_id: UUID, barcode: str, count: int = 1) -> int:
        """
        Инкрементировать серийный номер и вернуть новое значение.

        Args:
            user_id: ID пользователя
            barcode: Баркод товара
            count: На сколько увеличить

        Returns:
            Новый серийный номер
        """
        card = await self.get_by_barcode(user_id, barcode)
        if not card:
            return count

        new_serial = card.last_serial_number + count
        await self.update_serial(user_id, barcode, new_serial)
        return new_serial

    async def delete(self, user_id: UUID, barcode: str) -> bool:
        """
        Удалить карточку.

        Args:
            user_id: ID пользователя
            barcode: Баркод товара

        Returns:
            True если карточка была удалена
        """
        result = await self.session.execute(
            delete(ProductCard).where(
                ProductCard.user_id == user_id,
                ProductCard.barcode == barcode,
            )
        )
        await self.session.flush()
        return (result.rowcount or 0) > 0

    async def delete_all(self, user_id: UUID) -> int:
        """
        Удалить все карточки пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Количество удалённых карточек
        """
        result = await self.session.execute(
            delete(ProductCard).where(ProductCard.user_id == user_id)
        )
        await self.session.flush()
        return result.rowcount or 0

    async def search(self, user_id: UUID, query: str, limit: int = 20) -> list[ProductCard]:
        """
        Поиск по названию/артикулу/баркоду.

        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            Список найденных карточек
        """
        # Экранируем SQL wildcards для защиты от SQL Wildcard Injection
        escaped_query = query.replace("%", r"\%").replace("_", r"\_")
        search_pattern = f"%{escaped_query}%"

        result = await self.session.execute(
            select(ProductCard)
            .where(
                ProductCard.user_id == user_id,
                or_(
                    ProductCard.barcode.ilike(search_pattern),
                    ProductCard.name.ilike(search_pattern),
                    ProductCard.article.ilike(search_pattern),
                    ProductCard.brand.ilike(search_pattern),
                ),
            )
            .order_by(ProductCard.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(self, user_id: UUID) -> int:
        """
        Подсчитать количество карточек пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Количество карточек
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(ProductCard.id)).where(ProductCard.user_id == user_id)
        )
        return result.scalar_one()
