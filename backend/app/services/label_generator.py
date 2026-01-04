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

from reportlab.graphics.barcode import code128
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

# Путь к шрифтам DejaVu в контейнере Docker
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_PATH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_NAME = "DejaVuSans"
FONT_NAME_BOLD = "DejaVuSans-Bold"

# Флаг инициализации шрифта
_font_registered = False


def _ensure_font_registered() -> None:
    """Регистрирует шрифты DejaVu (обычный и жирный) для кириллицы."""
    global _font_registered
    if _font_registered:
        return

    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, FONT_PATH_BOLD))
        _font_registered = True
    except Exception:
        # Fallback для локальной разработки (Windows)
        import os

        # Попробуем найти Arial или другой шрифт
        windows_fonts = [
            ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
            ("C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/tahomabd.ttf"),
            ("C:/Windows/Fonts/calibri.ttf", "C:/Windows/Fonts/calibrib.ttf"),
        ]
        for font_path, bold_path in windows_fonts:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, bold_path))
                else:
                    # Если нет bold, используем обычный
                    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, font_path))
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
            # DataMatrix слева вверху (15мм как в HTML)
            "datamatrix": {"x": 1.5, "y": 23.5, "size": 15},
            # Код ЧЗ текстом под DataMatrix
            "chz_code_text": {"x": 1.5, "y": 20, "size": 3, "max_width": 15},
            "chz_code_text_2": {"x": 1.5, "y": 17.5, "size": 3, "max_width": 15},
            # "ЧЕСТНЫЙ ЗНАК" и EAC слева внизу
            "dm_label": {"x": 1.5, "y": 13, "size": 3.5, "text": "ЧЕСТНЫЙ ЗНАК"},
            "eac_label": {"x": 1.5, "y": 8, "size": 7, "text": "EAC"},
            "serial_number": {"x": 1.5, "y": 4, "size": 5},
            # === Правая колонка: центр между DataMatrix (17мм) и краем (58мм) = 37.5мм ===
            # ИНН + организация (плотно, 1.5мм между строками)
            "inn": {"x": 37.5, "y": 37, "size": 4, "max_width": 38, "centered": True},
            "organization": {"x": 37.5, "y": 35, "size": 4, "max_width": 38, "centered": True},
            # Название крупно (жирный шрифт 7pt, 3мм между строками)
            "name": {"x": 37.5, "y": 30, "size": 7, "max_width": 38, "centered": True},
            "name_2": {"x": 37.5, "y": 26, "size": 7, "max_width": 38, "centered": True},
            # Характеристики (плотно, 2мм между строками)
            "color": {"x": 37.5, "y": 21, "size": 4, "max_width": 38, "centered": True},
            "size_field": {"x": 37.5, "y": 19, "size": 4, "max_width": 38, "centered": True},
            "article": {"x": 37.5, "y": 17, "size": 4, "max_width": 38, "centered": True},
            # Штрихкод WB справа внизу (центрирован в правой колонке)
            "barcode": {"x": 19, "y": 4, "width": 38, "height": 8},
            "barcode_text": {"x": 37.5, "y": 2, "size": 4, "centered": True},
        },
        "58x30": {
            # DataMatrix слева (компактный размер 12мм)
            "datamatrix": {"x": 1.5, "y": 16, "size": 12},
            "chz_code_text": {"x": 1.5, "y": 13, "size": 2.5, "max_width": 12},
            "chz_code_text_2": {"x": 1.5, "y": 11, "size": 2.5, "max_width": 12},
            "dm_label": {"x": 1.5, "y": 7, "size": 3, "text": "ЧЗ"},
            "eac_label": {"x": 1.5, "y": 3, "size": 5, "text": "EAC"},
            "serial_number": {"x": 9, "y": 3, "size": 3},
            # === Правая колонка: центр = (14 + 58) / 2 = 36мм ===
            "inn": {"x": 36, "y": 28, "size": 3, "max_width": 42, "centered": True},
            "organization": {"x": 36, "y": 26, "size": 3, "max_width": 42, "centered": True},
            # Название (компактно)
            "name": {"x": 36, "y": 22, "size": 5, "max_width": 42, "centered": True},
            # Характеристики (одной строкой)
            "size_color": {"x": 36, "y": 18, "size": 3.5, "max_width": 42, "centered": True},
            "article": {"x": 36, "y": 15, "size": 3.5, "max_width": 42, "centered": True},
            # Штрихкод WB (центрирован)
            "barcode": {"x": 16, "y": 4, "width": 40, "height": 7},
            "barcode_text": {"x": 36, "y": 2, "size": 3.5, "centered": True},
        },
        "58x60": {
            # DataMatrix слева (18мм для большей этикетки)
            "datamatrix": {"x": 1.5, "y": 40, "size": 18},
            "chz_code_text": {"x": 1.5, "y": 36, "size": 3, "max_width": 18},
            "chz_code_text_2": {"x": 1.5, "y": 33.5, "size": 3, "max_width": 18},
            "dm_label": {"x": 1.5, "y": 29, "size": 4, "text": "ЧЕСТНЫЙ ЗНАК"},
            "eac_label": {"x": 1.5, "y": 22, "size": 8, "text": "EAC"},
            "serial_number": {"x": 1.5, "y": 16, "size": 5},
            # Страна и состав внизу слева
            "country": {"x": 1.5, "y": 10, "size": 4, "max_width": 18},
            "composition": {"x": 1.5, "y": 6, "size": 3.5, "max_width": 18},
            # === Правая колонка: центр = (20 + 58) / 2 = 39мм ===
            "inn": {"x": 39, "y": 57, "size": 4, "max_width": 36, "centered": True},
            "organization": {"x": 39, "y": 54.5, "size": 4, "max_width": 36, "centered": True},
            # Название крупно (две строки)
            "name": {"x": 39, "y": 49, "size": 8, "max_width": 36, "centered": True},
            "name_2": {"x": 39, "y": 44, "size": 8, "max_width": 36, "centered": True},
            # Характеристики (плотно)
            "color": {"x": 39, "y": 38, "size": 5, "max_width": 36, "centered": True},
            "size_field": {"x": 39, "y": 35, "size": 5, "max_width": 36, "centered": True},
            "article": {"x": 39, "y": 32, "size": 5, "max_width": 36, "centered": True},
            # Штрихкод WB (центрирован)
            "barcode": {"x": 21, "y": 6, "width": 36, "height": 14},
            "barcode_text": {"x": 39, "y": 3, "size": 5, "centered": True},
        },
    },
    "professional": {
        # Professional только для 58x40 и 58x60 (много информации)
        "58x40": {
            # === Вертикальная линия-разделитель (отступ 1мм от DataMatrix) ===
            "divider": {"x": 16.5, "y_start": 1, "y_end": 39, "width": 0.5},
            # === Левая колонка (x=1.5, ширина до 15мм) ===
            "eac_label": {"x": 1.5, "y": 36, "size": 5, "text": "EAC"},
            "chz_logo": {"x": 7, "y": 36, "size": 3, "text": "ЧЕСТНЫЙ"},
            "chz_logo_2": {"x": 7, "y": 34, "size": 3, "text": "ЗНАК"},
            "datamatrix": {"x": 1.5, "y": 19, "size": 14},
            "chz_code_text": {"x": 1.5, "y": 16, "size": 2.5, "max_width": 14},
            "chz_code_text_2": {"x": 1.5, "y": 14, "size": 2.5, "max_width": 14},
            "country": {"x": 1.5, "y": 2, "size": 3, "max_width": 14},
            # === Правая колонка (x=18, ширина 39мм, центр=37.5мм) ===
            # Штрихкод вверху (центрирован)
            "barcode": {"x": 18, "y": 33, "width": 39, "height": 6},
            "barcode_text": {"x": 37.5, "y": 31, "size": 3.5, "centered": True},
            # Описание (название, цвет, размер) - центрировано, жирное
            "description": {
                "x": 37.5,
                "y": 27,
                "size": 4,
                "max_width": 39,
                "centered": True,
                "bold": True,
            },
            "description_2": {
                "x": 37.5,
                "y": 24,
                "size": 4,
                "max_width": 39,
                "centered": True,
                "bold": True,
            },
            # Поля - прижаты к левому краю (к разделителю), label жирный
            "article": {"x": 18, "y": 20, "size": 3, "max_width": 39, "label_bold": True},
            "brand": {"x": 18, "y": 17.5, "size": 3, "max_width": 39, "label_bold": True},
            "size_color": {"x": 18, "y": 15, "size": 3, "max_width": 39, "label_bold": True},
            # Реквизиты - всё обычным шрифтом
            "importer": {"x": 18, "y": 12, "size": 2.5, "max_width": 39, "label_bold": False},
            "manufacturer": {"x": 18, "y": 9.5, "size": 2.5, "max_width": 39, "label_bold": False},
            "address": {"x": 18, "y": 7, "size": 2.5, "max_width": 39, "label_bold": False},
            "production_date": {"x": 18, "y": 4, "size": 2.5, "max_width": 19, "label_bold": False},
            "certificate": {"x": 38, "y": 4, "size": 2.5, "max_width": 19, "label_bold": False},
        },
        "58x60": {
            # === Вертикальная линия-разделитель (отступ 1мм от DataMatrix 17мм) ===
            "divider": {"x": 19.5, "y_start": 1, "y_end": 59, "width": 0.5},
            # === Левая колонка (x=1.5, ширина до 17мм) ===
            "eac_label": {"x": 1.5, "y": 56, "size": 6, "text": "EAC"},
            "chz_logo": {"x": 8, "y": 56, "size": 4, "text": "ЧЕСТНЫЙ"},
            "chz_logo_2": {"x": 8, "y": 53, "size": 4, "text": "ЗНАК"},
            "datamatrix": {"x": 1.5, "y": 35, "size": 17},
            "chz_code_text": {"x": 1.5, "y": 31, "size": 2.5, "max_width": 17},
            "chz_code_text_2": {"x": 1.5, "y": 28.5, "size": 2.5, "max_width": 17},
            "country": {"x": 1.5, "y": 2, "size": 3.5, "max_width": 17},
            # === Правая колонка (x=21, ширина 36мм, центр=39мм) ===
            # Штрихкод вверху (центрирован)
            "barcode": {"x": 21, "y": 52, "width": 36, "height": 7},
            "barcode_text": {"x": 39, "y": 50, "size": 4, "centered": True},
            # Описание (название, цвет, размер) - центрировано, жирное
            "description": {
                "x": 39,
                "y": 45,
                "size": 4.5,
                "max_width": 36,
                "centered": True,
                "bold": True,
            },
            "description_2": {
                "x": 39,
                "y": 41,
                "size": 4.5,
                "max_width": 36,
                "centered": True,
                "bold": True,
            },
            # Поля - прижаты к левому краю, label жирный
            "article": {"x": 21, "y": 36, "size": 3.5, "max_width": 36, "label_bold": True},
            "brand": {"x": 21, "y": 32.5, "size": 3.5, "max_width": 36, "label_bold": True},
            "size_color": {"x": 21, "y": 29, "size": 3.5, "max_width": 36, "label_bold": True},
            # Реквизиты - всё обычным шрифтом
            "importer": {"x": 21, "y": 24, "size": 3, "max_width": 36, "label_bold": False},
            "manufacturer": {"x": 21, "y": 20, "size": 3, "max_width": 36, "label_bold": False},
            "address": {"x": 21, "y": 16, "size": 3, "max_width": 36, "label_bold": False},
            "address_2": {"x": 21, "y": 13, "size": 3, "max_width": 36, "label_bold": False},
            "production_date": {"x": 21, "y": 8, "size": 3, "max_width": 36, "label_bold": False},
            "certificate": {"x": 21, "y": 4, "size": 3, "max_width": 36, "label_bold": False},
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
                        _inn=inn,
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
            centered = inn_cfg.get("centered", False)
            text = self._truncate_text(c, f"ИНН: {inn_value}", inn_cfg["size"], max_w)
            self._draw_text(c, text, inn_cfg["x"], inn_cfg["y"], inn_cfg["size"], centered)

        if show_organization and organization and "organization" in layout_config:
            org = layout_config["organization"]
            max_w = org.get("max_width", 30)
            centered = org.get("centered", False)
            text = self._truncate_text(c, organization, org["size"], max_w)
            self._draw_text(c, text, org["x"], org["y"], org["size"], centered)

        # === Название товара (может быть в две строки) ===
        if show_name and item.name and "name" in layout_config:
            nm = layout_config["name"]
            max_w = nm.get("max_width", 30)
            centered = nm.get("centered", False)
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
                self._draw_text(c, " ".join(line1_words), nm["x"], nm["y"], nm["size"], centered)
            if line2_words and "name_2" in layout_config:
                nm2 = layout_config["name_2"]
                centered2 = nm2.get("centered", False)
                text2 = self._truncate_text(
                    c, " ".join(line2_words), nm2["size"], nm2.get("max_width", 30)
                )
                self._draw_text(c, text2, nm2["x"], nm2["y"], nm2["size"], centered2)

        # === Характеристики: цвет, размер, артикул ===
        # Цвет отдельно
        if show_size_color and item.color and "color" in layout_config:
            clr = layout_config["color"]
            max_w = clr.get("max_width", 30)
            centered = clr.get("centered", False)
            text = self._truncate_text(c, f"цвет: {item.color}", clr["size"], max_w)
            self._draw_text(c, text, clr["x"], clr["y"], clr["size"], centered)

        # Размер отдельно
        if show_size_color and item.size and "size_field" in layout_config:
            sz = layout_config["size_field"]
            centered = sz.get("centered", False)
            self._draw_text(c, f"размер: {item.size}", sz["x"], sz["y"], sz["size"], centered)

        # Размер/цвет вместе (для компактных размеров)
        if show_size_color and "size_color" in layout_config:
            parts = []
            if item.color:
                parts.append(item.color)
            if item.size:
                parts.append(item.size)
            if parts:
                sc = layout_config["size_color"]
                centered = sc.get("centered", False)
                self._draw_text(c, " / ".join(parts), sc["x"], sc["y"], sc["size"], centered)

        # Артикул
        if show_article and item.article and "article" in layout_config:
            art = layout_config["article"]
            max_w = art.get("max_width", 30)
            centered = art.get("centered", False)
            text = self._truncate_text(c, f"арт.: {item.article}", art["size"], max_w)
            self._draw_text(c, text, art["x"], art["y"], art["size"], centered)

        # Страна (для 58x60)
        if show_country and item.country and "country" in layout_config:
            cnt = layout_config["country"]
            max_w = cnt.get("max_width", 22)
            centered = cnt.get("centered", False)
            text = self._truncate_text(c, f"Страна: {item.country}", cnt["size"], max_w)
            self._draw_text(c, text, cnt["x"], cnt["y"], cnt["size"], centered)

        # Состав (для 58x60)
        if show_composition and item.composition and "composition" in layout_config:
            comp = layout_config["composition"]
            max_w = comp.get("max_width", 22)
            centered = comp.get("centered", False)
            text = self._truncate_text(c, f"Состав: {item.composition}", comp["size"], max_w)
            self._draw_text(c, text, comp["x"], comp["y"], comp["size"], centered)

        # === Штрихкод WB справа внизу ===
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        bc_text = layout_config["barcode_text"]
        bc_centered = bc_text.get("centered", False)
        self._draw_text(c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], bc_centered)

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
        Правая колонка: штрихкод, описание (центрировано, жирное), поля (слева, label жирный)
        """
        # === Вертикальная линия-разделитель ===
        if "divider" in layout_config:
            div = layout_config["divider"]
            self._draw_vertical_line(
                c, div["x"], div["y_start"], div["y_end"], div.get("width", 0.3)
            )

        # === Левая колонка ===

        # EAC
        if "eac_label" in layout_config:
            eac = layout_config["eac_label"]
            self._draw_text(c, eac["text"], eac["x"], eac["y"], eac["size"], bold=True)

        # "ЧЕСТНЫЙ ЗНАК" (две строки)
        if "chz_logo" in layout_config:
            chz = layout_config["chz_logo"]
            self._draw_text(c, chz["text"], chz["x"], chz["y"], chz["size"], bold=True)
        if "chz_logo_2" in layout_config:
            chz2 = layout_config["chz_logo_2"]
            self._draw_text(c, chz2["text"], chz2["x"], chz2["y"], chz2["size"], bold=True)

        # DataMatrix
        dm = layout_config["datamatrix"]
        self._draw_datamatrix(c, code, dm["x"], dm["y"], dm["size"])

        # Код ЧЗ текстом (две строки)
        if show_chz_code_text:
            if "chz_code_text" in layout_config:
                chz = layout_config["chz_code_text"]
                max_w = chz.get("max_width", 14)
                line1 = self._truncate_text(c, code[:16], chz["size"], max_w)
                self._draw_text(c, line1, chz["x"], chz["y"], chz["size"])
            if "chz_code_text_2" in layout_config:
                chz2 = layout_config["chz_code_text_2"]
                max_w = chz2.get("max_width", 14)
                line2 = self._truncate_text(c, code[16:31], chz2["size"], max_w)
                self._draw_text(c, line2, chz2["x"], chz2["y"], chz2["size"])

        # Страна производства
        country = item.country or "Россия"
        if show_country and "country" in layout_config:
            cnt = layout_config["country"]
            max_w = cnt.get("max_width", 14)
            text = self._truncate_text(c, f"Сделано в {country}", cnt["size"], max_w)
            self._draw_text(c, text, cnt["x"], cnt["y"], cnt["size"])

        # === Правая колонка ===

        # Штрихкод WB (вверху)
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        bc_text = layout_config["barcode_text"]
        bc_centered = bc_text.get("centered", False)
        self._draw_text(c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], bc_centered)

        # Описание (название, цвет, размер) - центрировано, жирное
        if show_name and item.name:
            desc_parts = [item.name]
            if item.color:
                desc_parts.append(f"цвет {item.color}")
            if item.size:
                desc_parts.append(f"размер {item.size}")

            full_desc = ", ".join(desc_parts)

            if "description" in layout_config:
                desc = layout_config["description"]
                max_w = desc.get("max_width", 40)
                centered = desc.get("centered", False)
                bold = desc.get("bold", False)

                # Используем жирный шрифт для расчёта ширины
                font = FONT_NAME_BOLD if bold else FONT_NAME
                c.setFont(font, desc["size"])

                if c.stringWidth(full_desc) <= max_w * mm:
                    self._draw_text(
                        c, full_desc, desc["x"], desc["y"], desc["size"], centered, bold
                    )
                else:
                    # Разбиваем на две строки
                    line1 = self._truncate_text(c, full_desc, desc["size"], max_w)
                    self._draw_text(c, line1, desc["x"], desc["y"], desc["size"], centered, bold)
                    # Вторая строка (остаток)
                    if "description_2" in layout_config:
                        desc2 = layout_config["description_2"]
                        centered2 = desc2.get("centered", False)
                        bold2 = desc2.get("bold", False)
                        truncated_len = len(line1) - 3 if line1.endswith("...") else len(line1)
                        remaining = full_desc[truncated_len:].strip()
                        if remaining:
                            line2 = self._truncate_text(
                                c, remaining, desc2["size"], desc2.get("max_width", 40)
                            )
                            self._draw_text(
                                c,
                                line2,
                                desc2["x"],
                                desc2["y"],
                                desc2["size"],
                                centered2,
                                bold2,
                            )

        # Артикул - label жирный, value обычный
        if show_article and item.article and "article" in layout_config:
            art = layout_config["article"]
            label_bold = art.get("label_bold", True)
            self._draw_label_value(
                c, "Артикул", item.article, art["x"], art["y"], art["size"], label_bold
            )

        # Бренд
        if show_brand and item.brand and "brand" in layout_config:
            br = layout_config["brand"]
            label_bold = br.get("label_bold", True)
            self._draw_label_value(c, "Бренд", item.brand, br["x"], br["y"], br["size"], label_bold)

        # Размер / Цвет (с жирными labels если label_bold=True)
        if show_size_color and "size_color" in layout_config:
            sc = layout_config["size_color"]
            label_bold = sc.get("label_bold", True)
            x_pos = sc["x"]
            y_pos = sc["y"]
            font_size = sc["size"]

            if item.size:
                if label_bold:
                    self._draw_label_value(c, "Размер", item.size, x_pos, y_pos, font_size, True)
                    # Вычисляем ширину для следующего поля
                    c.setFont(FONT_NAME_BOLD, font_size)
                    x_pos += c.stringWidth(f"Размер: {item.size}  ", FONT_NAME, font_size) / mm
                else:
                    self._draw_text(c, f"Размер: {item.size}", x_pos, y_pos, font_size)
                    c.setFont(FONT_NAME, font_size)
                    x_pos += c.stringWidth(f"Размер: {item.size}  ", FONT_NAME, font_size) / mm

            if item.color:
                if label_bold:
                    self._draw_label_value(c, "Цвет", item.color, x_pos, y_pos, font_size, True)
                else:
                    self._draw_text(c, f"Цвет: {item.color}", x_pos, y_pos, font_size)

        # === Реквизиты (всё обычным шрифтом) ===

        # Импортер
        imp_value = importer or organization
        if show_importer and imp_value and "importer" in layout_config:
            imp = layout_config["importer"]
            label_bold = imp.get("label_bold", False)
            self._draw_label_value(
                c, "Импортер", imp_value, imp["x"], imp["y"], imp["size"], label_bold
            )

        # Производитель
        mfr_value = manufacturer or organization
        if show_manufacturer and mfr_value and "manufacturer" in layout_config:
            mfr = layout_config["manufacturer"]
            label_bold = mfr.get("label_bold", False)
            self._draw_label_value(
                c, "Производитель", mfr_value, mfr["x"], mfr["y"], mfr["size"], label_bold
            )

        # Адрес
        addr_value = organization_address or item.organization_address
        if show_address and addr_value and "address" in layout_config:
            addr = layout_config["address"]
            label_bold = addr.get("label_bold", False)
            max_w = addr.get("max_width", 40)
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

    def _draw_barcode(
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
        bold: bool = False,
    ) -> None:
        """Рисует текст с кириллицей."""
        font = FONT_NAME_BOLD if bold else FONT_NAME
        c.setFont(font, font_size)
        c.setFillColorRGB(0, 0, 0)

        if centered:
            c.drawCentredString(x * mm, y * mm, text)
        else:
            c.drawString(x * mm, y * mm, text)

    def _draw_label_value(
        self,
        c: canvas.Canvas,
        label: str,
        value: str,
        x: float,
        y: float,
        font_size: float,
        label_bold: bool = True,
    ) -> None:
        """Рисует текст в формате 'Label: Value' где label может быть жирным."""
        if label_bold:
            # Рисуем label жирным
            c.setFont(FONT_NAME_BOLD, font_size)
            c.setFillColorRGB(0, 0, 0)
            label_text = f"{label}: "
            c.drawString(x * mm, y * mm, label_text)
            # Вычисляем ширину label для позиционирования value
            label_width = c.stringWidth(label_text, FONT_NAME_BOLD, font_size)
            # Рисуем value обычным шрифтом
            c.setFont(FONT_NAME, font_size)
            c.drawString(x * mm + label_width, y * mm, value)
        else:
            # Всё обычным шрифтом
            c.setFont(FONT_NAME, font_size)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(x * mm, y * mm, f"{label}: {value}")

    def _draw_vertical_line(
        self,
        c: canvas.Canvas,
        x: float,
        y_start: float,
        y_end: float,
        width: float = 0.5,
    ) -> None:
        """Рисует вертикальную линию-разделитель."""
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(width * mm)
        c.line(x * mm, y_start * mm, x * mm, y_end * mm)

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
