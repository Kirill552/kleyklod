"""
Тесты генератора этикеток label_generator.py.

Покрывает:
- Размер DataMatrix >= 22мм (требование ЧЗ)
- Генерация валидных PDF
- Все layouts (basic, professional, extended)
- Все размеры (58x30, 58x40, 58x60)
- Режимы нумерации
"""

import pytest

from app.config import LABEL
from app.services.datamatrix import DataMatrixGenerator, GeneratedDataMatrix
from app.services.label_generator import (
    LABEL_SIZES,
    LAYOUTS,
    LabelGenerator,
    LabelItem,
    parse_preflight_error,
)

# === Fixtures ===


@pytest.fixture
def generator() -> LabelGenerator:
    """Экземпляр генератора этикеток."""
    return LabelGenerator()


@pytest.fixture
def dm_generator() -> DataMatrixGenerator:
    """Экземпляр генератора DataMatrix."""
    return DataMatrixGenerator()


@pytest.fixture
def sample_item() -> LabelItem:
    """Тестовый товар."""
    return LabelItem(
        barcode="4670049774802",
        name="Валенки зимние",
        article="VAL-24",
        size="42",
        color="Черный",
        brand="TestBrand",
        country="Россия",
        composition="Шерсть 100%",
    )


@pytest.fixture
def sample_items() -> list[LabelItem]:
    """Список тестовых товаров."""
    return [
        LabelItem(
            barcode="4670049774802",
            name="Валенки зимние",
            article="VAL-24",
            size="42",
            color="Черный",
        ),
        LabelItem(
            barcode="4670049774819",
            name="Валенки летние",
            article="VAL-26",
            size="44",
            color="Белый",
        ),
    ]


@pytest.fixture
def sample_chz_codes() -> list[str]:
    """Реальные коды ЧЗ для тестов."""
    return [
        "010467004977480221JNlMVsj,QVL6\x1d93xxxx",
        "010467004977480221BBBtest\x1d93yyyy",
        "010467004977480221CCCdata\x1d93zzzz",
    ]


@pytest.fixture
def single_chz_code() -> str:
    """Один код ЧЗ."""
    return "010467004977480221JNlMVsj,QVL6\x1d93xxxx"


# === Тесты размера DataMatrix ===


class TestDataMatrixSize:
    """Размер DataMatrix >= 22мм — критическое требование ЧЗ."""

    def test_datamatrix_minimum_size_config(self):
        """Проверка что конфиг содержит минимум 22мм."""
        assert LABEL.DATAMATRIX_MIN_MM >= 22.0
        assert LABEL.DATAMATRIX_MAX_MM >= LABEL.DATAMATRIX_MIN_MM

    def test_datamatrix_generator_default_size(self, dm_generator: DataMatrixGenerator):
        """Генератор по умолчанию использует оптимальный размер (26мм)."""
        assert dm_generator.target_size_mm == LABEL.DATAMATRIX_MAX_MM
        assert dm_generator.target_size_mm >= 22.0

    def test_datamatrix_generated_size_meets_minimum(
        self, dm_generator: DataMatrixGenerator, single_chz_code: str
    ):
        """Сгенерированный DataMatrix >= 22мм."""
        result = dm_generator.generate(single_chz_code, with_quiet_zone=False)

        assert result.width_mm >= LABEL.DATAMATRIX_MIN_MM
        assert result.height_mm >= LABEL.DATAMATRIX_MIN_MM

    def test_datamatrix_with_quiet_zone_size(
        self, dm_generator: DataMatrixGenerator, single_chz_code: str
    ):
        """DataMatrix с зоной покоя больше чем без неё."""
        without_qz = dm_generator.generate(single_chz_code, with_quiet_zone=False)
        with_qz = dm_generator.generate(single_chz_code, with_quiet_zone=True)

        assert with_qz.width_mm > without_qz.width_mm
        assert with_qz.height_mm > without_qz.height_mm

    def test_datamatrix_layout_config_basic_58x40(self):
        """В layout basic 58x40 DataMatrix размер >= 22мм."""
        config = LAYOUTS["basic"]["58x40"]
        dm_config = config["datamatrix"]

        assert dm_config["size"] >= 22, "DataMatrix в basic 58x40 должен быть >= 22мм"

    def test_datamatrix_layout_config_basic_58x30(self):
        """В layout basic 58x30 DataMatrix размер >= 22мм."""
        config = LAYOUTS["basic"]["58x30"]
        dm_config = config["datamatrix"]

        assert dm_config["size"] >= 22, "DataMatrix в basic 58x30 должен быть >= 22мм"

    def test_datamatrix_layout_config_basic_58x60(self):
        """В layout basic 58x60 DataMatrix размер >= 22мм."""
        config = LAYOUTS["basic"]["58x60"]
        dm_config = config["datamatrix"]

        assert dm_config["size"] >= 22, "DataMatrix в basic 58x60 должен быть >= 22мм"

    def test_datamatrix_layout_config_professional(self):
        """В layout professional DataMatrix размер >= 22мм."""
        config = LAYOUTS["professional"]["58x40"]
        dm_config = config["datamatrix"]

        assert dm_config["size"] >= 22, "DataMatrix в professional должен быть >= 22мм"

    def test_datamatrix_layout_config_extended(self):
        """В layout extended DataMatrix размер >= 22мм."""
        config = LAYOUTS["extended"]["58x40"]
        dm_config = config["datamatrix"]

        assert dm_config["size"] >= 22, "DataMatrix в extended должен быть >= 22мм"


