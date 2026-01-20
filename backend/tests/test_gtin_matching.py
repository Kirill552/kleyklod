"""
Тесты для матчинга по GTIN и preflight проверок.

Покрывает:
- Матчинг товаров по GTIN из кодов ЧЗ
- Ошибки при отсутствии товара
- Preflight проверку лимитов полей
- Обогащение из ProductCards
"""

from dataclasses import asdict

import pytest

from app.services.excel_parser import DEFAULT_FIELD_PRIORITY
from app.services.label_generator import LabelGenerator, LabelItem


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
        for item, _code in matched:
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


class TestAutoFallbackSingleItem:
    """Тесты авто-fallback для 1 товара + 1 уникального GTIN.

    Проблема: СНГ-селлеры имеют внутренние WB баркоды (20...)
    которые не совпадают с GTIN в кодах ЧЗ (047...).
    Решение: При 1 товаре в Excel и 1 уникальном GTIN в ЧЗ —
    автоматически считать их одним товаром.
    """

    def setup_method(self):
        """Создаём генератор для тестов."""
        self.generator = LabelGenerator()

    def test_single_item_single_gtin_fallback(self):
        """1 товар + 1 GTIN разные баркоды → fallback работает.

        Ситуация:
        - В Excel баркод 2000012345678 (внутренний WB)
        - В кодах ЧЗ GTIN 04670049774802 (реальный)
        - Они не совпадают, но это единственный товар
        - Должен сработать fallback
        """
        # Внутренний WB баркод (не совпадает с GTIN)
        item = LabelItem(
            barcode="2000012345678",
            name="Товар СНГ-селлера",
            article="СНГ-001",
        )
        items = [item]

        # 3 кода ЧЗ с одним GTIN (отличается от баркода товара)
        codes = [
            "010467004977480221AAA\x1d93xxxx",
            "010467004977480221BBB\x1d93xxxx",
            "010467004977480221CCC\x1d93xxxx",
        ]

        # Должен сработать fallback — не упасть с ошибкой
        matched = self.generator._match_items_with_codes(items, codes)

        # Все 3 кода должны быть сопоставлены с единственным товаром
        assert len(matched) == 3
        for matched_item, _code in matched:
            assert matched_item.barcode == "2000012345678"
            assert matched_item.name == "Товар СНГ-селлера"

    def test_single_item_multiple_gtins_no_fallback(self):
        """1 товар + несколько разных GTIN → ошибка (без fallback).

        Ситуация:
        - В Excel 1 товар
        - В кодах ЧЗ несколько разных GTIN
        - Невозможно определить какой GTIN к какому товару
        - Должна быть ошибка
        """
        item = LabelItem(
            barcode="2000012345678",
            name="Товар СНГ-селлера",
            article="СНГ-001",
        )
        items = [item]

        # 3 кода ЧЗ с РАЗНЫМИ GTIN
        codes = [
            "010467004977480221AAA\x1d93xxxx",  # GTIN: 04670049774802
            "010467004977481921BBB\x1d93xxxx",  # GTIN: 04670049774819 (другой!)
            "010467004977480221CCC\x1d93xxxx",  # GTIN: 04670049774802
        ]

        # Должна быть ошибка — несколько разных GTIN, fallback не применяется
        with pytest.raises(ValueError) as exc_info:
            self.generator._match_items_with_codes(items, codes)

        assert "Не найдены товары для баркодов" in str(exc_info.value)

    def test_multiple_items_no_fallback(self):
        """Несколько товаров → без fallback (стандартная логика).

        Если товаров больше одного, fallback не применяется,
        даже если баркоды не совпадают.
        """
        item1 = LabelItem(
            barcode="2000012345678",
            name="Товар 1",
            article="T-001",
        )
        item2 = LabelItem(
            barcode="2000012345679",
            name="Товар 2",
            article="T-002",
        )
        items = [item1, item2]

        # Коды ЧЗ с GTIN который не совпадает ни с одним баркодом
        codes = [
            "010467004977480221AAA\x1d93xxxx",
            "010467004977480221BBB\x1d93xxxx",
        ]

        # Должна быть ошибка — несколько товаров, fallback не применяется
        with pytest.raises(ValueError) as exc_info:
            self.generator._match_items_with_codes(items, codes)

        assert "Не найдены товары для баркодов" in str(exc_info.value)


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


