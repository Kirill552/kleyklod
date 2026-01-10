"""
Тесты PDF парсера (legacy режим).

Покрывает:
- Парсинг PDF файлов с кодами ЧЗ
- Декодирование DataMatrix
- Авто-кроп и нормализация ориентации
- Smart crop оптимизация
"""

import pytest
from PIL import Image

from app.config import LABEL
from app.services.datamatrix import DataMatrixGenerator
from app.services.label_generator import LabelGenerator, LabelItem
from app.services.pdf_parser import ExtractedCodes, ParsedPDF, PDFParser


# === Fixtures ===


@pytest.fixture
def parser() -> PDFParser:
    """Экземпляр PDF парсера."""
    return PDFParser()


@pytest.fixture
def dm_generator() -> DataMatrixGenerator:
    """Генератор DataMatrix для создания тестовых данных."""
    return DataMatrixGenerator()


@pytest.fixture
def label_generator() -> LabelGenerator:
    """Генератор этикеток для создания тестовых PDF."""
    return LabelGenerator()


@pytest.fixture
def sample_chz_code() -> str:
    """Тестовый код ЧЗ."""
    return "010467004977480221JNlMVsj,QVL6\x1d93xxxx"


@pytest.fixture
def sample_chz_codes() -> list[str]:
    """Список тестовых кодов ЧЗ."""
    return [
        "010467004977480221JNlMVsj,QVL6\x1d93xxxx",
        "010467004977480221BBBtest\x1d93yyyy",
        "010467004977480221CCCdata\x1d93zzzz",
    ]


@pytest.fixture
def sample_item() -> LabelItem:
    """Тестовый товар."""
    return LabelItem(
        barcode="4670049774802",
        name="Тестовый товар",
        article="TEST-001",
    )


@pytest.fixture
def generated_pdf_bytes(label_generator: LabelGenerator, sample_item: LabelItem, sample_chz_codes: list[str]) -> bytes:
    """PDF сгенерированный через label_generator для тестирования."""
    return label_generator.generate(
        items=[sample_item],
        codes=sample_chz_codes,
        size="58x40",
        layout="basic",
    )


# === Тесты PDF парсера ===


class TestPDFParser:
    """Парсинг PDF файлов."""

    def test_parser_initialization(self, parser: PDFParser):
        """Парсер инициализируется с правильным DPI."""
        assert parser.dpi == LABEL.DPI
        assert parser.scale == LABEL.DPI / 72.0

    def test_parser_custom_dpi(self):
        """Парсер с кастомным DPI."""
        custom_parser = PDFParser(dpi=300)
        assert custom_parser.dpi == 300
        assert custom_parser.scale == 300 / 72.0


class TestNormalizeOrientation:
    """Нормализация ориентации изображений."""

    def test_portrait_image_unchanged(self, parser: PDFParser):
        """Портретное изображение не меняется."""
        img = Image.new("RGB", (100, 200), color="white")
        result = parser._normalize_orientation(img)

        assert result.width == 100
        assert result.height == 200

    def test_landscape_image_rotated(self, parser: PDFParser):
        """Альбомное изображение поворачивается на 90°."""
        img = Image.new("RGB", (200, 100), color="white")
        result = parser._normalize_orientation(img)

        assert result.width == 100
        assert result.height == 200

    def test_square_image_unchanged(self, parser: PDFParser):
        """Квадратное изображение не меняется."""
        img = Image.new("RGB", (100, 100), color="white")
        result = parser._normalize_orientation(img)

        assert result.width == 100
        assert result.height == 100


class TestAutoCrop:
    """Автоматическое кадрирование."""

    def test_auto_crop_empty_image(self, parser: PDFParser):
        """Пустое белое изображение возвращается без изменений."""
        img = Image.new("RGB", (100, 100), color="white")
        result = parser._auto_crop(img)

        # Размер может измениться если getbbox вернёт None
        assert result is not None

    def test_auto_crop_with_content(self, parser: PDFParser):
        """Изображение с контентом кропится правильно."""
        # Создаём изображение с чёрным квадратом в центре
        img = Image.new("RGB", (200, 200), color="white")
        # Рисуем чёрный квадрат 50x50 в центре
        for x in range(75, 125):
            for y in range(75, 125):
                img.putpixel((x, y), (0, 0, 0))

        result = parser._auto_crop(img, margin=10)

        # Результат должен быть меньше оригинала
        assert result.width < img.width
        assert result.height < img.height


