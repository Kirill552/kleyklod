# backend/app/services/label_generator.py
"""
Генератор этикеток WB + Честный Знак через ReportLab (векторный PDF).

Поддерживает два layout:
- CLASSIC: штрихкод слева, текст слева, DataMatrix справа
- CENTERED: штрихкод по центру, текст по центру, DataMatrix справа

Размеры: 58x40, 58x30, 58x60 мм
"""

from dataclasses import dataclass
from io import BytesIO
from typing import Literal

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# pylibdmtx для DataMatrix (GS1 поддержка для Честный Знак)
try:
    from pylibdmtx.pylibdmtx import encode as dmtx_encode

    DMTX_AVAILABLE = True
except ImportError:
    DMTX_AVAILABLE = False

# Путь к шрифту DejaVu в контейнере Docker
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_NAME = "DejaVuSans"

# Флаг инициализации шрифта
_font_registered = False


def _ensure_font_registered() -> None:
    """Регистрирует шрифт DejaVu для кириллицы."""
    global _font_registered
    if _font_registered:
        return

    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        _font_registered = True
    except Exception:
        # Fallback для локальной разработки (Windows)
        import os

        # Попробуем найти Arial или другой шрифт
        windows_fonts = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]
        for font_path in windows_fonts:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
                _font_registered = True
                return

        # Если ничего не нашли, используем Helvetica (без кириллицы)
        _font_registered = True


@dataclass
class LabelItem:
    """Данные для одной этикетки."""

    barcode: str
    article: str | None = None
    size: str | None = None
    color: str | None = None
    name: str | None = None
    country: str | None = None
    composition: str | None = None


# Конфигурация layouts для каждого размера
# Все координаты в мм, Y от нижнего края (ReportLab convention)
# Новый порядок полей (сверху вниз): организация → название → артикул → размер/цвет → страна → состав
LAYOUTS = {
    "classic": {
        "58x40": {
            "barcode": {"x": 2, "y": 28, "width": 26, "height": 10},
            "barcode_text": {"x": 2, "y": 26, "size": 6},
            "organization": {"x": 2, "y": 22, "size": 5, "max_width": 26},
            "name": {"x": 2, "y": 18, "size": 5, "max_width": 26},
            "article": {"x": 2, "y": 14, "size": 5},
            "size_color": {"x": 2, "y": 10, "size": 5},
            "country": {"x": 2, "y": 6, "size": 4, "max_width": 26},
            "composition": {"x": 2, "y": 2, "size": 4, "max_width": 26},
            "datamatrix": {"x": 34, "y": 10, "size": 22},
            "dm_gtin": {"x": 34, "y": 6, "size": 4},
            "dm_label": {"x": 34, "y": 2, "size": 4, "text": "ЧЕСТНЫЙ ЗНАК"},
        },
        "58x30": {
            "barcode": {"x": 2, "y": 20, "width": 24, "height": 8},
            "barcode_text": {"x": 2, "y": 18, "size": 5},
            "organization": {"x": 2, "y": 14, "size": 4, "max_width": 24},
            "name": {"x": 2, "y": 10, "size": 4, "max_width": 24},
            "article": {"x": 2, "y": 6, "size": 4},
            "size_color": {"x": 2, "y": 2, "size": 4},
            "datamatrix": {"x": 34, "y": 6, "size": 18},
            "dm_gtin": {"x": 34, "y": 2, "size": 3},
            "dm_label": {"x": 34, "y": -1, "size": 3, "text": "ЧЕСТНЫЙ ЗНАК"},
        },
        "58x60": {
            "barcode": {"x": 2, "y": 48, "width": 28, "height": 12},
            "barcode_text": {"x": 2, "y": 46, "size": 6},
            "organization": {"x": 2, "y": 40, "size": 6, "max_width": 28},
            "name": {"x": 2, "y": 34, "size": 6, "max_width": 28},
            "article": {"x": 2, "y": 28, "size": 6},
            "size_color": {"x": 2, "y": 22, "size": 6},
            "country": {"x": 2, "y": 16, "size": 5, "max_width": 28},
            "composition": {"x": 2, "y": 10, "size": 5, "max_width": 28},
            "datamatrix": {"x": 34, "y": 30, "size": 22},
            "dm_gtin": {"x": 34, "y": 26, "size": 5},
            "dm_label": {"x": 34, "y": 22, "size": 5, "text": "ЧЕСТНЫЙ ЗНАК"},
        },
    },
    "centered": {
        "58x40": {
            "barcode": {"x": 16, "y": 28, "width": 26, "height": 10},
            "barcode_text": {"x": 29, "y": 26, "size": 6, "centered": True},
            "organization": {"x": 29, "y": 22, "size": 5, "max_width": 54, "centered": True},
            "name": {"x": 29, "y": 18, "size": 5, "max_width": 54, "centered": True},
            "article": {"x": 29, "y": 14, "size": 5, "centered": True},
            "size_color": {"x": 29, "y": 10, "size": 5, "centered": True},
            "country": {"x": 29, "y": 6, "size": 4, "max_width": 54, "centered": True},
            "composition": {"x": 29, "y": 2, "size": 4, "max_width": 54, "centered": True},
            "datamatrix": {"x": 34, "y": 10, "size": 22},
            "dm_gtin": {"x": 34, "y": 6, "size": 4},
            "dm_label": {"x": 34, "y": 2, "size": 4, "text": "ЧЕСТНЫЙ ЗНАК"},
        },
        "58x30": {
            "barcode": {"x": 17, "y": 20, "width": 24, "height": 8},
            "barcode_text": {"x": 29, "y": 18, "size": 5, "centered": True},
            "organization": {"x": 29, "y": 14, "size": 4, "max_width": 54, "centered": True},
            "name": {"x": 29, "y": 10, "size": 4, "max_width": 54, "centered": True},
            "article": {"x": 29, "y": 6, "size": 4, "centered": True},
            "size_color": {"x": 29, "y": 2, "size": 4, "centered": True},
            "datamatrix": {"x": 34, "y": 6, "size": 18},
            "dm_gtin": {"x": 34, "y": 2, "size": 3},
            "dm_label": {"x": 34, "y": -1, "size": 3, "text": "ЧЕСТНЫЙ ЗНАК"},
        },
        "58x60": {
            "barcode": {"x": 15, "y": 48, "width": 28, "height": 12},
            "barcode_text": {"x": 29, "y": 46, "size": 6, "centered": True},
            "organization": {"x": 29, "y": 40, "size": 6, "max_width": 54, "centered": True},
            "name": {"x": 29, "y": 34, "size": 6, "max_width": 54, "centered": True},
            "article": {"x": 29, "y": 28, "size": 6, "centered": True},
            "size_color": {"x": 29, "y": 22, "size": 6, "centered": True},
            "country": {"x": 29, "y": 16, "size": 5, "max_width": 54, "centered": True},
            "composition": {"x": 29, "y": 10, "size": 5, "max_width": 54, "centered": True},
            "datamatrix": {"x": 34, "y": 30, "size": 22},
            "dm_gtin": {"x": 34, "y": 26, "size": 5},
            "dm_label": {"x": 34, "y": 22, "size": 5, "text": "ЧЕСТНЫЙ ЗНАК"},
        },
    },
}

