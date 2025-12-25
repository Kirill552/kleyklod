"""
Парсер PDF файлов от Wildberries.

Извлекает изображения этикеток из PDF.
"""

import io
from dataclasses import dataclass

import pypdfium2 as pdfium
from PIL import Image

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

            # Рендерим страницу в изображение
            bitmap = page.render(scale=self.scale)
            pil_image = bitmap.to_pil()

            # Конвертируем в RGB если нужно
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

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
    Конвертация списка изображений в PDF.

    Args:
        images: Список PIL изображений
        dpi: Разрешение для метаданных PDF

    Returns:
        Байты PDF файла
    """
    if not images:
        raise ValueError("Список изображений пустой")

    # Конвертируем все изображения в RGB
    rgb_images = []
    for img in images:
        if img.mode != "RGB":
            img = img.convert("RGB")
        rgb_images.append(img)

    # Сохраняем в PDF
    output = io.BytesIO()

    # Первое изображение как база, остальные добавляем
    first_image = rgb_images[0]
    if len(rgb_images) > 1:
        first_image.save(
            output,
            format="PDF",
            save_all=True,
            append_images=rgb_images[1:],
            resolution=dpi,
        )
    else:
        first_image.save(output, format="PDF", resolution=dpi)

    output.seek(0)
    return output.getvalue()
