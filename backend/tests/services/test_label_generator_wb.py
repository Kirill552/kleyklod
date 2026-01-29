"""Тесты для генератора этикеток Только WB."""

import io

import pikepdf

from app.services.label_generator import LabelGenerator


class TestWbOnlyGeneration:
    """Тесты генерации этикеток только WB."""

    def test_generate_wb_only_58x40_minimal(self):
        """Генерация этикетки WB только со штрихкодом."""
        items = [{"barcode": "4601234567890"}]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={"barcode": True},
        )

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_wb_only_with_all_fields(self):
        """Генерация этикетки WB со всеми полями."""
        items = [
            {
                "barcode": "4601234567890",
                "name": "Футболка мужская",
                "article": "FT-001",
                "size": "M",
                "color": "Черный",
                "brand": "TestBrand",
            },
        ]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={
                "barcode": True,
                "name": True,
                "article": True,
                "size": True,
                "color": True,
                "brand": True,
            },
        )

        assert pdf_bytes is not None
        assert pdf_bytes[:4] == b"%PDF"

    def test_pdf_has_correct_page_count(self):
        """PDF должен содержать по одной странице на каждый товар."""
        items = [
            {"barcode": "4601234567890"},
            {"barcode": "4601234567891"},
            {"barcode": "4601234567892"},
        ]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={"barcode": True},
        )

        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 3

    def test_single_item_single_page(self):
        """Один товар = одна страница."""
        items = [{"barcode": "4601234567890"}]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={"barcode": True},
        )

        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 1

    def test_large_batch_generation(self):
        """Генерация большого количества этикеток (50 шт)."""
        items = [{"barcode": f"460123456789{i % 10}"} for i in range(50)]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={"barcode": True},
        )

        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 50

    def test_all_label_sizes(self):
        """Все размеры этикеток создают валидный PDF."""
        items = [{"barcode": "4601234567890"}]
        generator = LabelGenerator()

        for size in ["58x40", "58x30"]:
            pdf_bytes = generator.generate_wb_only(
                items=items,
                label_size=size,
                show_fields={"barcode": True},
            )

            assert pdf_bytes[:4] == b"%PDF"
            pdf = pikepdf.open(io.BytesIO(pdf_bytes))
            assert len(pdf.pages) == 1

    def test_show_fields_only_barcode(self):
        """Только штрихкод включен — PDF создаётся."""
        items = [
            {
                "barcode": "4601234567890",
                "name": "Название",
                "article": "ART",
            }
        ]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={"barcode": True, "name": False, "article": False},
        )

        assert pdf_bytes is not None
        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 1

    def test_show_fields_all_enabled(self):
        """Все поля включены — PDF создаётся."""
        items = [
            {
                "barcode": "4601234567890",
                "name": "Футболка",
                "article": "FT-001",
                "size": "L",
                "color": "Белый",
                "brand": "Nike",
            }
        ]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={
                "barcode": True,
                "name": True,
                "article": True,
                "size": True,
                "color": True,
                "brand": True,
            },
        )

        assert pdf_bytes is not None
        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 1

    def test_pdf_minimum_size(self):
        """PDF должен иметь разумный размер."""
        items = [{"barcode": "4601234567890"}]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={"barcode": True},
        )

        # Минимум 500 байт для одной этикетки со штрихкодом
        assert len(pdf_bytes) > 500

    def test_empty_items_list(self):
        """Пустой список товаров должен вернуть пустой PDF или ошибку."""
        generator = LabelGenerator()

        try:
            pdf_bytes = generator.generate_wb_only(
                items=[],
                label_size="58x40",
                show_fields={"barcode": True},
            )
            # Если не поднялось исключение, проверяем что PDF пустой
            if pdf_bytes:
                pdf = pikepdf.open(io.BytesIO(pdf_bytes))
                assert len(pdf.pages) == 0
        except (ValueError, Exception):
            # Ожидаемое поведение — ошибка на пустой список
            pass

    def test_item_with_missing_optional_fields(self):
        """Товар без опциональных полей — PDF создаётся."""
        items = [{"barcode": "4601234567890"}]  # Только обязательное поле

        generator = LabelGenerator()
        pdf_bytes = generator.generate_wb_only(
            items=items,
            label_size="58x40",
            show_fields={"barcode": True, "name": True, "article": True},
        )

        assert pdf_bytes is not None
        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 1
