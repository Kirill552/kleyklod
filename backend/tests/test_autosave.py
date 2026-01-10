"""
Тесты автосохранения карточек товаров после генерации.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.db.models import UserPlan
from app.repositories.product_repo import ProductRepository


class TestAutoSaveProducts:
    """Тесты автосохранения карточек в базу после генерации."""

    @pytest.fixture
    def mock_user_pro(self):
        """PRO пользователь с правом на автосохранение."""
        user = MagicMock()
        user.id = uuid4()
        user.plan = UserPlan.PRO
        return user

    @pytest.fixture
    def mock_user_enterprise(self):
        """ENTERPRISE пользователь с правом на автосохранение."""
        user = MagicMock()
        user.id = uuid4()
        user.plan = UserPlan.ENTERPRISE
        return user

    @pytest.fixture
    def mock_user_free(self):
        """FREE пользователь без права на автосохранение."""
        user = MagicMock()
        user.id = uuid4()
        user.plan = UserPlan.FREE
        return user

    @pytest.fixture
    def sample_label_items(self):
        """Тестовые товары для сохранения."""
        from app.services.label_generator import LabelItem

        return [
            LabelItem(
                barcode="4670049774802",
                name="Валенки 24",
                article="VAL-24",
                size="24",
                color="Белый",
            ),
            LabelItem(
                barcode="4670049774819",
                name="Валенки 26",
                article="VAL-26",
                size="26",
                color="Серый",
            ),
        ]

    @pytest.fixture
    def sample_label_items_with_duplicates(self):
        """Тестовые товары с дубликатами баркодов (разные коды ЧЗ)."""
        from app.services.label_generator import LabelItem

        return [
            LabelItem(
                barcode="4670049774802",
                name="Валенки 24",
                article="VAL-24",
                size="24",
                color="Белый",
            ),
            LabelItem(
                barcode="4670049774802",  # Тот же баркод, другой код ЧЗ
                name="Валенки 24",
                article="VAL-24",
                size="24",
                color="Белый",
            ),
            LabelItem(
                barcode="4670049774819",
                name="Валенки 26",
                article="VAL-26",
                size="26",
                color="Серый",
            ),
        ]

    def test_autosave_extracts_unique_products(self, sample_label_items):
        """Автосохранение извлекает уникальные товары по barcode."""
        from app.api.routes.labels import _extract_unique_products_for_save

        items_to_save = _extract_unique_products_for_save(sample_label_items)

        assert len(items_to_save) == 2
        barcodes = {item["barcode"] for item in items_to_save}
        assert barcodes == {"4670049774802", "4670049774819"}

    def test_autosave_deduplicates_by_barcode(self, sample_label_items_with_duplicates):
        """Автосохранение дедуплицирует товары с одинаковым barcode."""
        from app.api.routes.labels import _extract_unique_products_for_save

        items_to_save = _extract_unique_products_for_save(sample_label_items_with_duplicates)

        # Должно быть 2 уникальных товара, а не 3
        assert len(items_to_save) == 2
        barcodes = [item["barcode"] for item in items_to_save]
        assert barcodes.count("4670049774802") == 1
        assert barcodes.count("4670049774819") == 1

    def test_autosave_skipped_for_free_plan(self, mock_user_free):
        """FREE план не сохраняет карточки."""
        from app.api.routes.labels import _should_autosave_products

        should_save = _should_autosave_products(mock_user_free)
        assert should_save is False

    def test_autosave_enabled_for_pro_plan(self, mock_user_pro):
        """PRO план сохраняет карточки."""
        from app.api.routes.labels import _should_autosave_products

        should_save = _should_autosave_products(mock_user_pro)
        assert should_save is True

    def test_autosave_enabled_for_enterprise_plan(self, mock_user_enterprise):
        """ENTERPRISE план сохраняет карточки."""
        from app.api.routes.labels import _should_autosave_products

        should_save = _should_autosave_products(mock_user_enterprise)
        assert should_save is True

    def test_autosave_skipped_for_none_user(self):
        """Без пользователя автосохранение отключено."""
        from app.api.routes.labels import _should_autosave_products

        should_save = _should_autosave_products(None)
        assert should_save is False

    def test_extract_preserves_all_fields(self, sample_label_items):
        """Извлечение сохраняет все поля карточки."""
        from app.api.routes.labels import _extract_unique_products_for_save

        items_to_save = _extract_unique_products_for_save(sample_label_items)

        # Проверяем первый товар
        item = next(i for i in items_to_save if i["barcode"] == "4670049774802")
        assert item["name"] == "Валенки 24"
        assert item["article"] == "VAL-24"
        assert item["size"] == "24"
        assert item["color"] == "Белый"

    def test_extract_skips_items_without_barcode(self):
        """Товары без barcode пропускаются."""
        from app.api.routes.labels import _extract_unique_products_for_save
        from app.services.label_generator import LabelItem

        items = [
            LabelItem(barcode="4670049774802", name="С баркодом"),
            LabelItem(barcode="", name="Без баркода"),  # Пустой barcode
            LabelItem(barcode="4670049774819", name="С баркодом 2"),
        ]

        items_to_save = _extract_unique_products_for_save(items)

        assert len(items_to_save) == 2
        barcodes = {item["barcode"] for item in items_to_save}
        assert "" not in barcodes

    @pytest.mark.asyncio
    async def test_autosave_calls_bulk_upsert(self, mock_user_pro, sample_label_items):
        """Автосохранение вызывает bulk_upsert репозитория."""
        from app.api.routes.labels import _autosave_products

        # Мокаем репозиторий
        mock_repo = AsyncMock(spec=ProductRepository)
        mock_repo.bulk_upsert.return_value = {"created": 2, "updated": 0, "skipped": 0}

        result = await _autosave_products(
            user=mock_user_pro,
            label_items=sample_label_items,
            product_repo=mock_repo,
        )

        # Проверяем что bulk_upsert был вызван
        mock_repo.bulk_upsert.assert_called_once()
        call_args = mock_repo.bulk_upsert.call_args
        assert call_args[0][0] == mock_user_pro.id  # user_id
        assert len(call_args[0][1]) == 2  # 2 товара

        # Проверяем результат
        assert result == {"created": 2, "updated": 0, "skipped": 0}

    @pytest.mark.asyncio
    async def test_autosave_returns_none_for_free_user(self, mock_user_free, sample_label_items):
        """Для FREE пользователя автосохранение возвращает None."""
        from app.api.routes.labels import _autosave_products

        mock_repo = AsyncMock(spec=ProductRepository)

        result = await _autosave_products(
            user=mock_user_free,
            label_items=sample_label_items,
            product_repo=mock_repo,
        )

        # bulk_upsert НЕ должен вызываться
        mock_repo.bulk_upsert.assert_not_called()
        assert result is None

    @pytest.mark.asyncio
    async def test_autosave_handles_exception(self, mock_user_pro, sample_label_items):
        """При ошибке репозитория автосохранение возвращает None без исключения."""
        from app.api.routes.labels import _autosave_products

        mock_repo = AsyncMock(spec=ProductRepository)
        mock_repo.bulk_upsert.side_effect = Exception("DB Error")

        result = await _autosave_products(
            user=mock_user_pro,
            label_items=sample_label_items,
            product_repo=mock_repo,
        )

        # Ошибка не должна пробрасываться
        assert result is None

    @pytest.mark.asyncio
    async def test_autosave_returns_none_for_empty_items(self, mock_user_pro):
        """Для пустого списка товаров возвращает None."""
        from app.api.routes.labels import _autosave_products

        mock_repo = AsyncMock(spec=ProductRepository)

        result = await _autosave_products(
            user=mock_user_pro,
            label_items=[],
            product_repo=mock_repo,
        )

        mock_repo.bulk_upsert.assert_not_called()
        assert result is None
