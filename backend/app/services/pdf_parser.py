"""
Парсер PDF файлов от Wildberries.

Извлекает изображения этикеток из PDF.
Поддерживает авто-разделение A4 PDF с несколькими этикетками.
"""

import io
import logging
from dataclasses import dataclass

import pypdfium2 as pdfium
from PIL import Image, ImageOps

from app.config import LABEL

logger = logging.getLogger(__name__)


@dataclass
class ParsedPDF:
    """Результат парсинга PDF."""

    pages: list[Image.Image]
    page_count: int
    original_width: int
    original_height: int


@dataclass
class ExtractedCodes:
    """Результат извлечения кодов DataMatrix из PDF."""

    codes: list[str]
    count: int
    duplicates_removed: int
    pages_processed: int


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

    def _normalize_orientation(self, img: Image.Image) -> Image.Image:
        """
        Нормализация ориентации: альбомная → портретная.

        Некоторые PDF от WB/ЧЗ приходят в альбомной ориентации,
        что ломает объединение с портретными этикетками.

        Args:
            img: Исходное изображение

        Returns:
            Изображение в портретной ориентации
        """
        if img.width > img.height:
            # Альбомная ориентация → поворачиваем на 90° против часовой
            return img.rotate(90, expand=True)
        return img

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

    def _find_all_datamatrix(self, img: Image.Image) -> list[tuple[str, tuple[int, int, int, int]]]:
        """
        Поиск всех DataMatrix кодов на изображении с их координатами.

        Args:
            img: PIL Image страницы

        Returns:
            Список кортежей (decoded_data, (left, top, width, height))
        """
        try:
            from pylibdmtx.pylibdmtx import decode

            results = decode(img)
            datamatrix_list = []

            for result in results:
                data = result.data.decode("utf-8", errors="ignore")
                # rect — это namedtuple с полями left, top, width, height
                rect = result.rect
                bbox = (rect.left, rect.top, rect.width, rect.height)
                datamatrix_list.append((data, bbox))

            logger.debug(f"Найдено DataMatrix на странице: {len(datamatrix_list)}")
            return datamatrix_list

        except ImportError:
            logger.warning("pylibdmtx не установлен, авто-разделение недоступно")
            return []
        except Exception as e:
            logger.error(f"Ошибка поиска DataMatrix: {e}")
            return []

    def _split_page_by_datamatrix(
        self,
        img: Image.Image,
        datamatrix_list: list[tuple[str, tuple[int, int, int, int]]],
        margin: int = 20,
    ) -> list[Image.Image]:
        """
        Разделение страницы на отдельные этикетки по найденным DataMatrix.

        Алгоритм:
        1. Сортируем DataMatrix по позиции (сверху вниз, слева направо)
        2. Определяем сетку по количеству уникальных X и Y позиций
        3. Вычисляем размер каждой ячейки сетки
        4. Кропим каждую ячейку как отдельную этикетку

        Args:
            img: Исходное изображение страницы
            datamatrix_list: Список найденных DataMatrix с координатами
            margin: Отступ от краёв

        Returns:
            Список изображений отдельных этикеток
        """
        if len(datamatrix_list) <= 1:
            # Только один DataMatrix — возвращаем всю страницу
            return [self._auto_crop(img)]

        # Собираем центры DataMatrix
        centers = []
        for _, (left, top, width, height) in datamatrix_list:
            # pylibdmtx даёт координаты относительно нижнего левого угла
            # Конвертируем в верхний левый угол (стандарт PIL)
            center_x = left + width // 2
            center_y = img.height - (top + height // 2)
            centers.append((center_x, center_y))

        # Определяем количество колонок и строк
        # Кластеризуем X-координаты
        x_coords = sorted({c[0] for c in centers})
        y_coords = sorted({c[1] for c in centers})

        # Простая кластеризация: объединяем близкие координаты
        def cluster_coords(coords: list[int], threshold: int = 100) -> list[int]:
            """Объединяет близкие координаты в кластеры."""
            if not coords:
                return []
            clusters = [coords[0]]
            for coord in coords[1:]:
                if coord - clusters[-1] > threshold:
                    clusters.append(coord)
            return clusters

        x_clusters = cluster_coords(x_coords, threshold=img.width // 10)
        y_clusters = cluster_coords(y_coords, threshold=img.height // 10)

        cols = len(x_clusters)
        rows = len(y_clusters)

        if cols == 0 or rows == 0:
            # Не удалось определить сетку
            return [self._auto_crop(img)]

        logger.info(f"Определена сетка этикеток: {rows}x{cols} ({rows * cols} этикеток)")

        # Вычисляем размер ячейки
        cell_width = img.width // cols
        cell_height = img.height // rows

        # Кропим каждую ячейку
        labels = []
        for row in range(rows):
            for col in range(cols):
                x1 = col * cell_width
                y1 = row * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height

                # Добавляем небольшое перекрытие чтобы не обрезать края
                x1 = max(0, x1 - margin)
                y1 = max(0, y1 - margin)
                x2 = min(img.width, x2 + margin)
                y2 = min(img.height, y2 + margin)

                cell = img.crop((x1, y1, x2, y2))

                # Применяем auto-crop к каждой ячейке
                cropped = self._auto_crop(cell, margin=5)
                labels.append(cropped)

        return labels

    def _is_a4_page(self, width_pt: float, height_pt: float) -> bool:
        """
        Проверяет, является ли страница A4 форматом.

        A4 = 595 x 842 pt (±10% допуск)
        """
        a4_width = 595
        a4_height = 842
        tolerance = 0.1

        # Проверяем оба варианта ориентации
        portrait_match = (
            abs(width_pt - a4_width) / a4_width < tolerance
            and abs(height_pt - a4_height) / a4_height < tolerance
        )
        landscape_match = (
            abs(width_pt - a4_height) / a4_height < tolerance
            and abs(height_pt - a4_width) / a4_width < tolerance
        )

        return portrait_match or landscape_match

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

            # Нормализуем ориентацию (альбомная → портретная)
            pil_image = self._normalize_orientation(pil_image)

            # Проверяем, является ли страница A4 (может содержать несколько этикеток)
            is_a4 = self._is_a4_page(width_pt, height_pt)

            if is_a4:
                # A4 страница — ищем несколько DataMatrix и разделяем
                datamatrix_list = self._find_all_datamatrix(pil_image)

                if len(datamatrix_list) > 1:
                    # Найдено несколько этикеток — разделяем страницу
                    logger.info(
                        f"Страница {i + 1}: A4 с {len(datamatrix_list)} этикетками, разделяем"
                    )
                    split_labels = self._split_page_by_datamatrix(pil_image, datamatrix_list)
                    pages.extend(split_labels)
                else:
                    # Одна этикетка или не найдено — стандартный auto-crop
                    pil_image = self._auto_crop(pil_image)
                    pages.append(pil_image)
            else:
                # Не A4 — стандартный auto-crop
                pil_image = self._auto_crop(pil_image)
                pages.append(pil_image)

        pdf.close()

        # page_count теперь отражает реальное количество извлечённых этикеток
        # (может быть больше исходных страниц если A4 был разделён)
        return ParsedPDF(
            pages=pages,
            page_count=len(pages),
            original_width=original_width,
            original_height=original_height,
        )

    def extract_codes(
        self,
        pdf_bytes: bytes,
        remove_duplicates: bool = True,
    ) -> ExtractedCodes:
        """
        Извлечение кодов DataMatrix из PDF файла с этикетками ЧЗ.

        Используется когда пользователь загружает PDF от Честного Знака
        вместо CSV/Excel с кодами.

        Args:
            pdf_bytes: Содержимое PDF файла
            remove_duplicates: Удалять дубликаты

        Returns:
            ExtractedCodes со списком кодов

        Raises:
            ValueError: Если не удалось извлечь коды
        """
        try:
            pdf = pdfium.PdfDocument(pdf_bytes)
        except Exception as e:
            raise ValueError(f"Не удалось открыть PDF: {str(e)}")

        page_count = len(pdf)
        if page_count == 0:
            pdf.close()
            raise ValueError("PDF файл пустой")

        all_codes: list[str] = []

        for i in range(page_count):
            page = pdf[i]

            # Рендерим страницу в высоком разрешении для надёжного распознавания
            render_scale = 300 / 72  # 300 DPI
            bitmap = page.render(scale=render_scale)
            pil_image = bitmap.to_pil()

            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Ищем все DataMatrix на странице
            datamatrix_list = self._find_all_datamatrix(pil_image)

            for code_data, _ in datamatrix_list:
                if code_data:
                    # Очистка кода от лишних символов
                    cleaned = code_data.strip()
                    if cleaned:
                        all_codes.append(cleaned)

            logger.debug(f"Страница {i + 1}: найдено {len(datamatrix_list)} DataMatrix")

        pdf.close()

        if not all_codes:
            raise ValueError(
                "Не найдено кодов DataMatrix в PDF. "
                "Убедитесь, что файл содержит этикетки с DataMatrix кодами Честного Знака."
            )

        # Удаление дубликатов
        duplicates_count = 0
        if remove_duplicates:
            unique_codes = list(dict.fromkeys(all_codes))  # Сохраняем порядок
            duplicates_count = len(all_codes) - len(unique_codes)
            all_codes = unique_codes

        logger.info(
            f"Извлечено {len(all_codes)} кодов из {page_count} страниц "
            f"(дубликатов удалено: {duplicates_count})"
        )

        return ExtractedCodes(
            codes=all_codes,
            count=len(all_codes),
            duplicates_removed=duplicates_count,
            pages_processed=page_count,
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
    for img in images:
        if img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        # JPEG с качеством 95% и DPI в EXIF
        img.save(buf, format="JPEG", quality=95, dpi=(dpi, dpi))
        jpeg_bytes = buf.getvalue()
        jpeg_bytes_list.append(jpeg_bytes)

    # img2pdf конвертирует JPEG напрямую без перекодирования
    pdf_bytes = img2pdf.convert(jpeg_bytes_list)

    return pdf_bytes