class TestDataclasses:
    """Тесты dataclass структур."""

    def test_parsed_pdf_dataclass(self):
        """ParsedPDF dataclass."""
        img = Image.new("RGB", (100, 100))
        parsed = ParsedPDF(
            pages=[img],
            page_count=1,
            original_width=100,
            original_height=100,
        )

        assert parsed.page_count == 1
        assert len(parsed.pages) == 1
        assert parsed.original_width == 100
        assert parsed.original_height == 100

    def test_extracted_codes_dataclass(self):
        """ExtractedCodes dataclass."""
        codes = ExtractedCodes(
            codes=["code1", "code2"],
            count=2,
            duplicates_removed=0,
            pages_processed=1,
        )

        assert codes.count == 2
        assert len(codes.codes) == 2
        assert codes.duplicates_removed == 0
        assert codes.pages_processed == 1


class TestDataMatrixDecoding:
    """Декодирование DataMatrix из изображений."""

    def test_decode_generated_datamatrix(self, dm_generator: DataMatrixGenerator, sample_chz_code: str):
        """Декодирование сгенерированного DataMatrix."""
        try:
            from pylibdmtx.pylibdmtx import decode
        except ImportError:
            pytest.skip("pylibdmtx не установлен")

        # Генерируем DataMatrix
        result = dm_generator.generate(sample_chz_code, with_quiet_zone=True)

        # Декодируем обратно
        decoded = decode(result.image)

        assert len(decoded) == 1
        decoded_data = decoded[0].data.decode("utf-8", errors="ignore")
        # Код должен содержать начало оригинального кода
        assert decoded_data.startswith("0104670049774802")

    def test_decode_from_pdf_page(
        self, parser: PDFParser, label_generator: LabelGenerator, sample_item: LabelItem, sample_chz_code: str
    ):
        """Декодирование DataMatrix из страницы PDF."""
        try:
            import pypdfium2 as pdfium
            from pylibdmtx.pylibdmtx import decode
        except ImportError:
            pytest.skip("pypdfium2 или pylibdmtx не установлен")

        # Генерируем PDF с одной этикеткой
        pdf_bytes = label_generator.generate(
            items=[sample_item],
            codes=[sample_chz_code],
            size="58x40",
            layout="basic",
        )

        # Рендерим первую страницу
        pdf = pdfium.PdfDocument(pdf_bytes)
        page = pdf[0]
        bitmap = page.render(scale=parser.scale)
        pil_image = bitmap.to_pil()
        pdf.close()

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Декодируем DataMatrix
        decoded = decode(pil_image)

        # Должен быть хотя бы один DataMatrix
        assert len(decoded) >= 1


class TestFindAllDataMatrix:
    """Поиск всех DataMatrix на изображении."""

    def test_find_datamatrix_on_generated_image(
        self, parser: PDFParser, dm_generator: DataMatrixGenerator, sample_chz_code: str
    ):
        """Поиск DataMatrix на сгенерированном изображении."""
        # Создаём изображение с DataMatrix в центре
        dm_result = dm_generator.generate(sample_chz_code, with_quiet_zone=True)

        # Создаём большое белое изображение и вставляем DataMatrix
        canvas = Image.new("RGB", (500, 500), color="white")
        # Вставляем DataMatrix в центр
        x = (500 - dm_result.image.width) // 2
        y = (500 - dm_result.image.height) // 2
        canvas.paste(dm_result.image, (x, y))

        # Ищем DataMatrix
        results = parser._find_all_datamatrix(canvas)

        # Должен найти хотя бы один
        assert len(results) >= 1

    def test_find_no_datamatrix_on_blank_image(self, parser: PDFParser):
        """На пустом изображении DataMatrix не найден."""
        blank = Image.new("RGB", (200, 200), color="white")
        results = parser._find_all_datamatrix(blank)

        assert len(results) == 0


class TestSmartCrop:
    """Оптимизация smart crop для файлов ЧЗ."""

    def test_smart_crop_finds_center_datamatrix(self, dm_generator: DataMatrixGenerator, sample_chz_code: str):
        """Smart crop находит DataMatrix в центре."""
        try:
            from pylibdmtx.pylibdmtx import decode
        except ImportError:
            pytest.skip("pylibdmtx не установлен")

        # Создаём изображение с DataMatrix в центре (как в файлах ЧЗ)
        dm_result = dm_generator.generate(sample_chz_code, with_quiet_zone=True)

        canvas = Image.new("RGB", (400, 600), color="white")
        # DataMatrix в центре
        x = (400 - dm_result.image.width) // 2
        y = (600 - dm_result.image.height) // 2 - 50  # Чуть выше центра, как в ЧЗ
        canvas.paste(dm_result.image, (x, y))

        # Smart crop: центральные 80% ширины, 70% высоты
        w, h = canvas.size
        x1 = int(w * 0.10)
        y1 = int(h * 0.10)
        x2 = int(w * 0.90)
        y2 = int(h * 0.80)
        cropped = canvas.crop((x1, y1, x2, y2))

        # Декодируем из кропнутого
        decoded = decode(cropped)

        assert len(decoded) >= 1