class TestFilterFieldsByPriority:
    """Тесты фильтрации полей по приоритету."""

    def test_basic_58x30_truncates_to_4_fields(self):
        """Basic 58x30: обрезает до 4 полей (name + 3)."""
        from app.services.layout_preflight import filter_fields_by_priority

        # 7 заполненных полей
        filled = {
            "name": True,
            "article": True,
            "size": True,
            "color": True,
            "brand": True,
            "composition": True,
            "country": True,
            "manufacturer": False,
            "importer": False,
            "production_date": False,
            "certificate": False,
        }

        result = filter_fields_by_priority(
            layout="basic",
            template="58x30",
            filled_fields=filled,
        )

        # Должно остаться 4 поля: name (отдельно) + article, size, color
        assert result["name"] is True
        assert result["article"] is True
        assert result["size"] is True
        assert result["color"] is True
        # Остальные обрезаны
        assert result["brand"] is False
        assert result["composition"] is False
        assert result["country"] is False

    def test_basic_58x40_truncates_to_5_fields(self):
        """Basic 58x40: обрезает до 5 полей (name + 4)."""
        from app.services.layout_preflight import filter_fields_by_priority

        filled = {
            "name": True,
            "article": True,
            "size": True,
            "color": True,
            "brand": True,
            "composition": True,
            "country": True,
            "manufacturer": False,
            "importer": False,
            "production_date": False,
            "certificate": False,
        }

        result = filter_fields_by_priority(
            layout="basic",
            template="58x40",
            filled_fields=filled,
        )

        # Должно остаться 5 полей: name + article, size, color, brand
        assert result["name"] is True
        assert result["article"] is True
        assert result["size"] is True
        assert result["color"] is True
        assert result["brand"] is True
        # Остальные обрезаны
        assert result["composition"] is False
        assert result["country"] is False

    def test_extended_truncates_all_fields_together(self):
        """Extended: все поля в одном блоке, обрезаются вместе."""
        from app.services.layout_preflight import filter_fields_by_priority

        # Все 11 полей заполнены
        filled = {
            "name": True,
            "article": True,
            "size": True,
            "color": True,
            "brand": True,
            "composition": True,
            "country": True,
            "manufacturer": True,
            "importer": True,
            "production_date": True,
            "certificate": True,
        }

        result = filter_fields_by_priority(
            layout="extended",
            template="58x40",
            filled_fields=filled,
        )

        # Extended 58x40 лимит = 12, все 11 должны пройти
        assert sum(result.values()) == 11

    def test_custom_priority_respected(self):
        """Кастомный приоритет: brand перед size."""
        from app.services.layout_preflight import filter_fields_by_priority

        filled = {
            "name": True,
            "article": True,
            "size": True,
            "color": True,
            "brand": True,
            "composition": False,
            "country": False,
            "manufacturer": False,
            "importer": False,
            "production_date": False,
            "certificate": False,
        }

        # Кастомный приоритет: brand важнее size
        custom_priority = [
            "name",
            "article",
            "brand",  # Переместили выше size
            "color",
            "size",
            "composition",
            "country",
            "manufacturer",
            "importer",
            "production_date",
            "certificate",
        ]

        result = filter_fields_by_priority(
            layout="basic",
            template="58x30",  # Лимит 4: name + 3
            filled_fields=filled,
            field_priority=custom_priority,
        )

        # name (отдельно) + article, brand, color — size обрезан!
        assert result["name"] is True
        assert result["article"] is True
        assert result["brand"] is True
        assert result["color"] is True
        assert result["size"] is False  # Обрезан из-за низкого приоритета

    def test_no_name_filled(self):
        """Без name: весь лимит на текстовый блок."""
        from app.services.layout_preflight import filter_fields_by_priority

        filled = {
            "name": False,  # Нет названия
            "article": True,
            "size": True,
            "color": True,
            "brand": True,
            "composition": True,
            "country": False,
            "manufacturer": False,
            "importer": False,
            "production_date": False,
            "certificate": False,
        }

        result = filter_fields_by_priority(
            layout="basic",
            template="58x30",  # Лимит 4
            filled_fields=filled,
        )

        # Без name: все 4 поля в текстовый блок
        assert result["name"] is False
        assert result["article"] is True
        assert result["size"] is True
        assert result["color"] is True
        assert result["brand"] is True
        assert result["composition"] is False  # 5-е поле обрезано

    def test_fewer_fields_than_limit(self):
        """Меньше полей чем лимит: все проходят."""
        from app.services.layout_preflight import filter_fields_by_priority

        filled = {
            "name": True,
            "article": True,
            "size": False,
            "color": False,
            "brand": False,
            "composition": False,
            "country": False,
            "manufacturer": False,
            "importer": False,
            "production_date": False,
            "certificate": False,
        }

        result = filter_fields_by_priority(
            layout="basic",
            template="58x40",  # Лимит 5
            filled_fields=filled,
        )

        # Только 2 поля заполнено — оба проходят
        assert result["name"] is True
        assert result["article"] is True
        assert sum(result.values()) == 2
