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
    brand: str | None = None
    country: str | None = None
    composition: str | None = None
    inn: str | None = None  # ИНН организации
    serial_number: int | None = None  # Серийный номер (автоинкремент)
    # Реквизиты для профессионального шаблона
    organization_address: str | None = None
    importer: str | None = None
    manufacturer: str | None = None
    production_date: str | None = None
    certificate_number: str | None = None


# Конфигурация layouts для каждого размера
# Все координаты в мм, Y от нижнего края (ReportLab convention)
#
# BASIC: Вертикальный шаблон
# - DataMatrix слева
# - Справа сверху: ИНН + организация
# - Центр: название товара (крупно)
# - Справа: цвет, размер, артикул
# - Внизу слева: код ЧЗ текстом, "ЧЕСТНЫЙ ЗНАК", EAC
# - Внизу справа: штрихкод WB
#
# PROFESSIONAL: Двухколоночный шаблон (только 58x40, 58x60)
# - Левая колонка: EAC, "ЧЕСТНЫЙ ЗНАК", DataMatrix, код ЧЗ, страна
# - Правая колонка: штрихкод, описание, артикул, бренд, размер/цвет, реквизиты

LAYOUTS = {
    "basic": {
        "58x40": {
            # DataMatrix слева вверху
            "datamatrix": {"x": 2, "y": 18, "size": 20},
            "chz_code_text": {"x": 2, "y": 14, "size": 3, "max_width": 20},
            "chz_code_text_2": {"x": 2, "y": 11, "size": 3, "max_width": 20},
            "dm_label": {"x": 2, "y": 7, "size": 4, "text": "ЧЕСТНЫЙ ЗНАК"},
            "eac_label": {"x": 2, "y": 3, "size": 5, "text": "EAC"},
            "serial_number": {"x": 12, "y": 3, "size": 4},
            # Справа сверху: ИНН + организация
            "inn": {"x": 26, "y": 36, "size": 4, "max_width": 30},
            "organization": {"x": 26, "y": 33, "size": 4, "max_width": 30},
            # Название крупно по центру справа
            "name": {"x": 26, "y": 28, "size": 6, "max_width": 30},
            "name_2": {"x": 26, "y": 24, "size": 6, "max_width": 30},
            # Характеристики
            "color": {"x": 26, "y": 19, "size": 4, "max_width": 30},
            "size_field": {"x": 26, "y": 16, "size": 4, "max_width": 30},
            "article": {"x": 26, "y": 13, "size": 4, "max_width": 30},
            # Штрихкод WB справа внизу
            "barcode": {"x": 26, "y": 4, "width": 28, "height": 8},
            "barcode_text": {"x": 26, "y": 2, "size": 5},
        },
        "58x30": {
            # DataMatrix слева (меньше)
            "datamatrix": {"x": 2, "y": 10, "size": 18},
            "chz_code_text": {"x": 2, "y": 6, "size": 2.5, "max_width": 18},
            "chz_code_text_2": {"x": 2, "y": 4, "size": 2.5, "max_width": 18},
            "dm_label": {"x": 2, "y": 1, "size": 3, "text": "ЧЗ"},
            "eac_label": {"x": 10, "y": 1, "size": 3, "text": "EAC"},
            "serial_number": {"x": 16, "y": 1, "size": 3},
            # Справа сверху
            "inn": {"x": 24, "y": 27, "size": 3, "max_width": 32},
            "organization": {"x": 24, "y": 24, "size": 3.5, "max_width": 32},
            # Название
            "name": {"x": 24, "y": 20, "size": 5, "max_width": 32},
            # Характеристики (компактно)
            "size_color": {"x": 24, "y": 16, "size": 3.5},
            "article": {"x": 24, "y": 13, "size": 3.5, "max_width": 32},
            # Штрихкод WB
            "barcode": {"x": 24, "y": 4, "width": 30, "height": 7},
            "barcode_text": {"x": 24, "y": 2, "size": 4},
        },
        "58x60": {
            # DataMatrix слева (больше места)
            "datamatrix": {"x": 2, "y": 36, "size": 22},
            "chz_code_text": {"x": 2, "y": 32, "size": 3.5, "max_width": 22},
            "chz_code_text_2": {"x": 2, "y": 29, "size": 3.5, "max_width": 22},
            "dm_label": {"x": 2, "y": 24, "size": 5, "text": "ЧЕСТНЫЙ ЗНАК"},
            "eac_label": {"x": 2, "y": 19, "size": 6, "text": "EAC"},
            "serial_number": {"x": 12, "y": 19, "size": 5},
            # Страна и состав внизу слева
            "country": {"x": 2, "y": 14, "size": 4, "max_width": 22},
            "composition": {"x": 2, "y": 10, "size": 3.5, "max_width": 22},
            # Справа сверху: ИНН + организация
            "inn": {"x": 28, "y": 56, "size": 4, "max_width": 28},
            "organization": {"x": 28, "y": 52, "size": 5, "max_width": 28},
            # Название крупно
            "name": {"x": 28, "y": 46, "size": 7, "max_width": 28},
            "name_2": {"x": 28, "y": 40, "size": 7, "max_width": 28},
            # Характеристики
            "color": {"x": 28, "y": 34, "size": 5, "max_width": 28},
            "size_field": {"x": 28, "y": 30, "size": 5, "max_width": 28},
            "article": {"x": 28, "y": 26, "size": 5, "max_width": 28},
            # Штрихкод WB справа внизу
            "barcode": {"x": 28, "y": 6, "width": 26, "height": 12},
            "barcode_text": {"x": 28, "y": 3, "size": 5},
        },
    },
    "professional": {
        # Professional только для 58x40 и 58x60 (много информации)
        "58x40": {
            # === Левая колонка (x=2, ширина ~24мм) ===
            "eac_label": {"x": 2, "y": 36, "size": 5, "text": "EAC"},
            "chz_logo": {"x": 10, "y": 35, "size": 4, "text": "ЧЕСТНЫЙ"},
            "chz_logo_2": {"x": 10, "y": 32, "size": 4, "text": "ЗНАК"},
            "datamatrix": {"x": 2, "y": 14, "size": 17},
            "chz_code_text": {"x": 2, "y": 10, "size": 2.5, "max_width": 22},
            "chz_code_text_2": {"x": 2, "y": 8, "size": 2.5, "max_width": 22},
            "country": {"x": 2, "y": 2, "size": 3.5, "max_width": 24},
            # === Правая колонка (x=27, ширина ~29мм) ===
            "barcode": {"x": 27, "y": 32, "width": 28, "height": 7},
            "barcode_text": {"x": 27, "y": 30, "size": 4},
            # Описание (название + цвет + артикул + размер)
            "description": {"x": 27, "y": 26, "size": 3.5, "max_width": 29},
            "description_2": {"x": 27, "y": 23, "size": 3.5, "max_width": 29},
            # Поля
            "article": {"x": 27, "y": 19, "size": 3.5, "max_width": 29},
            "brand": {"x": 27, "y": 16, "size": 3.5, "max_width": 29},
            "size_color": {"x": 27, "y": 13, "size": 3.5, "max_width": 29},
            # Реквизиты
            "importer": {"x": 27, "y": 10, "size": 3, "max_width": 29},
            "manufacturer": {"x": 27, "y": 7, "size": 3, "max_width": 29},
            "address": {"x": 27, "y": 4, "size": 3, "max_width": 29},
            "production_date": {"x": 27, "y": 1, "size": 3, "max_width": 14},
            "certificate": {"x": 42, "y": 1, "size": 3, "max_width": 14},
        },
        "58x60": {
            # === Левая колонка (x=2, ширина ~24мм) ===
            "eac_label": {"x": 2, "y": 56, "size": 6, "text": "EAC"},
            "chz_logo": {"x": 10, "y": 55, "size": 5, "text": "ЧЕСТНЫЙ"},
            "chz_logo_2": {"x": 10, "y": 51, "size": 5, "text": "ЗНАК"},
            "datamatrix": {"x": 2, "y": 28, "size": 22},
            "chz_code_text": {"x": 2, "y": 24, "size": 3, "max_width": 24},
            "chz_code_text_2": {"x": 2, "y": 21, "size": 3, "max_width": 24},
            "country": {"x": 2, "y": 4, "size": 4, "max_width": 24},
            # === Правая колонка (x=28, ширина ~28мм) ===
            "barcode": {"x": 28, "y": 50, "width": 26, "height": 9},
            "barcode_text": {"x": 28, "y": 48, "size": 5},
            # Описание
            "description": {"x": 28, "y": 43, "size": 4, "max_width": 28},
            "description_2": {"x": 28, "y": 39, "size": 4, "max_width": 28},
            # Поля
            "article": {"x": 28, "y": 34, "size": 4, "max_width": 28},
            "brand": {"x": 28, "y": 30, "size": 4, "max_width": 28},
            "size_color": {"x": 28, "y": 26, "size": 4, "max_width": 28},
            # Реквизиты
            "importer": {"x": 28, "y": 21, "size": 3.5, "max_width": 28},
            "manufacturer": {"x": 28, "y": 17, "size": 3.5, "max_width": 28},
            "address": {"x": 28, "y": 13, "size": 3.5, "max_width": 28},
            "address_2": {"x": 28, "y": 10, "size": 3.5, "max_width": 28},
            "production_date": {"x": 28, "y": 5, "size": 3.5, "max_width": 28},
            "certificate": {"x": 28, "y": 1, "size": 3.5, "max_width": 28},
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
        inn: str | None = None,
        layout: Literal["basic", "professional"] = "basic",
        label_format: Literal["combined", "separate"] = "combined",
        show_article: bool = True,
        show_size_color: bool = True,
        show_name: bool = True,
        show_organization: bool = True,
        show_inn: bool = False,
        show_country: bool = False,
        show_composition: bool = False,
        show_chz_code_text: bool = True,
        show_serial_number: bool = False,
        show_brand: bool = False,
        show_importer: bool = False,
        show_manufacturer: bool = False,
        show_address: bool = False,
        show_production_date: bool = False,
        show_certificate: bool = False,
        # Реквизиты организации (для professional шаблона)
        organization_address: str | None = None,
        importer: str | None = None,
        manufacturer: str | None = None,
        production_date: str | None = None,
        certificate_number: str | None = None,
        demo_mode: bool = False,
    ) -> bytes:
        """
        Генерирует PDF с этикетками.

        Args:
            items: Список товаров (баркоды WB)
            codes: Список кодов ЧЗ (DataMatrix)
            size: Размер этикетки (58x40, 58x30, 58x60)
            organization: Название организации
            inn: ИНН организации
            layout: Шаблон (basic, professional)
            label_format: Формат (combined - на одной странице, separate - раздельно)
            show_*: Флаги отображения полей
            organization_address: Адрес производства (professional)
            importer: Импортер (professional)
            manufacturer: Производитель (professional)
            production_date: Дата производства (professional)
            certificate_number: Номер сертификата (professional)
            demo_mode: Добавить водяной знак DEMO на этикетки

        Returns:
            bytes: PDF файл
        """
        if size not in LABEL_SIZES:
            size = "58x40"
        if layout not in LAYOUTS:
            layout = "basic"

        # Professional шаблон не поддерживает 58x30
        if layout == "professional" and size == "58x30":
            size = "58x40"

        width_mm, height_mm = LABEL_SIZES[size]
        layout_config = LAYOUTS[layout][size]

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(width_mm * mm, height_mm * mm))

        # Количество этикеток = минимум из товаров и кодов
        count = min(len(items), len(codes))

        for i in range(count):
            item = items[i]
            code = codes[i]
            # Серийный номер для текущей этикетки (начинается с 1)
            serial = i + 1 if show_serial_number else None

            if label_format == "combined":
                # Одна страница: WB + DataMatrix
                if layout == "basic":
                    self._draw_basic_label(
                        c=c,
                        item=item,
                        code=code,
                        layout_config=layout_config,
                        organization=organization,
                        inn=inn,
                        serial_number=serial,
                        show_article=show_article,
                        show_size_color=show_size_color,
                        show_name=show_name,
                        show_organization=show_organization,
                        show_inn=show_inn,
                        show_country=show_country,
                        show_composition=show_composition,
                        show_chz_code_text=show_chz_code_text,
                    )
                else:  # professional
                    self._draw_professional_label(
                        c=c,
                        item=item,
                        code=code,
                        layout_config=layout_config,
                        organization=organization,
                        inn=inn,
                        organization_address=organization_address,
                        importer=importer or organization,  # По умолчанию = организация
                        manufacturer=manufacturer or organization,
                        production_date=production_date,
                        certificate_number=certificate_number,
                        show_article=show_article,
                        show_size_color=show_size_color,
                        show_name=show_name,
                        show_brand=show_brand,
                        show_country=show_country,
                        show_importer=show_importer,
                        show_manufacturer=show_manufacturer,
                        show_address=show_address,
                        show_production_date=show_production_date,
                        show_certificate=show_certificate,
                        show_chz_code_text=show_chz_code_text,
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
                    inn=inn,
                    serial_number=serial,
                    show_article=show_article,
                    show_size_color=show_size_color,
                    show_name=show_name,
                    show_organization=show_organization,
                    show_inn=show_inn,
                    show_country=show_country,
                    show_composition=show_composition,
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
                    show_chz_code_text=show_chz_code_text,
                )
                if demo_mode:
                    self._draw_watermark(c, width_mm, height_mm)
                c.showPage()

        c.save()
        return buffer.getvalue()

    def _draw_basic_label(
        self,
        c: canvas.Canvas,
        item: LabelItem,
        code: str,
        layout_config: dict,
        organization: str | None,
        inn: str | None,
        serial_number: int | None,
        show_article: bool,
        show_size_color: bool,
        show_name: bool,
        show_organization: bool,
        show_inn: bool,
        show_country: bool,
        show_composition: bool,
        show_chz_code_text: bool,
    ) -> None:
        """
        Рисует BASIC этикетку:
        - DataMatrix слева
        - Справа сверху: ИНН + организация
        - Центр: название товара
        - Справа: цвет, размер, артикул
        - Внизу слева: код ЧЗ, "ЧЕСТНЫЙ ЗНАК", EAC
        - Внизу справа: штрихкод WB
        """
        # === DataMatrix слева ===
        dm = layout_config["datamatrix"]
        self._draw_datamatrix(c, code, dm["x"], dm["y"], dm["size"])

        # Код ЧЗ текстом под DataMatrix (две строки)
        if show_chz_code_text:
            if "chz_code_text" in layout_config:
                chz = layout_config["chz_code_text"]
                max_w = chz.get("max_width", 20)
                line1 = self._truncate_text(c, code[:16], chz["size"], max_w)
                self._draw_text(c, line1, chz["x"], chz["y"], chz["size"])
            if "chz_code_text_2" in layout_config:
                chz2 = layout_config["chz_code_text_2"]
                max_w = chz2.get("max_width", 20)
                line2 = self._truncate_text(c, code[16:31], chz2["size"], max_w)
                self._draw_text(c, line2, chz2["x"], chz2["y"], chz2["size"])

        # "ЧЕСТНЫЙ ЗНАК" под кодом
        if "dm_label" in layout_config:
            dm_lbl = layout_config["dm_label"]
            self._draw_text(c, dm_lbl["text"], dm_lbl["x"], dm_lbl["y"], dm_lbl["size"])

        # "EAC" внизу слева
        if "eac_label" in layout_config:
            eac = layout_config["eac_label"]
            self._draw_text(c, eac["text"], eac["x"], eac["y"], eac["size"])

        # Серийный номер (№ 0001)
        if serial_number is not None and "serial_number" in layout_config:
            sn = layout_config["serial_number"]
            self._draw_text(c, f"№ {serial_number:04d}", sn["x"], sn["y"], sn["size"])

        # === Справа сверху: ИНН + организация ===
        inn_value = inn or item.inn
        if show_inn and inn_value and "inn" in layout_config:
            inn_cfg = layout_config["inn"]
            max_w = inn_cfg.get("max_width", 30)
            text = self._truncate_text(c, f"ИНН: {inn_value}", inn_cfg["size"], max_w)
            self._draw_text(c, text, inn_cfg["x"], inn_cfg["y"], inn_cfg["size"])

        if show_organization and organization and "organization" in layout_config:
            org = layout_config["organization"]
            max_w = org.get("max_width", 30)
            text = self._truncate_text(c, organization, org["size"], max_w)
            self._draw_text(c, text, org["x"], org["y"], org["size"])

        # === Название товара (может быть в две строки) ===
        if show_name and item.name and "name" in layout_config:
            nm = layout_config["name"]
            max_w = nm.get("max_width", 30)
            # Разбиваем на две строки если не помещается
            words = item.name.split()
            line1_words = []
            line2_words = []
            c.setFont(FONT_NAME, nm["size"])

            for word in words:
                test_line = " ".join(line1_words + [word])
                if c.stringWidth(test_line) <= max_w * mm:
                    line1_words.append(word)
                else:
                    line2_words.append(word)

            if line1_words:
                self._draw_text(
                    c, " ".join(line1_words), nm["x"], nm["y"], nm["size"]
                )
            if line2_words and "name_2" in layout_config:
                nm2 = layout_config["name_2"]
                text2 = self._truncate_text(
                    c, " ".join(line2_words), nm2["size"], nm2.get("max_width", 30)
                )
                self._draw_text(c, text2, nm2["x"], nm2["y"], nm2["size"])

        # === Характеристики: цвет, размер, артикул ===
        # Цвет отдельно
        if show_size_color and item.color and "color" in layout_config:
            clr = layout_config["color"]
            max_w = clr.get("max_width", 30)
            text = self._truncate_text(c, f"цвет: {item.color}", clr["size"], max_w)
            self._draw_text(c, text, clr["x"], clr["y"], clr["size"])

        # Размер отдельно
        if show_size_color and item.size and "size_field" in layout_config:
            sz = layout_config["size_field"]
            self._draw_text(c, f"размер: {item.size}", sz["x"], sz["y"], sz["size"])

        # Размер/цвет вместе (для компактных размеров)
        if show_size_color and "size_color" in layout_config:
            parts = []
            if item.color:
                parts.append(item.color)
            if item.size:
                parts.append(item.size)
            if parts:
                sc = layout_config["size_color"]
                self._draw_text(c, " / ".join(parts), sc["x"], sc["y"], sc["size"])

        # Артикул
        if show_article and item.article and "article" in layout_config:
            art = layout_config["article"]
            max_w = art.get("max_width", 30)
            text = self._truncate_text(c, f"арт.: {item.article}", art["size"], max_w)
            self._draw_text(c, text, art["x"], art["y"], art["size"])

        # Страна (для 58x60)
        if show_country and item.country and "country" in layout_config:
            cnt = layout_config["country"]
            max_w = cnt.get("max_width", 22)
            text = self._truncate_text(c, f"Страна: {item.country}", cnt["size"], max_w)
            self._draw_text(c, text, cnt["x"], cnt["y"], cnt["size"])

        # Состав (для 58x60)
        if show_composition and item.composition and "composition" in layout_config:
            comp = layout_config["composition"]
            max_w = comp.get("max_width", 22)
            text = self._truncate_text(c, f"Состав: {item.composition}", comp["size"], max_w)
            self._draw_text(c, text, comp["x"], comp["y"], comp["size"])

        # === Штрихкод WB справа внизу ===
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        bc_text = layout_config["barcode_text"]
        self._draw_text(c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"])

    def _draw_professional_label(
        self,
        c: canvas.Canvas,
        item: LabelItem,
        code: str,
        layout_config: dict,
        organization: str | None,
        _inn: str | None,  # ИНН не показывается в professional шаблоне (реквизиты отдельно)
        organization_address: str | None,
        importer: str | None,
        manufacturer: str | None,
        production_date: str | None,
        certificate_number: str | None,
        show_article: bool,
        show_size_color: bool,
        show_name: bool,
        show_brand: bool,
        show_country: bool,
        show_importer: bool,
        show_manufacturer: bool,
        show_address: bool,
        show_production_date: bool,
        show_certificate: bool,
        show_chz_code_text: bool,
    ) -> None:
        """
        Рисует PROFESSIONAL этикетку (двухколоночный):
        Левая колонка: EAC, "ЧЕСТНЫЙ ЗНАК", DataMatrix, код ЧЗ, страна
        Правая колонка: штрихкод, описание, артикул, бренд, размер/цвет, реквизиты
        """
        # === Левая колонка ===

        # EAC
        if "eac_label" in layout_config:
            eac = layout_config["eac_label"]
            self._draw_text(c, eac["text"], eac["x"], eac["y"], eac["size"])

        # "ЧЕСТНЫЙ ЗНАК" (две строки)
        if "chz_logo" in layout_config:
            chz = layout_config["chz_logo"]
            self._draw_text(c, chz["text"], chz["x"], chz["y"], chz["size"])
        if "chz_logo_2" in layout_config:
            chz2 = layout_config["chz_logo_2"]
            self._draw_text(c, chz2["text"], chz2["x"], chz2["y"], chz2["size"])

        # DataMatrix
        dm = layout_config["datamatrix"]
        self._draw_datamatrix(c, code, dm["x"], dm["y"], dm["size"])

        # Код ЧЗ текстом (две строки)
        if show_chz_code_text:
            if "chz_code_text" in layout_config:
                chz = layout_config["chz_code_text"]
                max_w = chz.get("max_width", 22)
                line1 = self._truncate_text(c, code[:16], chz["size"], max_w)
                self._draw_text(c, line1, chz["x"], chz["y"], chz["size"])
            if "chz_code_text_2" in layout_config:
                chz2 = layout_config["chz_code_text_2"]
                max_w = chz2.get("max_width", 22)
                line2 = self._truncate_text(c, code[16:31], chz2["size"], max_w)
                self._draw_text(c, line2, chz2["x"], chz2["y"], chz2["size"])

        # Страна производства
        country = item.country or "Россия"
        if show_country and "country" in layout_config:
            cnt = layout_config["country"]
            max_w = cnt.get("max_width", 24)
            text = self._truncate_text(c, f"Сделано в {country}", cnt["size"], max_w)
            self._draw_text(c, text, cnt["x"], cnt["y"], cnt["size"])

        # === Правая колонка ===

        # Штрихкод WB
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        bc_text = layout_config["barcode_text"]
        self._draw_text(c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"])

        # Описание (название + цвет + артикул + размер в одну-две строки)
        if show_name and item.name:
            desc_parts = [item.name]
            if item.color:
                desc_parts.append(f"цвет {item.color}")
            if item.article:
                desc_parts.append(f"артикул {item.article}")
            if item.size:
                desc_parts.append(f"размер {item.size}")

            full_desc = ", ".join(desc_parts)

            if "description" in layout_config:
                desc = layout_config["description"]
                max_w = desc.get("max_width", 29)
                # Разбиваем на две строки
                c.setFont(FONT_NAME, desc["size"])
                if c.stringWidth(full_desc) <= max_w * mm:
                    self._draw_text(c, full_desc, desc["x"], desc["y"], desc["size"])
                else:
                    # Первая строка
                    line1 = self._truncate_text(c, full_desc, desc["size"], max_w)
                    self._draw_text(c, line1, desc["x"], desc["y"], desc["size"])
                    # Вторая строка (остаток)
                    if "description_2" in layout_config:
                        desc2 = layout_config["description_2"]
                        # Находим где обрезали (убираем "..." если была обрезка)
                        truncated_len = len(line1) - 3 if line1.endswith("...") else len(line1)
                        remaining = full_desc[truncated_len:].strip()
                        if remaining:
                            line2 = self._truncate_text(
                                c, remaining, desc2["size"], desc2.get("max_width", 29)
                            )
                            self._draw_text(c, line2, desc2["x"], desc2["y"], desc2["size"])

        # Артикул отдельной строкой
        if show_article and item.article and "article" in layout_config:
            art = layout_config["article"]
            max_w = art.get("max_width", 29)
            text = self._truncate_text(c, f"Артикул: {item.article}", art["size"], max_w)
            self._draw_text(c, text, art["x"], art["y"], art["size"])

        # Бренд
        if show_brand and item.brand and "brand" in layout_config:
            br = layout_config["brand"]
            max_w = br.get("max_width", 29)
            text = self._truncate_text(c, f"Бренд: {item.brand}", br["size"], max_w)
            self._draw_text(c, text, br["x"], br["y"], br["size"])

        # Размер / Цвет
        if show_size_color and "size_color" in layout_config:
            parts = []
            if item.size:
                parts.append(f"Размер: {item.size}")
            if item.color:
                parts.append(f"Цвет: {item.color}")
            if parts:
                sc = layout_config["size_color"]
                text = "    ".join(parts)  # Разделяем пробелами
                self._draw_text(c, text, sc["x"], sc["y"], sc["size"])

        # === Реквизиты ===

        # Импортер
        imp_value = importer or organization
        if show_importer and imp_value and "importer" in layout_config:
            imp = layout_config["importer"]
            max_w = imp.get("max_width", 29)
            text = self._truncate_text(c, f"Импортер: {imp_value}", imp["size"], max_w)
            self._draw_text(c, text, imp["x"], imp["y"], imp["size"])

        # Производитель
        mfr_value = manufacturer or organization
        if show_manufacturer and mfr_value and "manufacturer" in layout_config:
            mfr = layout_config["manufacturer"]
            max_w = mfr.get("max_width", 29)
            text = self._truncate_text(c, f"Производитель: {mfr_value}", mfr["size"], max_w)
            self._draw_text(c, text, mfr["x"], mfr["y"], mfr["size"])

        # Адрес
        addr_value = organization_address or item.organization_address
        if show_address and addr_value and "address" in layout_config:
            addr = layout_config["address"]
            max_w = addr.get("max_width", 29)
            text = self._truncate_text(c, f"Адрес: {addr_value}", addr["size"], max_w)
            self._draw_text(c, text, addr["x"], addr["y"], addr["size"])

        # Дата производства
        date_value = production_date or item.production_date
        if show_production_date and date_value and "production_date" in layout_config:
            pd = layout_config["production_date"]
            max_w = pd.get("max_width", 14)
            text = self._truncate_text(c, f"Дата: {date_value}", pd["size"], max_w)
            self._draw_text(c, text, pd["x"], pd["y"], pd["size"])

        # Сертификат
        cert_value = certificate_number or item.certificate_number
        if show_certificate and cert_value and "certificate" in layout_config:
            cert = layout_config["certificate"]
            max_w = cert.get("max_width", 14)
            text = self._truncate_text(c, f"Серт: {cert_value}", cert["size"], max_w)
            self._draw_text(c, text, cert["x"], cert["y"], cert["size"])

    def _draw_label_wb_only(
        self,
        c: canvas.Canvas,
        item: LabelItem,
        layout_config: dict,
        organization: str | None,
        inn: str | None,
        serial_number: int | None,
        show_article: bool,
        show_size_color: bool,
        show_name: bool,
        show_organization: bool,
        show_inn: bool,
        show_country: bool,
        show_composition: bool,
    ) -> None:
        """Рисует только WB часть этикетки (без DataMatrix)."""
        # Штрихкод WB
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        # Номер под штрихкодом
        bc_text = layout_config["barcode_text"]
        centered = bc_text.get("centered", False)
        self._draw_text(c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], centered)

        # Серийный номер (№ 0001)
        if serial_number is not None and "serial_number" in layout_config:
            sn = layout_config["serial_number"]
            self._draw_text(c, f"№ {serial_number:04d}", sn["x"], sn["y"], sn["size"])

        # ИНН
        inn_value = inn or item.inn
        if show_inn and inn_value and "inn" in layout_config:
            inn_cfg = layout_config["inn"]
            centered = inn_cfg.get("centered", False)
            max_width = inn_cfg.get("max_width", 26)
            text = self._truncate_text(c, f"ИНН: {inn_value}", inn_cfg["size"], max_width)
            self._draw_text(c, text, inn_cfg["x"], inn_cfg["y"], inn_cfg["size"], centered)

        # Организация
        if show_organization and organization and "organization" in layout_config:
            org = layout_config["organization"]
            centered = org.get("centered", False)
            max_width = org.get("max_width", 26)
            text = self._truncate_text(c, organization, org["size"], max_width)
            self._draw_text(c, text, org["x"], org["y"], org["size"], centered)

        # Название товара
        if show_name and item.name and "name" in layout_config:
            nm = layout_config["name"]
            centered = nm.get("centered", False)
            max_width = nm.get("max_width", 26)
            text = self._truncate_text(c, item.name, nm["size"], max_width)
            self._draw_text(c, text, nm["x"], nm["y"], nm["size"], centered)

        # Артикул
        if show_article and item.article and "article" in layout_config:
            art = layout_config["article"]
            centered = art.get("centered", False)
            self._draw_text(
                c, f"Артикул: {item.article}", art["x"], art["y"], art["size"], centered
            )

        # Цвет / Размер
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

        # Страна (если включено)
        if show_country and item.country and "country" in layout_config:
            cnt = layout_config["country"]
            centered = cnt.get("centered", False)
            max_width = cnt.get("max_width", 26)
            text = self._truncate_text(c, f"Страна: {item.country}", cnt["size"], max_width)
            self._draw_text(c, text, cnt["x"], cnt["y"], cnt["size"], centered)

        # Состав (если включено)
        if show_composition and item.composition and "composition" in layout_config:
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
        show_chz_code_text: bool = False,
    ) -> None:
        """Рисует только DataMatrix по центру страницы."""
        dm_size = 22  # мм
        x = (width_mm - dm_size) / 2
        y = (height_mm - dm_size) / 2 + 2  # чуть выше центра

        self._draw_datamatrix(c, code, x, y, dm_size)

        # Код ЧЗ текстом (если включено)
        if show_chz_code_text:
            self._draw_text(
                c,
                code[:31] + "...",
                width_mm / 2,
                y - 4,
                4,
                centered=True,
            )
            y_label = y - 8
        else:
            y_label = y - 4

        # Подпись
        self._draw_text(
            c,
            "Честный знак",
            width_mm / 2,
            y_label,
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