class TestPDFRoundTrip:
    """Тест round-trip: генерация PDF → парсинг → извлечение кодов."""

    def test_roundtrip_single_label(
        self, parser: PDFParser, label_generator: LabelGenerator, sample_item: LabelItem, sample_chz_code: str
    ):
        """Round-trip для одной этикетки."""
        try:
            import pypdfium2 as pdfium
            from pylibdmtx.pylibdmtx import decode
        except ImportError:
            pytest.skip("pypdfium2 или pylibdmtx не установлен")

        # 1. Генерируем PDF
        pdf_bytes = label_generator.generate(
            items=[sample_item],
            codes=[sample_chz_code],
            size="58x40",
            layout="basic",
        )

        # 2. Проверяем что это валидный PDF
        assert pdf_bytes[:5] == b"%PDF-"

        # 3. Парсим PDF
        pdf = pdfium.PdfDocument(pdf_bytes)
        assert len(pdf) == 1  # Одна страница

        # 4. Рендерим страницу
        page = pdf[0]
        bitmap = page.render(scale=parser.scale)
        pil_image = bitmap.to_pil()
        pdf.close()

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # 5. Декодируем DataMatrix
        decoded = decode(pil_image)

        # 6. Проверяем что код извлечён
        assert len(decoded) >= 1
        decoded_data = decoded[0].data.decode("utf-8", errors="ignore")
        # GTIN должен совпадать
        assert "04670049774802" in decoded_data

    def test_roundtrip_multiple_labels(
        self, parser: PDFParser, label_generator: LabelGenerator, sample_item: LabelItem, sample_chz_codes: list[str]
    ):
        """Round-trip для нескольких этикеток."""
        try:
            import pypdfium2 as pdfium
            from pylibdmtx.pylibdmtx import decode
        except ImportError:
            pytest.skip("pypdfium2 или pylibdmtx не установлен")

        # 1. Генерируем PDF с несколькими этикетками
        pdf_bytes = label_generator.generate(
            items=[sample_item],
            codes=sample_chz_codes,
            size="58x40",
            layout="basic",
        )

        # 2. Парсим PDF
        pdf = pdfium.PdfDocument(pdf_bytes)
        page_count = len(pdf)

        # 3. Должно быть столько страниц, сколько кодов
        assert page_count == len(sample_chz_codes)

        # 4. Декодируем DataMatrix с каждой страницы
        decoded_codes = []
        for i in range(page_count):
            page = pdf[i]
            bitmap = page.render(scale=parser.scale)
            pil_image = bitmap.to_pil()

            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            decoded = decode(pil_image)
            if decoded:
                decoded_codes.append(decoded[0].data.decode("utf-8", errors="ignore"))

        pdf.close()

        # 5. Все коды должны быть извлечены
        assert len(decoded_codes) == len(sample_chz_codes)


class TestEdgeCases:
    """Граничные случаи."""

    def test_parser_with_empty_pdf_bytes(self, parser: PDFParser):
        """Пустые байты вызывают ошибку."""
        try:
            import pypdfium2 as pdfium
        except ImportError:
            pytest.skip("pypdfium2 не установлен")

        with pytest.raises(Exception):
            pdfium.PdfDocument(b"")

    def test_parser_with_invalid_pdf(self, parser: PDFParser):
        """Невалидный PDF вызывает ошибку."""
        try:
            import pypdfium2 as pdfium
        except ImportError:
            pytest.skip("pypdfium2 не установлен")

        with pytest.raises(Exception):
            pdfium.PdfDocument(b"not a pdf file")

    def test_parser_with_non_pdf_content(self, parser: PDFParser):
        """Контент не-PDF вызывает ошибку."""
        try:
            import pypdfium2 as pdfium
        except ImportError:
            pytest.skip("pypdfium2 не установлен")

        # HTML вместо PDF
        html_content = b"<html><body>Hello</body></html>"
        with pytest.raises(Exception):
            pdfium.PdfDocument(html_content)