# === Тесты генерации DataMatrix ===


class TestDataMatrixGeneration:
    """Генерация валидных DataMatrix кодов."""

    def test_generate_valid_datamatrix(
        self, dm_generator: DataMatrixGenerator, single_chz_code: str
    ):
        """Генерация DataMatrix из валидного кода."""
        result = dm_generator.generate(single_chz_code)

        assert isinstance(result, GeneratedDataMatrix)
        assert result.image is not None
        assert result.width_pixels > 0
        assert result.height_pixels > 0

    def test_generate_datamatrix_with_gs1_separators(self, dm_generator: DataMatrixGenerator):
        """Генерация DataMatrix с GS1 сепараторами (\\x1d)."""
        code_with_gs1 = "010467004977480221JNlMVsj\x1d93xxxx\x1d3103000150"
        result = dm_generator.generate(code_with_gs1)

        assert result.image is not None

    def test_datamatrix_too_short_code_raises(self, dm_generator: DataMatrixGenerator):
        """Слишком короткий код вызывает ValueError."""
        with pytest.raises(ValueError, match="короткий"):
            dm_generator.generate("12345")

    def test_datamatrix_empty_code_raises(self, dm_generator: DataMatrixGenerator):
        """Пустой код вызывает ValueError."""
        with pytest.raises(ValueError, match="короткий"):
            dm_generator.generate("")

    def test_generate_batch_valid_codes(
        self, dm_generator: DataMatrixGenerator, sample_chz_codes: list[str]
    ):
        """Пакетная генерация нескольких кодов."""
        results = dm_generator.generate_batch(sample_chz_codes)

        assert len(results) == len(sample_chz_codes)
        for result in results:
            assert isinstance(result, GeneratedDataMatrix)

    def test_generate_batch_skips_invalid_codes(self, dm_generator: DataMatrixGenerator):
        """Пакетная генерация пропускает невалидные коды."""
        codes = [
            "010467004977480221Valid\x1d93xxxx",
            "short",  # Невалидный
            "010467004977480221Another\x1d93yyyy",
        ]
        results = dm_generator.generate_batch(codes)

        assert len(results) == 2  # Только валидные


# === Тесты генерации PDF этикеток ===


class TestLabelGeneration:
    """Генерация PDF этикеток."""

    def test_generate_single_label_returns_valid_pdf(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация одной этикетки возвращает валидный PDF."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x40",
            layout="basic",
        )

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:5] == b"%PDF-", "Файл должен начинаться с %PDF-"

    def test_generate_multiple_labels(
        self, generator: LabelGenerator, sample_item: LabelItem, sample_chz_codes: list[str]
    ):
        """Генерация нескольких этикеток."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=sample_chz_codes,
            size="58x40",
            layout="basic",
        )

        assert pdf_bytes[:5] == b"%PDF-"
        # PDF должен быть больше чем для одной этикетки
        single_pdf = generator.generate(
            items=[sample_item],
            codes=[sample_chz_codes[0]],
            size="58x40",
            layout="basic",
        )
        assert len(pdf_bytes) > len(single_pdf)

    def test_generate_basic_layout_58x40(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация basic layout 58x40."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x40",
            layout="basic",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_basic_layout_58x30(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация basic layout 58x30."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x30",
            layout="basic",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_basic_layout_58x60(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация basic layout 58x60."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x60",
            layout="basic",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_professional_layout(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация professional layout."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x40",
            layout="professional",
            organization="ООО Тест",
            inn="1234567890",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_extended_layout(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация extended layout с кастомными строками."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x40",
            layout="extended",
            custom_lines=["Строка 1", "Строка 2", "Строка 3"],
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_demo_mode_works(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация в demo режиме работает."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x40",
            layout="basic",
            demo_mode=True,
        )

        assert pdf_bytes[:5] == b"%PDF-"
        # Demo PDF может быть чуть больше из-за водяного знака
        assert len(pdf_bytes) > 0

    def test_generate_invalid_size_fallback(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Невалидный размер fallback на 58x40."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="invalid",
            layout="basic",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_invalid_layout_fallback(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Невалидный layout fallback на basic."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x40",
            layout="invalid",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_professional_forces_58x40(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Professional layout форсирует размер 58x40."""
        # Даже если указан 58x30, professional должен использовать 58x40
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            size="58x30",  # Пытаемся указать другой размер
            layout="professional",
        )

        assert pdf_bytes[:5] == b"%PDF-"


