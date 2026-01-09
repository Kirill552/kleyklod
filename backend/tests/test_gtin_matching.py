"""
Тесты для матчинга по GTIN и preflight проверок.

Покрывает:
- Матчинг товаров по GTIN из кодов ЧЗ
- Ошибки при отсутствии товара
- Preflight проверку лимитов полей
- Обогащение из ProductCards
"""

import pytest
from dataclasses import asdict
from unittest.mock import MagicMock, patch

from app.services.label_generator import LabelGenerator, LabelItem
from app.services.excel_parser import DEFAULT_FIELD_PRIORITY


class TestExtractGtinFromCode:
    """Тесты извлечения GTIN из кода маркировки."""

    def setup_method(self):
        """Создаём генератор для тестов."""
        self.generator = LabelGenerator()

    def test_extract_gtin_valid_code(self):
        """Извлечение GTIN из валидного кода."""
        code = "010467004977480221JNlMVsj,QVL6\x1d93xxxx"
        gtin = self.generator._extract_gtin_from_code(code)
        assert gtin == "04670049774802"

    def test_extract_gtin_code_without_ai(self):
        """Код без AI 01 — возвращает None."""
        code = "210467004977480221JNlMVsj"
        gtin = self.generator._extract_gtin_from_code(code)
        assert gtin is None

    def test_extract_gtin_short_code(self):
        """Слишком короткий код — возвращает None."""
        code = "010467"
        gtin = self.generator._extract_gtin_from_code(code)
        assert gtin is None

    def test_extract_gtin_empty_code(self):
        """Пустой код — возвращает None."""
        gtin = self.generator._extract_gtin_from_code("")
        assert gtin is None


class TestMatchItemsWithCodes:
    """Тесты матчинга товаров с кодами ЧЗ по GTIN."""

    def setup_method(self):
        """Создаём генератор и тестовые данные."""
        self.generator = LabelGenerator()

        # Тестовые товары
        self.item1 = LabelItem(
            barcode="4670049774802",
            name="Валенки 24 размер",
            article="VAL-24",
        )
        self.item2 = LabelItem(
            barcode="4670049774819",
            name="Валенки 26 размер",
            article="VAL-26",
        )

    def test_match_one_item_multiple_codes(self):
        """1 товар + несколько кодов с одним GTIN → все коды матчатся."""
        items = [self.item1]
        codes = [
            "010467004977480221AAA\x1d93xxxx",
            "010467004977480221BBB\x1d93xxxx",
            "010467004977480221CCC\x1d93xxxx",
        ]

        matched = self.generator._match_items_with_codes(items, codes)

        assert len(matched) == 3
        for item, code in matched:
            assert item.barcode == "4670049774802"

    def test_match_multiple_items_multiple_codes(self):
        """Несколько товаров + коды с разными GTIN → правильный матчинг."""
        items = [self.item1, self.item2]
        codes = [
            "010467004977480221AAA\x1d93xxxx",  # item1
            "010467004977481921BBB\x1d93xxxx",  # item2
            "010467004977480221CCC\x1d93xxxx",  # item1
        ]

        matched = self.generator._match_items_with_codes(items, codes)

        assert len(matched) == 3
        # Проверяем что матчинг правильный
        barcodes = [item.barcode for item, _ in matched]
        assert barcodes.count("4670049774802") == 2
        assert barcodes.count("4670049774819") == 1

    def test_match_missing_item_raises_error(self):
        """Код с GTIN без соответствующего товара → ValueError."""
        items = [self.item1]  # Только item1
        codes = [
            "010467004977480221AAA\x1d93xxxx",  # item1 - ОК
            "010467004977481921BBB\x1d93xxxx",  # item2 - НЕТ В СПИСКЕ!
        ]

        with pytest.raises(ValueError) as exc_info:
            self.generator._match_items_with_codes(items, codes)

        assert "Не найдены товары для баркодов" in str(exc_info.value)
        assert "4670049774819" in str(exc_info.value)

    def test_match_ignores_invalid_codes(self):
        """Невалидные коды пропускаются без ошибки."""
        items = [self.item1]
        codes = [
            "010467004977480221AAA\x1d93xxxx",  # Валидный
            "invalid_code",  # Невалидный — пропускается
            "010467004977480221BBB\x1d93xxxx",  # Валидный
        ]

        matched = self.generator._match_items_with_codes(items, codes)

        assert len(matched) == 2

    def test_match_empty_codes(self):
        """Пустой список кодов → пустой результат."""
        items = [self.item1]
        codes = []

        matched = self.generator._match_items_with_codes(items, codes)

        assert len(matched) == 0

    def test_match_gtin_with_leading_zero(self):
        """GTIN с ведущим нулём → баркод без ведущего нуля."""
        # GTIN: 04670049774802 → Баркод: 4670049774802
        item = LabelItem(barcode="4670049774802", name="Test")
        items = [item]
        codes = ["010467004977480221AAA\x1d93xxxx"]

        matched = self.generator._match_items_with_codes(items, codes)

        assert len(matched) == 1
        assert matched[0][0].barcode == "4670049774802"