# Размеры этикеток в мм
LABEL_SIZES = {
    "58x40": (58, 40),
    "58x30": (58, 30),
    "58x60": (58, 60),
}


class LabelGenerator:
    """Генератор этикеток WB + ЧЗ через ReportLab (вектор)."""

    def __init__(self) -> None:
        _ensure_font_registered()

    def generate(
        self,
        items: list[LabelItem],
        codes: list[str],
        size: str = "58x40",
        organization: str | None = None,
        layout: Literal["classic", "centered"] = "classic",
        label_format: Literal["combined", "separate"] = "combined",
        show_article: bool = True,
        show_size_color: bool = True,
        show_name: bool = True,
        demo_mode: bool = False,
    ) -> bytes:
        """
        Генерирует PDF с этикетками.

        Args:
            items: Список товаров (баркоды WB)
            codes: Список кодов ЧЗ (DataMatrix)
            size: Размер этикетки (58x40, 58x30, 58x60)
            organization: Название организации
            layout: Шаблон (classic, centered)
            label_format: Формат (combined - на одной странице, separate - раздельно)
            show_article: Показывать артикул
            show_size_color: Показывать размер/цвет
            show_name: Показывать название
            demo_mode: Добавить водяной знак DEMO на этикетки

        Returns:
            bytes: PDF файл
        """
        if size not in LABEL_SIZES:
            size = "58x40"
        if layout not in LAYOUTS:
            layout = "classic"

        width_mm, height_mm = LABEL_SIZES[size]
        layout_config = LAYOUTS[layout][size]

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(width_mm * mm, height_mm * mm))

        # Количество этикеток = минимум из товаров и кодов
        count = min(len(items), len(codes))

        for i in range(count):
            item = items[i]
            code = codes[i]

            if label_format == "combined":
                # Одна страница: WB + DataMatrix
                self._draw_label(
                    c=c,
                    item=item,
                    code=code,
                    layout_config=layout_config,
                    organization=organization,
                    show_article=show_article,
                    show_size_color=show_size_color,
                    show_name=show_name,
                )
                if demo_mode:
                    self._draw_watermark(c, width_mm, height_mm)
                c.showPage()
            else:
                # Раздельно: сначала WB этикетка
                self._draw_label_wb_only(
                    c=c,
                    item=item,
                    layout_config=layout_config,
                    organization=organization,
                    show_article=show_article,
                    show_size_color=show_size_color,
                    show_name=show_name,
                )
                if demo_mode:
                    self._draw_watermark(c, width_mm, height_mm)
                c.showPage()

                # Затем DataMatrix
                self._draw_label_dm_only(
                    c=c,
                    code=code,
                    width_mm=width_mm,
                    height_mm=height_mm,
                )
                if demo_mode:
                    self._draw_watermark(c, width_mm, height_mm)
                c.showPage()

        c.save()
        return buffer.getvalue()

    def _draw_label(
        self,
        c: canvas.Canvas,
        item: LabelItem,
        code: str,
        layout_config: dict,
        organization: str | None,
        show_article: bool,
        show_size_color: bool,
        show_name: bool,
    ) -> None:
        """Рисует одну этикетку (WB + DataMatrix)."""
        # Штрихкод WB
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        # Номер под штрихкодом (один раз, без разделения)
        bc_text = layout_config["barcode_text"]
        centered = bc_text.get("centered", False)
        self._draw_text(c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], centered)

        # 1. Организация (всегда первая)
        if organization and "organization" in layout_config:
            org = layout_config["organization"]
            centered = org.get("centered", False)
            max_width = org.get("max_width", 26)
            text = self._truncate_text(c, organization, org["size"], max_width)
            self._draw_text(c, text, org["x"], org["y"], org["size"], centered)

        # 2. Название товара
        if show_name and item.name and "name" in layout_config:
            nm = layout_config["name"]
            centered = nm.get("centered", False)
            max_width = nm.get("max_width", 26)
            text = self._truncate_text(c, item.name, nm["size"], max_width)
            self._draw_text(c, text, nm["x"], nm["y"], nm["size"], centered)

        # 3. Артикул
        if show_article and item.article and "article" in layout_config:
            art = layout_config["article"]
            centered = art.get("centered", False)
            self._draw_text(
                c, f"Артикул: {item.article}", art["x"], art["y"], art["size"], centered
            )

        # 4. Цвет / Размер (новый формат: "Цв: X / Раз: Y")
        if show_size_color and "size_color" in layout_config:
            parts = []
            if item.color:
                parts.append(f"Цв: {item.color}")
            if item.size:
                parts.append(f"Раз: {item.size}")
            if parts:
                sc = layout_config["size_color"]
                centered = sc.get("centered", False)
                self._draw_text(c, " / ".join(parts), sc["x"], sc["y"], sc["size"], centered)

        # 5. Страна (если есть)
        if item.country and "country" in layout_config:
            cnt = layout_config["country"]
            centered = cnt.get("centered", False)
            max_width = cnt.get("max_width", 26)
            text = self._truncate_text(c, f"Страна: {item.country}", cnt["size"], max_width)
            self._draw_text(c, text, cnt["x"], cnt["y"], cnt["size"], centered)

        # 6. Состав (если есть)
        if item.composition and "composition" in layout_config:
            comp = layout_config["composition"]
            centered = comp.get("centered", False)
            max_width = comp.get("max_width", 26)
            text = self._truncate_text(c, f"Состав: {item.composition}", comp["size"], max_width)
            self._draw_text(c, text, comp["x"], comp["y"], comp["size"], centered)

        # DataMatrix
        dm = layout_config["datamatrix"]
        self._draw_datamatrix(c, code, dm["x"], dm["y"], dm["size"])

        # GTIN под DataMatrix
        if "dm_gtin" in layout_config:
            gtin = self._extract_gtin_from_code(code)
            if gtin:
                dm_gtin = layout_config["dm_gtin"]
                self._draw_text(c, gtin, dm_gtin["x"], dm_gtin["y"], dm_gtin["size"])

        # Подпись "ЧЕСТНЫЙ ЗНАК"
        if "dm_label" in layout_config:
            dm_lbl = layout_config["dm_label"]
            self._draw_text(c, dm_lbl["text"], dm_lbl["x"], dm_lbl["y"], dm_lbl["size"])

    def _draw_label_wb_only(
        self,
        c: canvas.Canvas,
        item: LabelItem,
        layout_config: dict,
        organization: str | None,
        show_article: bool,
        show_size_color: bool,
        show_name: bool,
    ) -> None:
        """Рисует только WB часть этикетки (без DataMatrix)."""
        # Штрихкод WB
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        # Номер под штрихкодом
        bc_text = layout_config["barcode_text"]
        centered = bc_text.get("centered", False)
        self._draw_text(c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], centered)

        # 1. Организация (всегда первая)
        if organization and "organization" in layout_config:
            org = layout_config["organization"]
            centered = org.get("centered", False)
            max_width = org.get("max_width", 26)
            text = self._truncate_text(c, organization, org["size"], max_width)
            self._draw_text(c, text, org["x"], org["y"], org["size"], centered)

        # 2. Название товара
        if show_name and item.name and "name" in layout_config:
            nm = layout_config["name"]
            centered = nm.get("centered", False)
            max_width = nm.get("max_width", 26)
            text = self._truncate_text(c, item.name, nm["size"], max_width)
            self._draw_text(c, text, nm["x"], nm["y"], nm["size"], centered)

        # 3. Артикул
        if show_article and item.article and "article" in layout_config:
            art = layout_config["article"]
            centered = art.get("centered", False)
            self._draw_text(
                c, f"Артикул: {item.article}", art["x"], art["y"], art["size"], centered
            )

        # 4. Цвет / Размер (новый формат: "Цв: X / Раз: Y")
        if show_size_color and "size_color" in layout_config:
            parts = []
            if item.color:
                parts.append(f"Цв: {item.color}")
            if item.size:
                parts.append(f"Раз: {item.size}")
            if parts:
                sc = layout_config["size_color"]
                centered = sc.get("centered", False)
                self._draw_text(c, " / ".join(parts), sc["x"], sc["y"], sc["size"], centered)

        # 5. Страна (если есть)
        if item.country and "country" in layout_config:
            cnt = layout_config["country"]
            centered = cnt.get("centered", False)
            max_width = cnt.get("max_width", 26)
            text = self._truncate_text(c, f"Страна: {item.country}", cnt["size"], max_width)
            self._draw_text(c, text, cnt["x"], cnt["y"], cnt["size"], centered)

        # 6. Состав (если есть)
        if item.composition and "composition" in layout_config:
            comp = layout_config["composition"]
            centered = comp.get("centered", False)
            max_width = comp.get("max_width", 26)
            text = self._truncate_text(c, f"Состав: {item.composition}", comp["size"], max_width)
            self._draw_text(c, text, comp["x"], comp["y"], comp["size"], centered)

    def _draw_label_dm_only(
        self,
        c: canvas.Canvas,
        code: str,
        width_mm: float,
        height_mm: float,
    ) -> None:
        """Рисует только DataMatrix по центру страницы."""
        dm_size = 22  # мм
        x = (width_mm - dm_size) / 2
        y = (height_mm - dm_size) / 2 + 2  # чуть выше центра

        self._draw_datamatrix(c, code, x, y, dm_size)

        # Подпись
        self._draw_text(
            c,
            "Честный знак",
            width_mm / 2,
            y - 4,
            5,
            centered=True,
        )

    def _detect_barcode_type(self, value: str) -> Literal["EAN13", "CODE128"]:
        """Автоматически определяет тип штрихкода."""
        # EAN-13: ровно 13 цифр (или 12 + контрольная)
        if len(value) in (12, 13) and value.isdigit():
            return "EAN13"
        return "CODE128"

    def _draw_barcode(
        self,
        c: canvas.Canvas,
        value: str,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        """Рисует штрихкод (автоопределение EAN-13 / Code128)."""
        barcode_type = self._detect_barcode_type(value)

        if barcode_type == "EAN13":
            self._draw_barcode_ean13(c, value, x, y, width, height)
        else:
            self._draw_barcode_code128(c, value, x, y, width, height)

    def _draw_barcode_ean13(
        self,
        c: canvas.Canvas,
        value: str,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        """EAN-13 штрихкод."""
        # Добавляем контрольную цифру если нужно
        if len(value) == 12:
            value = value + self._calculate_ean13_check_digit(value)

        barcode = Ean13BarcodeWidget(value)
        barcode.barHeight = height * mm
        # EAN-13 имеет 95 модулей
        barcode.barWidth = (width * mm) / 95

        d = Drawing()
        d.add(barcode)
        renderPDF.draw(d, c, x * mm, y * mm)

    def _draw_barcode_code128(
        self,
        c: canvas.Canvas,
        value: str,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        """Code128 штрихкод."""
        barcode = code128.Code128(
            value,
            barHeight=height * mm,
            barWidth=(width * mm) / (len(value) * 11 + 35),  # примерный расчёт
            humanReadable=False,
        )
        barcode.drawOn(c, x * mm, y * mm)

    def _draw_datamatrix(
        self,
        c: canvas.Canvas,
        value: str,
        x: float,
        y: float,
        size: float,
    ) -> None:
        """DataMatrix через pylibdmtx (GS1 поддержка для Честный Знак)."""
        if not DMTX_AVAILABLE:
            self._draw_dm_placeholder(c, x, y, size)
            return

        try:
            from PIL import Image

            # Кодируем DataMatrix через pylibdmtx
            # pylibdmtx корректно обрабатывает GS1 коды с FNC1
            encoded = dmtx_encode(value.encode("utf-8"))

            # Создаём PIL Image из результата
            img = Image.frombytes(
                "RGB",
                (encoded.width, encoded.height),
                encoded.pixels,
            )

            # Конвертируем в черно-белое для лучшей контрастности
            img = img.convert("1")

            # Сохраняем во временный буфер для вставки в PDF
            img_buffer = BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            # Вставляем изображение в PDF с нужным размером
            img_reader = ImageReader(img_buffer)
            c.drawImage(
                img_reader,
                x * mm,
                y * mm,
                width=size * mm,
                height=size * mm,
                preserveAspectRatio=True,
                anchor="sw",
            )
        except Exception:
            # Fallback: рисуем placeholder если код невалидный
            self._draw_dm_placeholder(c, x, y, size)

    def _draw_dm_placeholder(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        size: float,
    ) -> None:
        """Рисует placeholder вместо DataMatrix при ошибке."""
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x * mm, y * mm, size * mm, size * mm, fill=1, stroke=1)

        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont(FONT_NAME, 6)
        c.drawCentredString((x + size / 2) * mm, (y + size / 2) * mm, "Ошибка кода")

    def _draw_text(
        self,
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        font_size: float,
        centered: bool = False,
    ) -> None:
        """Рисует текст с кириллицей."""
        c.setFont(FONT_NAME, font_size)
        c.setFillColorRGB(0, 0, 0)

        if centered:
            c.drawCentredString(x * mm, y * mm, text)
        else:
            c.drawString(x * mm, y * mm, text)

    def _truncate_text(
        self,
        c: canvas.Canvas,
        text: str,
        font_size: float,
        max_width_mm: float,
    ) -> str:
        """Обрезает текст если он не помещается."""
        c.setFont(FONT_NAME, font_size)
        max_width = max_width_mm * mm

        if c.stringWidth(text) <= max_width:
            return text

        # Обрезаем и добавляем ...
        while len(text) > 3 and c.stringWidth(text + "...") > max_width:
            text = text[:-1]

        return text + "..."

    def _calculate_ean13_check_digit(self, code: str) -> str:
        """Вычисляет контрольную цифру EAN-13."""
        if len(code) != 12:
            return "0"

        total = 0
        for i, digit in enumerate(code):
            if i % 2 == 0:
                total += int(digit)
            else:
                total += int(digit) * 3

        check = (10 - (total % 10)) % 10
        return str(check)

    def _extract_gtin_from_code(self, code: str) -> str | None:
        """Извлекает GTIN (14 цифр) из кода маркировки ЧЗ."""
        # Код ЧЗ начинается с "01" + 14 цифр GTIN
        if code.startswith("01") and len(code) >= 16:
            return code[2:16]
        return None

    def _draw_watermark(
        self,
        c: canvas.Canvas,
        width_mm: float,
        height_mm: float,
    ) -> None:
        """
        Рисует водяной знак DEMO на этикетке.

        Полупрозрачный серый текст по центру + мелкий текст в углах.
        """
        # Сохраняем текущее состояние
        c.saveState()

        # Серый цвет для водяного знака
        c.setFillColorRGB(0.7, 0.7, 0.7)

        # Большой текст DEMO по центру
        font_size_big = min(width_mm, height_mm) * 0.25
        c.setFont(FONT_NAME, font_size_big)
        c.drawCentredString(
            (width_mm / 2) * mm,
            (height_mm / 2) * mm,
            "DEMO",
        )

        # Мелкий текст в углах
        font_size_small = 4
        c.setFont(FONT_NAME, font_size_small)

        # Верхний левый угол
        c.drawString(1 * mm, (height_mm - 3) * mm, "DEMO")

        # Нижний правый угол
        text_width = c.stringWidth("DEMO", FONT_NAME, font_size_small)
        c.drawString((width_mm * mm) - text_width - 1 * mm, 1 * mm, "DEMO")

        # Восстанавливаем состояние
        c.restoreState()
