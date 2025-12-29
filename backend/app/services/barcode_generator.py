"""
Генератор штрихкодов EAN-13 и Code128.

Создаёт изображения штрихкодов из цифровых строк для этикеток WB.
Используется для генерации PDF с этикетками из Excel файла.
"""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.config import LABEL


@dataclass
class GeneratedBarcode:
    """Результат генерации штрихкода."""

    image: Image.Image
    width_pixels: int
    height_pixels: int
    width_mm: float
    height_mm: float
    barcode_type: str  # "ean13" или "code128"


class BarcodeGenerator:
    """
    Генератор штрихкодов из цифр.

    Поддерживает:
    - EAN-13 для 13-значных баркодов (стандарт WB)
    - Code128 для других длин (универсальный)
    """

    def __init__(
        self,
        dpi: int = LABEL.DPI,
    ):
        """
        Инициализация генератора.

        Args:
            dpi: Разрешение (по умолчанию 203 DPI для термопринтеров)
        """
        self.dpi = dpi

    def generate(
        self,
        digits: str,
        width_mm: float = 40.0,
        height_mm: float = 15.0,
        barcode_format: str = "auto",
    ) -> GeneratedBarcode:
        """
        Генерирует штрихкод из цифровой строки.

        Args:
            digits: Цифры баркода (без пробелов и лишних символов)
            width_mm: Ширина штрихкода в мм
            height_mm: Высота штрихкода в мм
            barcode_format: Формат ("auto", "ean13", "code128")

        Returns:
            GeneratedBarcode с изображением

        Raises:
            ValueError: Если код невалидный
        """
        try:
            from barcode import EAN13, Code128
            from barcode.writer import ImageWriter
        except ImportError:
            raise ImportError(
                "python-barcode не установлен. Установите: pip install python-barcode[images]"
            )

        # Очищаем строку от лишних символов
        digits = self._clean_digits(digits)

        if not digits:
            raise ValueError("Пустой баркод")

        # Определяем формат автоматически
        if barcode_format == "auto":
            barcode_format = self._detect_format(digits)

        # Генерируем штрихкод
        buffer = BytesIO()
        writer = ImageWriter()

        # Настройки для ImageWriter — оптимизировано для читаемости
        options = {
            "module_width": 0.33,  # Ширина модуля (бара) в мм — увеличено для сканеров
            "module_height": height_mm,  # Высота баров
            "quiet_zone": 2.5,  # Зона покоя по бокам
            "font_size": 10,  # Размер шрифта под кодом — увеличено для читаемости
            "text_distance": 1.5,  # Расстояние до текста — уменьшено
            "write_text": True,  # Писать цифры под штрихкодом
            "dpi": self.dpi,
        }

        if barcode_format == "ean13":
            # EAN-13: строго 13 цифр (12 + контрольная)
            if len(digits) == 12:
                # Без контрольной суммы — barcode сам добавит
                barcode = EAN13(digits, writer=writer)
            elif len(digits) == 13:
                # С контрольной суммой — проверяем
                barcode = EAN13(digits[:12], writer=writer)
            else:
                raise ValueError(f"EAN-13 требует 12-13 цифр, получено: {len(digits)}")
        else:
            # Code128: любая длина
            barcode = Code128(digits, writer=writer)

        # Генерируем в буфер
        barcode.write(buffer, options=options)
        buffer.seek(0)

        # Читаем как PIL Image
        img = Image.open(buffer)
        img = img.convert("RGB")

        # Масштабируем до нужной ширины
        target_width_px = LABEL.mm_to_pixels(width_mm)
        aspect = img.height / img.width
        target_height_px = int(target_width_px * aspect)

        img_resized = img.resize(
            (target_width_px, target_height_px),
            Image.Resampling.LANCZOS,
        )

        return GeneratedBarcode(
            image=img_resized,
            width_pixels=img_resized.width,
            height_pixels=img_resized.height,
            width_mm=LABEL.pixels_to_mm(img_resized.width),
            height_mm=LABEL.pixels_to_mm(img_resized.height),
            barcode_type=barcode_format,
        )

    def generate_batch(
        self,
        barcodes: list[str],
        width_mm: float = 40.0,
        height_mm: float = 15.0,
    ) -> list[GeneratedBarcode | None]:
        """
        Генерация нескольких штрихкодов.

        Args:
            barcodes: Список баркодов (цифровые строки)
            width_mm: Ширина штрихкода в мм
            height_mm: Высота штрихкода в мм

        Returns:
            Список GeneratedBarcode (None для невалидных кодов)
        """
        results: list[GeneratedBarcode | None] = []

        for barcode in barcodes:
            try:
                result = self.generate(barcode, width_mm, height_mm)
                results.append(result)
            except ValueError:
                # Невалидный код — пропускаем (None)
                results.append(None)

        return results

    def _clean_digits(self, digits: str) -> str:
        """Очистка строки от лишних символов."""
        # Убираем пробелы, тире, переносы
        cleaned = digits.strip().replace(" ", "").replace("-", "").replace("\n", "")
        # Оставляем только цифры
        return "".join(c for c in cleaned if c.isdigit())

    def _detect_format(self, digits: str) -> str:
        """
        Определение формата штрихкода по длине.

        Args:
            digits: Очищенная строка цифр

        Returns:
            "ean13" или "code128"
        """
        length = len(digits)

        # EAN-13: 12 или 13 цифр
        if length in (12, 13):
            return "ean13"

        # Для остальных — Code128
        return "code128"
