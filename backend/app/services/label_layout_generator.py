# backend/app/services/label_layout_generator.py
"""
Генератор полных этикеток WB из данных Excel.

Поддерживает три шаблона:
- CLASSIC: штрихкод сверху, текст слева (по умолчанию)
- CENTERED: штрихкод сверху, текст по центру
- MINIMAL: только штрихкод + артикул
"""

from PIL import Image, ImageDraw, ImageFont

from app.config import LABEL
from app.models.label_types import LabelData, LabelLayout, LabelSize, ShowFields
from app.services.barcode_generator import BarcodeGenerator


class LabelLayoutGenerator:
    """Генератор полных этикеток WB из данных Excel."""

    def __init__(self):
        self.barcode_gen = BarcodeGenerator()
        self._font = None
        self._font_small = None
        self._font_bold = None

    def _get_font(self, size: int = 14) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Получить шрифт для текста."""
        import os

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(current_dir, "..", "assets", "fonts", "arial.ttf")
            return ImageFont.truetype(font_path, size)
        except OSError:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except OSError:
                return ImageFont.load_default()

    def generate(
        self,
        data: LabelData,
        layout: LabelLayout = LabelLayout.CLASSIC,
        size: LabelSize = LabelSize.SIZE_58x40,
        show_fields: ShowFields | None = None,
    ) -> Image.Image:
        """
        Генерирует изображение этикетки.

        Args:
            data: Данные этикетки (баркод, артикул, размер и т.д.)
            layout: Шаблон этикетки (classic, centered, minimal)
            size: Размер этикетки
            show_fields: Какие поля показывать

        Returns:
            PIL Image с этикеткой
        """
        if show_fields is None:
            show_fields = ShowFields()

        width_mm, height_mm = size.dimensions_mm
        width_px = LABEL.mm_to_pixels(width_mm)
        height_px = LABEL.mm_to_pixels(height_mm)

        if layout == LabelLayout.CLASSIC:
            return self._generate_classic(data, width_px, height_px, show_fields)
        elif layout == LabelLayout.CENTERED:
            return self._generate_centered(data, width_px, height_px, show_fields)
        else:  # MINIMAL
            return self._generate_minimal(data, width_px, height_px, show_fields)

    def generate_batch(
        self,
        items: list[LabelData],
        layout: LabelLayout = LabelLayout.CLASSIC,
        size: LabelSize = LabelSize.SIZE_58x40,
        show_fields: ShowFields | None = None,
    ) -> list[Image.Image]:
        """Генерация пакета этикеток."""
        return [self.generate(item, layout, size, show_fields) for item in items]

    def _generate_classic(
        self,
        data: LabelData,
        width_px: int,
        height_px: int,
        show_fields: ShowFields,
    ) -> Image.Image:
        """
        CLASSIC шаблон: как у конкурента — штрихкод сверху, текст снизу.

        ┌───────────────────┐
        │   ║║║║║║║║║║║║   │
        │   4607100000012   │
        │   Моя организация │
        │ Тестовый товар    │
        │ Артикул: ABC-123  │
        │ Цв.: Черный / Раз.: M │
        └───────────────────┘
        """
        # Создаём белый холст
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)

        margin = LABEL.mm_to_pixels(2)  # 2мм отступы
        y_cursor = margin

        # Шрифты — КРУПНЕЕ для читаемости
        font_bold = self._get_font(14)  # Жирный для названия и организации
        font_normal = self._get_font(12)  # Обычный для артикула и размера
        line_height = LABEL.mm_to_pixels(4)  # Межстрочный интервал

        # Генерируем штрихкод
        barcode_width_mm = 45.0  # Ширина штрихкода
        barcode_height_mm = 12.0  # Высота штрихкода (меньше чтобы влез текст)

        try:
            barcode_result = self.barcode_gen.generate(
                data.barcode,
                width_mm=barcode_width_mm,
                height_mm=barcode_height_mm,
            )
            barcode_img = barcode_result.image

            # Центрируем штрихкод
            barcode_x = (width_px - barcode_img.width) // 2
            img.paste(barcode_img, (barcode_x, y_cursor))
            y_cursor += barcode_img.height + LABEL.mm_to_pixels(1)
        except ValueError:
            # Невалидный баркод — пишем текстом
            text = f"Баркод: {data.barcode}"
            bbox = draw.textbbox((0, 0), text, font=font_normal)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width_px - text_width) // 2, y_cursor),
                text,
                fill="black",
                font=font_normal,
            )
            y_cursor += LABEL.mm_to_pixels(6)

        # Организация — СРАЗУ после штрихкода, жирным, по центру
        if data.organization:
            org_text = self._truncate_text(data.organization, width_px - 2 * margin, font_bold)
            bbox = draw.textbbox((0, 0), org_text, font=font_bold)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width_px - text_width) // 2, y_cursor),
                org_text,
                fill="black",
                font=font_bold,
            )
            y_cursor += line_height

        # Название товара — жирным
        if show_fields.name and data.name:
            name_text = self._truncate_text(data.name, width_px - 2 * margin, font_bold)
            draw.text(
                (margin, y_cursor),
                name_text,
                fill="black",
                font=font_bold,
            )
            y_cursor += line_height

        # Артикул — с префиксом "Артикул:"
        if show_fields.article and data.article:
            article_text = f"Артикул: {data.article}"
            draw.text(
                (margin, y_cursor),
                article_text,
                fill="black",
                font=font_normal,
            )
            y_cursor += line_height

        # Размер / Цвет — с префиксами "Цв.:" и "Раз.:"
        if show_fields.size_color and (data.size or data.color):
            parts = []
            if data.color:
                parts.append(f"Цв.: {data.color}")
            if data.size:
                parts.append(f"Раз.: {data.size}")
            size_color_text = " / ".join(parts)

            draw.text(
                (margin, y_cursor),
                size_color_text,
                fill="black",
                font=font_normal,
            )

        return img

    def _generate_centered(
        self,
        data: LabelData,
        width_px: int,
        height_px: int,
        show_fields: ShowFields,
    ) -> Image.Image:
        """
        CENTERED шаблон: штрихкод сверху, всё по центру.

        ┌───────────────────┐
        │   ║║║║║║║║║║║║   │
        │   4607100000012   │
        │   Моя организация │
        │  Тестовый товар   │
        │  Артикул: ABC-123 │
        │ Цв.: Черный / Раз.: M │
        └───────────────────┘
        """
        # Создаём белый холст
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)

        margin = LABEL.mm_to_pixels(2)  # 2мм отступы
        y_cursor = margin

        # Шрифты — КРУПНЕЕ для читаемости
        font_bold = self._get_font(14)
        font_normal = self._get_font(12)
        line_height = LABEL.mm_to_pixels(4)

        # Генерируем штрихкод
        barcode_width_mm = 45.0
        barcode_height_mm = 12.0

        try:
            barcode_result = self.barcode_gen.generate(
                data.barcode,
                width_mm=barcode_width_mm,
                height_mm=barcode_height_mm,
            )
            barcode_img = barcode_result.image

            # Центрируем штрихкод
            barcode_x = (width_px - barcode_img.width) // 2
            img.paste(barcode_img, (barcode_x, y_cursor))
            y_cursor += barcode_img.height + LABEL.mm_to_pixels(1)
        except ValueError:
            text = f"Баркод: {data.barcode}"
            bbox = draw.textbbox((0, 0), text, font=font_normal)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width_px - text_width) // 2, y_cursor),
                text,
                fill="black",
                font=font_normal,
            )
            y_cursor += LABEL.mm_to_pixels(6)

        # Организация — СРАЗУ после штрихкода, жирным, по центру
        if data.organization:
            org_text = self._truncate_text(data.organization, width_px - 2 * margin, font_bold)
            bbox = draw.textbbox((0, 0), org_text, font=font_bold)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width_px - text_width) // 2, y_cursor),
                org_text,
                fill="black",
                font=font_bold,
            )
            y_cursor += line_height

        # Название товара — жирным, по центру
        if show_fields.name and data.name:
            name_text = self._truncate_text(data.name, width_px - 2 * margin, font_bold)
            bbox = draw.textbbox((0, 0), name_text, font=font_bold)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width_px - text_width) // 2, y_cursor),
                name_text,
                fill="black",
                font=font_bold,
            )
            y_cursor += line_height

        # Артикул — с префиксом, по центру
        if show_fields.article and data.article:
            article_text = f"Артикул: {data.article}"
            bbox = draw.textbbox((0, 0), article_text, font=font_normal)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width_px - text_width) // 2, y_cursor),
                article_text,
                fill="black",
                font=font_normal,
            )
            y_cursor += line_height

        # Размер / Цвет — с префиксами, по центру
        if show_fields.size_color and (data.size or data.color):
            parts = []
            if data.color:
                parts.append(f"Цв.: {data.color}")
            if data.size:
                parts.append(f"Раз.: {data.size}")
            size_color_text = " / ".join(parts)

            bbox = draw.textbbox((0, 0), size_color_text, font=font_normal)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width_px - text_width) // 2, y_cursor),
                size_color_text,
                fill="black",
                font=font_normal,
            )

        return img

    def _generate_minimal(
        self,
        data: LabelData,
        width_px: int,
        height_px: int,
        show_fields: ShowFields,
    ) -> Image.Image:
        """
        MINIMAL layout: только штрихкод + артикул.

        ┌───────────────────┐
        │                   │
        │   ║║║║║║║║║║║║   │
        │   4607100000012   │
        │     ABC-123       │
        │                   │
        └───────────────────┘
        """
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)

        # Большой штрихкод по центру
        barcode_width_mm = 50.0
        barcode_height_mm = 18.0

        try:
            barcode_result = self.barcode_gen.generate(
                data.barcode,
                width_mm=barcode_width_mm,
                height_mm=barcode_height_mm,
            )
            barcode_img = barcode_result.image

            # Центрируем
            barcode_x = (width_px - barcode_img.width) // 2
            barcode_y = (height_px - barcode_img.height) // 2 - LABEL.mm_to_pixels(3)
            img.paste(barcode_img, (barcode_x, barcode_y))

            y_after_barcode = barcode_y + barcode_img.height + LABEL.mm_to_pixels(1)
        except ValueError:
            y_after_barcode = height_px // 2

        # Артикул под штрихкодом
        if show_fields.article and data.article:
            font = self._get_font(12)
            bbox = draw.textbbox((0, 0), data.article, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width_px - text_width) // 2, y_after_barcode),
                data.article,
                fill="black",
                font=font,
            )

        return img

    def _truncate_text(
        self,
        text: str,
        max_width_px: int,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> str:
        """Обрезает текст до указанной ширины с многоточием."""
        # Создаём временный draw для измерения текста
        tmp_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(tmp_img)

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width_px:
            return text

        # Обрезаем с многоточием
        while len(text) > 3:
            text = text[:-1]
            test_text = text + "..."
            bbox = draw.textbbox((0, 0), test_text, font=font)
            if bbox[2] - bbox[0] <= max_width_px:
                return test_text

        return text[:3] + "..."