# === Тесты режимов нумерации ===


class TestNumberingModes:
    """Режимы нумерации этикеток."""

    def test_numbering_none(
        self, generator: LabelGenerator, sample_item: LabelItem, sample_chz_codes: list[str]
    ):
        """Режим none — без нумерации."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=sample_chz_codes,
            numbering_mode="none",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_numbering_sequential(
        self, generator: LabelGenerator, sample_item: LabelItem, sample_chz_codes: list[str]
    ):
        """Режим sequential — последовательная нумерация."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=sample_chz_codes,
            numbering_mode="sequential",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_numbering_per_product(
        self, generator: LabelGenerator, sample_items: list[LabelItem], sample_chz_codes: list[str]
    ):
        """Режим per_product — нумерация для каждого товара отдельно."""
        pdf_bytes = generator.generate(
            items=sample_items,
            codes=sample_chz_codes,
            numbering_mode="per_product",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_numbering_continue(
        self, generator: LabelGenerator, sample_item: LabelItem, sample_chz_codes: list[str]
    ):
        """Режим continue — продолжение нумерации с указанного номера."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=sample_chz_codes,
            numbering_mode="continue",
            start_number=100,
        )

        assert pdf_bytes[:5] == b"%PDF-"


# === Тесты show флагов ===


class TestShowFlags:
    """Флаги отображения полей."""

    def test_generate_with_all_show_flags_enabled(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация со всеми включенными полями."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            show_article=True,
            show_size=True,
            show_color=True,
            show_name=True,
            show_organization=True,
            show_inn=True,
            show_country=True,
            show_composition=True,
            show_brand=True,
            organization="ООО Тест",
            inn="1234567890",
        )

        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_with_all_show_flags_disabled(
        self, generator: LabelGenerator, sample_item: LabelItem, single_chz_code: str
    ):
        """Генерация со всеми выключенными полями."""
        pdf_bytes = generator.generate(
            items=[sample_item],
            codes=[single_chz_code],
            show_article=False,
            show_size=False,
            show_color=False,
            show_name=False,
            show_organization=False,
            show_inn=False,
            show_country=False,
            show_composition=False,
            show_brand=False,
            show_chz_code_text=False,
        )

        assert pdf_bytes[:5] == b"%PDF-"


# === Тесты парсинга preflight ошибок ===


class TestPreflightErrorParsing:
    """Парсинг preflight ошибок с привязкой к полям."""

    def test_parse_name_error(self):
        """Ошибка названия товара."""
        result = parse_preflight_error("Название слишком длинное")

        assert result.field_id == "name"
        assert result.suggestion is not None

    def test_parse_organization_error(self):
        """Ошибка организации."""
        result = parse_preflight_error("Организация не помещается")

        assert result.field_id == "organization"

    def test_parse_address_error(self):
        """Ошибка адреса."""
        result = parse_preflight_error("Адрес слишком длинный")

        assert result.field_id == "address"

    def test_parse_inn_error(self):
        """Ошибка ИНН."""
        result = parse_preflight_error("ИНН некорректный")

        assert result.field_id == "inn"

    def test_parse_size_color_error(self):
        """Ошибка размер/цвет."""
        result = parse_preflight_error("Размер/цвет слишком длинный")

        assert result.field_id == "size"  # Приоритет размер

    def test_parse_generic_error(self):
        """Общая ошибка без привязки к полю."""
        result = parse_preflight_error("Текстовый блок переполнен")

        assert result.field_id is None
        assert result.suggestion is not None


# === Тесты констант ===


class TestConstants:
    """Проверка констант и конфигурации."""

    def test_label_sizes_defined(self):
        """Все размеры этикеток определены."""
        assert "58x40" in LABEL_SIZES
        assert "58x30" in LABEL_SIZES
        assert "58x60" in LABEL_SIZES

    def test_layouts_defined(self):
        """Все layouts определены."""
        assert "basic" in LAYOUTS
        assert "professional" in LAYOUTS
        assert "extended" in LAYOUTS

    def test_basic_layout_has_all_sizes(self):
        """Basic layout поддерживает все размеры."""
        assert "58x40" in LAYOUTS["basic"]
        assert "58x30" in LAYOUTS["basic"]
        assert "58x60" in LAYOUTS["basic"]

    def test_professional_layout_only_58x40(self):
        """Professional layout только для 58x40."""
        assert "58x40" in LAYOUTS["professional"]
        # Professional НЕ должен иметь других размеров
        assert len(LAYOUTS["professional"]) == 1

    def test_extended_layout_only_58x40(self):
        """Extended layout только для 58x40."""
        assert "58x40" in LAYOUTS["extended"]
        assert len(LAYOUTS["extended"]) == 1

    def test_dpi_is_203(self):
        """DPI = 203 (стандарт термопринтеров)."""
        assert LABEL.DPI == 203
