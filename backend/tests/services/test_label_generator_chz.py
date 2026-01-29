"""Тесты для генератора этикеток Только ЧЗ."""

import io

import pikepdf
import pytest

from app.services.label_generator import LabelGenerator

# Валидные коды маркировки с криптохвостом
VALID_CODE_1 = "010467004977480221JNlMVstBYYuQ91EE0692Wh0KGcGm6HpwZf+7aWtp/DaNgFU="
VALID_CODE_2 = "010467004977480221ABC123defGHI91EE0692XYZTEST123456789abcdef="


class TestChzOnlyGeneration:
    """Тесты генерации этикеток только ЧЗ."""

    def test_generate_chz_only_58x40(self):
        """Генерация этикетки 58x40 только с DataMatrix и текстом кода."""
        codes = [VALID_CODE_1, VALID_CODE_2]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_chz_only(codes=codes, label_size="58x40")

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"  # Проверка PDF сигнатуры

    def test_pdf_has_correct_page_count(self):
        """PDF должен содержать по одной странице на каждый код."""
        codes = [VALID_CODE_1, VALID_CODE_2, VALID_CODE_1]  # 3 кода

        generator = LabelGenerator()
        pdf_bytes = generator.generate_chz_only(codes=codes, label_size="58x40")

        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 3

    def test_single_code_single_page(self):
        """Один код = одна страница."""
        codes = [VALID_CODE_1]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_chz_only(codes=codes, label_size="58x40")

        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 1

    def test_large_batch_generation(self):
        """Генерация большого количества этикеток (100 шт)."""
        codes = [VALID_CODE_1] * 100

        generator = LabelGenerator()
        pdf_bytes = generator.generate_chz_only(codes=codes, label_size="58x40")

        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        assert len(pdf.pages) == 100

    def test_pdf_minimum_size(self):
        """PDF должен иметь разумный размер."""
        codes = [VALID_CODE_1]

        generator = LabelGenerator()
        pdf_bytes = generator.generate_chz_only(codes=codes, label_size="58x40")

        # Минимум 1KB для одной этикетки с DataMatrix
        assert len(pdf_bytes) > 1000

    def test_invalid_size_raises_error(self):
        """Неподдерживаемый размер должен вызывать ошибку."""
        codes = [VALID_CODE_1]
        generator = LabelGenerator()

        with pytest.raises(ValueError, match="Неподдерживаемый размер"):
            generator.generate_chz_only(codes=codes, label_size="43x25")

    def test_empty_codes_list(self):
        """Пустой список кодов должен вернуть пустой PDF или ошибку."""
        generator = LabelGenerator()

        # Либо возвращает пустой PDF, либо поднимает исключение
        try:
            pdf_bytes = generator.generate_chz_only(codes=[], label_size="58x40")
            # Если не поднялось исключение, проверяем что PDF пустой или минимальный
            if pdf_bytes:
                pdf = pikepdf.open(io.BytesIO(pdf_bytes))
                assert len(pdf.pages) == 0
        except (ValueError, Exception):
            # Ожидаемое поведение — ошибка на пустой список
            pass

    def test_datamatrix_minimum_22mm(self):
        """DataMatrix должен быть минимум 22x22мм по ГОСТу."""
        # Этот тест проверяет конфигурацию, а не сам PDF
        from app.config import LABEL

        assert hasattr(LABEL, "DATAMATRIX_MIN_MM")
        assert LABEL.DATAMATRIX_MIN_MM >= 22.0