class TestPreflightFieldLimits:
    """Тесты preflight проверки лимитов полей."""

    def test_basic_58x30_limit(self):
        """Basic 58x30: лимит 4 поля (name + 3 текстовых)."""
        from app.services.layout_preflight import FIELD_LIMITS

        limit = FIELD_LIMITS.get("basic", {}).get("58x30")
        # basic 58x30: name (1) + 3 = 4 поля
        assert limit == 4

    def test_professional_58x40_limit(self):
        """Professional 58x40: лимит 11 полей."""
        from app.services.layout_preflight import FIELD_LIMITS

        limit = FIELD_LIMITS.get("professional", {}).get("58x40")
        assert limit == 11

    def test_extended_58x40_limit(self):
        """Extended 58x40: лимит 12 полей."""
        from app.services.layout_preflight import FIELD_LIMITS

        limit = FIELD_LIMITS.get("extended", {}).get("58x40")
        assert limit == 12

    def test_check_field_limits_ok(self):
        """Проверка лимитов: поля в норме."""
        from app.services.layout_preflight import check_field_limits

        result = check_field_limits("basic", "58x40", filled_fields_count=5)
        assert result is None

    def test_check_field_limits_exceeded(self):
        """Проверка лимитов: превышение."""
        from app.services.layout_preflight import check_field_limits

        result = check_field_limits("basic", "58x40", filled_fields_count=7)
        assert result is not None
        assert "Слишком много полей" in result.message


class TestDefaultFieldPriority:
    """Тесты дефолтного приоритета полей."""

    def test_name_is_first(self):
        """Name всегда первым в приоритете."""
        assert DEFAULT_FIELD_PRIORITY[0] == "name"

    def test_article_is_second(self):
        """Article вторым — идентификатор товара."""
        assert DEFAULT_FIELD_PRIORITY[1] == "article"

    def test_all_fields_present(self):
        """Все 11 полей присутствуют."""
        expected_fields = {
            "name",
            "article",
            "size",
            "color",
            "brand",
            "composition",
            "country",
            "manufacturer",
            "importer",
            "production_date",
            "certificate",
        }
        assert set(DEFAULT_FIELD_PRIORITY) == expected_fields

    def test_no_duplicates(self):
        """Нет дубликатов в приоритете."""
        assert len(DEFAULT_FIELD_PRIORITY) == len(set(DEFAULT_FIELD_PRIORITY))


class TestProductCardEnrichment:
    """Тесты обогащения данных из ProductCards."""

    def test_excel_has_priority_over_product_card(self):
        """Данные из Excel имеют приоритет над ProductCard."""
        # Excel данные
        excel_item = LabelItem(
            barcode="4670049774802",
            name="Название из Excel",
            article="ART-EXCEL",
            size=None,  # Пустое — должно обогатиться
        )

        # ProductCard данные
        product_card = {
            "barcode": "4670049774802",
            "name": "Название из базы",
            "article": "ART-DB",
            "size": "42",
            "color": "Красный",
        }

        # Симулируем обогащение
        enriched = _enrich_item_from_product_card(excel_item, product_card)

        # Excel данные сохранились
        assert enriched.name == "Название из Excel"
        assert enriched.article == "ART-EXCEL"
        # Пустые поля обогатились
        assert enriched.size == "42"
        assert enriched.color == "Красный"


def _enrich_item_from_product_card(item: LabelItem, product_card: dict) -> LabelItem:
    """Вспомогательная функция обогащения (копия логики из labels.py)."""
    enriched_data = asdict(item)

    for field in ["name", "article", "size", "color", "brand", "composition", "country"]:
        if not enriched_data.get(field) and product_card.get(field):
            enriched_data[field] = product_card[field]

    return LabelItem(**enriched_data)
