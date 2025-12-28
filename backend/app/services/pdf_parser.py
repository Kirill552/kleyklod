"""
Парсер PDF файлов от Wildberries.

Извлекает изображения этикеток из PDF.
"""

import io
from dataclasses import dataclass

import pypdfium2 as pdfium
from PIL import Image, ImageOps

from app.config import LABEL


@dataclass
class ParsedPDF:
    """Результат парсинга PDF."""

    pages: list[Image.Image]
    page_count: int
    original_width: int
    original_height: int


class PDFParser:
    """
    Парсер PDF файлов с этикетками WB.

    Использует pypdfium2 для быстрого рендеринга страниц.
    """

    def __init__(self, dpi: int = LABEL.DPI):
        """
        Инициализация парсера.

        Args:
            dpi: Разрешение для рендеринга (по умолчанию 203 DPI)
        """
        self.dpi = dpi
        # Масштаб для pypdfium2 (72 DPI базовое разрешение PDF)
        self.scale = dpi / 72.0

    def _auto_crop(self, img: Image.Image, margin: int = 10) -> Image.Image:
        """
        Автоматическое кадрирование изображения по контенту.

        WB генерирует PDF на A4, но этикетка маленькая в углу.
        Эта функция находит и вырезает только область с контентом.

        Args:
            img: Исходное изображение
            margin: Отступ от краёв контента в пикселях

        Returns:
            Обрезанное изображение
        """
        # Конвертируем в grayscale
        gray = img.convert("L")

        # Инвертируем (белый фон → чёрный, контент → белый)
        inverted = ImageOps.invert(gray)

        # Находим bounding box не-белых пикселей
        bbox = inverted.getbbox()

        if bbox is None:
            # Нет контента — возвращаем как есть
            return img

        # Добавляем отступы
        x1, y1, x2, y2 = bbox
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(img.width, x2 + margin)
        y2 = min(img.height, y2 + margin)

        # Вырезаем область с контентом
        return img.crop((x1, y1, x2, y2))

    def parse(self, pdf_bytes: bytes) -> ParsedPDF:
        """
        Парсинг PDF и извлечение изображений страниц.

        Args:
            pdf_bytes: Содержимое PDF файла

        Returns:
            ParsedPDF с изображениями всех страниц

        Raises:
            ValueError: Если PDF повреждён или защищён
        """
        try:
            pdf = pdfium.PdfDocument(pdf_bytes)
        except Exception as e:
            raise ValueError(f"Не удалось открыть PDF: {str(e)}")

        page_count = len(pdf)
        if page_count == 0:
            raise ValueError("PDF файл пустой")

        pages: list[Image.Image] = []
        original_width = 0
        original_height = 0

        for i in range(page_count):
            page = pdf[i]

            # Получаем размер страницы (в пунктах, 1 пункт = 1/72 дюйма)
            width_pt = page.get_width()
            height_pt = page.get_height()

            if i == 0:
                # Сохраняем оригинальные размеры первой страницы
                original_width = int(width_pt * self.scale)
                original_height = int(height_pt * self.scale)

            # Рендерим страницу в изображение (высокое разрешение для качества)
            render_scale = 300 / 72  # 300 DPI для рендера
            bitmap = page.render(scale=render_scale)
            pil_image = bitmap.to_pil()

            # Конвертируем в RGB если нужно
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Auto-crop: вырезаем только область с контентом
            pil_image = self._auto_crop(pil_image)

            pages.append(pil_image)

        pdf.close()

        return ParsedPDF(
            pages=pages,
            page_count=page_count,
            original_width=original_width,
            original_height=original_height,
        )

    def get_page_count(self, pdf_bytes: bytes) -> int:
        """
        Быстрое получение количества страниц без полного парсинга.

        Args:
            pdf_bytes: Содержимое PDF файла

        Returns:
            Количество страниц
        """
        try:
            pdf = pdfium.PdfDocument(pdf_bytes)
            count = len(pdf)
            pdf.close()
            return count
        except Exception as e:
            raise ValueError(f"Не удалось открыть PDF: {str(e)}")

    def extract_single_page(self, pdf_bytes: bytes, page_index: int = 0) -> Image.Image:
        """
        Извлечение одной страницы из PDF.

        Args:
            pdf_bytes: Содержимое PDF файла
            page_index: Индекс страницы (начиная с 0)

        Returns:
            PIL Image страницы
        """
        try:
            pdf = pdfium.PdfDocument(pdf_bytes)
        except Exception as e:
            raise ValueError(f"Не удалось открыть PDF: {str(e)}")

        if page_index >= len(pdf):
            pdf.close()
            raise ValueError(f"Страница {page_index} не существует. Всего страниц: {len(pdf)}")

        page = pdf[page_index]
        bitmap = page.render(scale=self.scale)
        pil_image = bitmap.to_pil()

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        pdf.close()
        return pil_image


def images_to_pdf(images: list[Image.Image], dpi: int = LABEL.DPI) -> bytes:
    """
    Конвертация списка изображений в PDF с точным размером страницы.

    Использует img2pdf для lossless конвертации с правильными размерами.
    Размер страницы = pixels / dpi (в мм).

    Args:
        images: Список PIL изображений
        dpi: Разрешение (по умолчанию 203 DPI для термопринтеров)

    Returns:
        Байты PDF файла
    """
    if not images:
        raise ValueError("Список изображений пустой")

    import img2pdf

    # Конвертируем PIL изображения в JPEG байты с DPI
    # JPEG вместо PNG — нет прозрачности, img2pdf работает корректнее
    jpeg_bytes_list = []
    for i, img in enumerate(images):
        if img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        # JPEG с качеством 95% и DPI в EXIF
        img.save(buf, format="JPEG", quality=95, dpi=(dpi, dpi))
        jpeg_bytes = buf.getvalue()
        jpeg_bytes_list.append(jpeg_bytes)

    # img2pdf конвертирует JPEG напрямую без перекодирования
    import img2pdf

    pdf_bytes = img2pdf.convert(jpeg_bytes_list)

    return pdf_bytes
