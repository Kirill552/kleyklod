"""
Сервис проверки дубликатов кодов маркировки.

Предотвращает повторное использование одних и тех же кодов ЧЗ,
что может привести к штрафам от регулятора.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CodeUsage


@dataclass
class DuplicateInfo:
    """Информация о дубликате кода."""

    code_hash: str
    used_at: datetime
    days_ago: int


@dataclass
class DuplicateCheckResult:
    """Результат проверки на дубликаты."""

    has_duplicates: bool
    duplicate_count: int
    duplicates: list[DuplicateInfo]
    total_codes: int

    @property
    def warning_message(self) -> str | None:
        """Сообщение для пользователя."""
        if not self.has_duplicates:
            return None

        if self.duplicate_count == 1:
            days = self.duplicates[0].days_ago
            if days == 0:
                return "⚠️ 1 код уже использовался сегодня. Продолжить?"
            elif days == 1:
                return "⚠️ 1 код уже использовался вчера. Продолжить?"
            else:
                return f"⚠️ 1 код уже использовался {days} дн. назад. Продолжить?"

        # Находим самый старый дубликат
        max_days = max(d.days_ago for d in self.duplicates)
        if max_days == 0:
            return f"⚠️ {self.duplicate_count} кодов уже использовались сегодня. Продолжить?"
        elif max_days == 1:
            return f"⚠️ {self.duplicate_count} кодов уже использовались вчера. Продолжить?"
        else:
            return f"⚠️ {self.duplicate_count} кодов уже использовались (до {max_days} дн. назад). Продолжить?"


class CodeHistoryService:
    """
    Сервис для отслеживания использованных кодов.

    Хранит SHA-256 хеши кодов, привязанные к пользователю.
    Проверяет дубликаты перед генерацией.
    """

    # Период хранения истории кодов
    RETENTION_DAYS = 30

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _hash_code(code: str) -> str:
        """Вычисляет SHA-256 хеш кода."""
        return hashlib.sha256(code.encode()).hexdigest()

    async def check_duplicates(
        self,
        user_id: uuid.UUID,
        codes: list[str],
    ) -> DuplicateCheckResult:
        """
        Проверяет, использовались ли коды ранее.

        Args:
            user_id: ID пользователя
            codes: Список кодов для проверки

        Returns:
            DuplicateCheckResult с информацией о дубликатах
        """
        if not codes:
            return DuplicateCheckResult(
                has_duplicates=False,
                duplicate_count=0,
                duplicates=[],
                total_codes=0,
            )

        # Вычисляем хеши всех кодов
        code_hashes = [self._hash_code(code) for code in codes]

        # Ищем существующие записи
        stmt = select(CodeUsage).where(
            CodeUsage.user_id == user_id,
            CodeUsage.code_hash.in_(code_hashes),
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().all()

        if not existing:
            return DuplicateCheckResult(
                has_duplicates=False,
                duplicate_count=0,
                duplicates=[],
                total_codes=len(codes),
            )

        # Формируем информацию о дубликатах
        now = datetime.now(UTC)
        duplicates = []
        for usage in existing:
            days_ago = (now - usage.used_at).days
            duplicates.append(
                DuplicateInfo(
                    code_hash=usage.code_hash[:8] + "...",  # Показываем только начало
                    used_at=usage.used_at,
                    days_ago=days_ago,
                )
            )

        return DuplicateCheckResult(
            has_duplicates=True,
            duplicate_count=len(duplicates),
            duplicates=duplicates,
            total_codes=len(codes),
        )

    async def save_usage(
        self,
        user_id: uuid.UUID,
        codes: list[str],
        generation_id: uuid.UUID | None = None,
    ) -> int:
        """
        Сохраняет использованные коды.

        Args:
            user_id: ID пользователя
            codes: Список использованных кодов
            generation_id: ID генерации (опционально)

        Returns:
            Количество сохранённых записей
        """
        if not codes:
            return 0

        # Вычисляем хеши
        code_hashes = [self._hash_code(code) for code in codes]

        # Проверяем, какие хеши уже есть (чтобы не дублировать)
        stmt = select(CodeUsage.code_hash).where(
            CodeUsage.user_id == user_id,
            CodeUsage.code_hash.in_(code_hashes),
        )
        result = await self.session.execute(stmt)
        existing_hashes = set(result.scalars().all())

        # Добавляем только новые
        new_usages = []
        for code_hash in code_hashes:
            if code_hash not in existing_hashes:
                new_usages.append(
                    CodeUsage(
                        user_id=user_id,
                        code_hash=code_hash,
                        generation_id=generation_id,
                    )
                )

        if new_usages:
            self.session.add_all(new_usages)
            await self.session.flush()

        return len(new_usages)

    async def cleanup_old_records(self) -> int:
        """
        Удаляет записи старше RETENTION_DAYS.

        Вызывается периодически (cron job).

        Returns:
            Количество удалённых записей
        """
        cutoff = datetime.now(UTC) - timedelta(days=self.RETENTION_DAYS)

        stmt = delete(CodeUsage).where(CodeUsage.used_at < cutoff)
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount or 0
