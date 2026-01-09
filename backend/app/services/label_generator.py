# backend/app/services/label_generator.py
"""
Генератор этикеток WB + Честный Знак через ReportLab (векторный PDF).

Поддерживает два layout:
- CLASSIC: штрихкод слева, текст слева, DataMatrix справа
- CENTERED: штрихкод по центру, текст по центру, DataMatrix справа

Размеры: 58x40, 58x30, 58x60 мм
"""

import os
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

# Пути к логотипам и шрифтам
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
CHZ_LOGO_PATH = os.path.join(ASSETS_DIR, "chz_logo.png")
EAC_LOGO_PATH = os.path.join(ASSETS_DIR, "eac_logo.png")

# Путь к шрифтам в контейнере Docker
DEJAVU_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEJAVU_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LIBERATION_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
LIBERATION_BOLD_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# Windows шрифты
ARIAL_PATH = "C:/Windows/Fonts/arial.ttf"
ARIAL_BOLD_PATH = "C:/Windows/Fonts/arialbd.ttf"
ARIAL_NARROW_PATH = "C:/Windows/Fonts/ARIALN.TTF"
ARIAL_NARROW_BOLD_PATH = "C:/Windows/Fonts/ARIALNB.TTF"

FONT_NAME = "LabelFont"
FONT_NAME_BOLD = "LabelFont-Bold"

# Флаг инициализации шрифта
_font_registered = False


def _ensure_font_registered() -> None:
    """Регистрирует шрифты для кириллицы. Приоритет: Roboto > PT Sans > DejaVu > системные."""
    global _font_registered
    if _font_registered:
        return

    # Приоритет шрифтов: Arial (Windows), Liberation Sans (Docker/Linux, копия Arial)
    font_options = [
        (ARIAL_PATH, ARIAL_BOLD_PATH, "Arial"),
        (LIBERATION_PATH, LIBERATION_BOLD_PATH, "Liberation Sans"),
        (DEJAVU_PATH, DEJAVU_BOLD_PATH, "DejaVu Sans"),
        (ARIAL_NARROW_PATH, ARIAL_NARROW_BOLD_PATH, "Arial Narrow"),
    ]

    for font_path, bold_path, _name in font_options:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, bold_path))
                else:
                    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, font_path))
                _font_registered = True
                return
            except Exception:
                continue

    # Если ничего не нашли
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
    organization_address: str | None = None  # Используется organization_address для совместимости
    address: str | None = None  # Alias для organization_address (новые API используют это поле)
    importer: str | None = None
    manufacturer: str | None = None
    production_date: str | None = None
    certificate_number: str | None = None


@dataclass
class PreflightErrorInfo:
    """Структурированная ошибка preflight с привязкой к полю."""

    field_id: str | None  # ID поля (organization, name, article и т.д.)
    message: str  # Текст ошибки
    suggestion: str | None  # Рекомендация по исправлению


def parse_preflight_error(error_text: str) -> PreflightErrorInfo:
    """
    Парсит текстовую preflight ошибку и определяет field_id.

    Маппинг ключевых слов на field_id:
    - "Название" → name
    - "Организация" → organization
    - "ИНН" → inn
    - "Адрес" → address
    - "Артикул" → article
    - "Размер" → size
    - "Цвет" → color
    - "Бренд" → brand
    - "Состав" → composition
    - "Страна" → country
    - "Производитель" → manufacturer
    - "Импортер" → importer
    - "Сертификат" → certificate
    - "Текстовый блок" → None (общая ошибка layout)
    - "Строка" → None (общая ошибка)
    - "Контент" → None (общая ошибка)
    """
    error_lower = error_text.lower()
    field_id: str | None = None
    suggestion: str | None = None

    # Определяем field_id по ключевым словам
    # ВАЖНО: порядок проверок имеет значение! Более специфичные проверки идут раньше.
    if "название" in error_lower:
        field_id = "name"
        suggestion = "Сократите название товара"
    elif "организация" in error_lower:
        field_id = "organization"
        suggestion = "Сократите название организации или используйте аббревиатуру"
    elif "адрес" in error_lower:
        field_id = "address"
        suggestion = "Сократите адрес (уберите лишние слова: г., ул., д.)"
    elif "артикул" in error_lower:
        field_id = "article"
        suggestion = "Сократите артикул"
    elif "размер" in error_lower and "цвет" in error_lower:
        # "Размер/цвет" — общая ошибка для обоих полей
        field_id = "size"  # Приоритет — размер
        suggestion = "Сократите размер или цвет"
    elif "размер" in error_lower:
        field_id = "size"
        suggestion = "Сократите значение размера"
    elif "цвет" in error_lower:
        field_id = "color"
        suggestion = "Сократите название цвета"
    elif "бренд" in error_lower:
        field_id = "brand"
        suggestion = "Сократите название бренда"
    elif "состав" in error_lower:
        field_id = "composition"
        suggestion = "Сократите описание состава"
    elif "страна" in error_lower:
        field_id = "country"
        suggestion = "Сократите название страны"
    elif "производитель" in error_lower:
        field_id = "manufacturer"
        suggestion = "Сократите название производителя"
    elif "импортер" in error_lower or "импортёр" in error_lower:
        field_id = "importer"
        suggestion = "Сократите название импортёра"
    elif "сертификат" in error_lower:
        field_id = "certificate"
        suggestion = "Сократите номер сертификата"
    elif "инн" in error_lower:
        # Проверяем ИНН после других полей, т.к. слово "длинный" содержит "инн"
        field_id = "inn"
        suggestion = "Проверьте корректность ИНН"
    elif "текстовый блок" in error_lower or "контент" in error_lower:
        # Общая ошибка layout — нельзя привязать к конкретному полю
        field_id = None
        suggestion = "Сократите текст в нескольких полях"
    elif "строка" in error_lower:
        # Ошибка отдельной строки — пробуем определить поле по содержимому
        field_id = None
        suggestion = "Сократите текст в одном из полей"

    return PreflightErrorInfo(
        field_id=field_id,
        message=error_text,
        suggestion=suggestion,
    )


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
# PROFESSIONAL: Двухколоночный шаблон (только 58x40)
# - Левая колонка: EAC, "ЧЕСТНЫЙ ЗНАК", DataMatrix, код ЧЗ, страна
# - Правая колонка: штрихкод, описание, артикул, бренд, размер/цвет, реквизиты

LAYOUTS = {
    "basic": {
        "58x40": {
            # DataMatrix слева вверху 22мм (минимум по ГОСТу для ЧЗ)
            # Отступы ~1.5мм как у конкурента
            "datamatrix": {"x": 1.5, "y": 16.5, "size": 22},
            # Код ЧЗ текстом (0.5мм между строками)
            # 2мм отступ от логотипа Честный знак
            "chz_code_text": {"x": 1.5, "y": 12.5, "size": 4, "max_width": 22},
            "chz_code_text_2": {"x": 1.5, "y": 10.8, "size": 4, "max_width": 22},
            # Логотипы "ЧЕСТНЫЙ ЗНАК" и EAC слева внизу
            # EAC: y=1.5, height=2.5 → верх на 4мм
            # Честный знак: 1мм отступ от EAC → y=5, height=4.5 → верх на 9.5мм
            "chz_logo": {"x": 1.5, "y": 5, "width": 13, "height": 4.0},  # PNG логотип (увеличен)
            "eac_logo": {"x": 1.5, "y": 1.5, "width": 7, "height": 3},  # PNG логотип (увеличен)
            "serial_number": {"x": 6, "y": 1.5, "size": 7, "bold": False},  # № рядом с EAC
            # === Правая колонка: текст справа от DataMatrix ===
            # ИНН: 1.5мм от верха, жирный шрифт
            "inn": {
                "x": 40,
                "y": 37.3,
                "size": 3.8,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            # Организация: 0.3мм под ИНН, жирный шрифт
            "organization": {
                "x": 40,
                "y": 35.8,
                "size": 3.8,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            # Название крупно (жирный шрифт, 0.5мм между строками)
            "name": {
                "x": 40,
                "y": 29,
                "size": 8.5,
                "max_width": 33,
                "centered": True,
                "bold": True,
            },
            "name_2": {
                "x": 40,
                "y": 25.5,
                "size": 8.5,
                "max_width": 33,
                "centered": True,
                "bold": True,
            },
            # Характеристики — 4 строки (жирный 4.5pt, ~2.1мм между строками)
            "char_line_1": {
                "x": 40,
                "y": 20.5,
                "size": 4.5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            "char_line_2": {
                "x": 40,
                "y": 18.4,
                "size": 4.5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            "char_line_3": {
                "x": 40,
                "y": 16.3,
                "size": 4.5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            "char_line_4": {
                "x": 40,
                "y": 14.2,
                "size": 4.5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            # Штрихкод WB внизу — x=20, до правого края с отступом 1.5мм
            "barcode": {"x": 20, "y": 3.5, "width": 36.5, "height": 9},
            "barcode_text": {"x": 39, "y": 1.5, "size": 4.5, "centered": True, "bold": True},
        },
        "58x30": {
            # DataMatrix слева 22мм (ГОСТ минимум) — занимает почти всю высоту
            # y = 30 - 1.5 (отступ сверху) - 22 = 6.5мм
            "datamatrix": {"x": 1.5, "y": 6.5, "size": 22},
            # Вертикальная линия-разделитель (3мм от DataMatrix)
            "divider": {"x": 26.5, "y_start": 1.5, "y_end": 28.5, "width": 0.8},
            # Код ЧЗ текстом — одна строка мелко, 0.5мм над логотипами
            "chz_code_text": {"x": 1.5, "y": 4.5, "size": 3, "max_width": 22},
            # EAC, ЧЗ логотип и серийный номер внизу (0.5мм между ними)
            # EAC 320x277 (ratio 1.15): height=2.5 → width=2.9
            # CHZ 163x57 (ratio 2.86): height=2.5 → width=7.2
            "eac_logo": {"x": 1.5, "y": 1.5, "width": 2.9, "height": 2.5},
            "chz_logo": {"x": 4.9, "y": 1.5, "width": 7.2, "height": 2.5},  # +0.5мм
            "serial_number": {"x": 12.6, "y": 2, "size": 5, "bold": False},  # чуть вверх
            # === Правая колонка: центр = 43мм (+3мм вправо) ===
            # ИНН: 1.5мм от верха
            "inn": {"x": 43, "y": 27.3, "size": 4, "max_width": 32, "centered": True, "bold": True},
            # Организация: 0.3мм под ИНН
            "organization": {
                "x": 43,
                "y": 25.8,
                "size": 4,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            # Название (две строки, 0.5мм между ними)
            # Правая колонка: от 28мм до 56.5мм = 28.5мм, центр = 42мм
            "name": {"x": 42, "y": 21, "size": 6, "max_width": 28, "centered": True, "bold": True},
            "name_2": {
                "x": 42,
                "y": 18.5,
                "size": 6,
                "max_width": 28,
                "centered": True,
                "bold": True,
            },
            # Характеристики: размер/цвет объединённо (мало места на 58x30)
            "size_color": {
                "x": 43,
                "y": 14.3,
                "size": 4,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            "article": {
                "x": 43,
                "y": 12.4,
                "size": 4,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            # Штрихкод WB внизу — до правого края с отступом 1.5мм
            "barcode": {"x": 30, "y": 3, "width": 26.5, "height": 7},
            "barcode_text": {"x": 43, "y": 1.5, "size": 4, "centered": True, "bold": True},
        },
        "58x60": {
            # DataMatrix слева 22мм (ГОСТ минимум)
            # y = 60 - 1.5 (отступ сверху) - 22 = 36.5мм
            "datamatrix": {"x": 1.5, "y": 36.5, "size": 22},
            # Код ЧЗ текстом (0.5мм между строками)
            "chz_code_text": {"x": 1.5, "y": 32.5, "size": 6, "max_width": 22},
            "chz_code_text_2": {"x": 1.5, "y": 30.8, "size": 6, "max_width": 22},
            # Логотипы слева внизу (ЧЗ 1мм над EAC)
            "chz_logo": {"x": 1.5, "y": 7.5, "width": 15, "height": 6},
            "eac_logo": {"x": 1.5, "y": 1.5, "width": 9, "height": 5},
            "serial_number": {"x": 7.5, "y": 1.5, "size": 7, "bold": False},
            # === Правая колонка: центр = 40мм ===
            # ИНН: 1.5мм от верха
            "inn": {
                "x": 40,
                "y": 57.3,
                "size": 4.5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            # Организация: 0.3мм под ИНН
            "organization": {
                "x": 40,
                "y": 55.8,
                "size": 4.5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            # Название крупно (две строки, 0.5мм между, центр между организацией и цветом)
            "name": {
                "x": 40,
                "y": 39.5,
                "size": 9.5,
                "max_width": 33,
                "centered": True,
                "bold": True,
            },
            "name_2": {
                "x": 40,
                "y": 36,
                "size": 9.5,
                "max_width": 33,
                "centered": True,
                "bold": True,
            },
            # Характеристики — 4 строки (как в 58x40)
            "char_line_1": {
                "x": 40,
                "y": 26,
                "size": 5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            "char_line_2": {
                "x": 40,
                "y": 23.5,
                "size": 5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            "char_line_3": {
                "x": 40,
                "y": 21,
                "size": 5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            "char_line_4": {
                "x": 40,
                "y": 18.5,
                "size": 5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            "char_line_5": {
                "x": 40,
                "y": 16,
                "size": 5,
                "max_width": 32,
                "centered": True,
                "bold": True,
            },
            # Штрихкод WB внизу — до правого края с отступом 1.5мм
            "barcode": {"x": 20, "y": 3.5, "width": 36.5, "height": 9},
            "barcode_text": {"x": 39, "y": 1.5, "size": 4.5, "centered": True, "bold": True},
        },
    },
    "extended": {
        # Расширенный классический — много полей с лейблами, выравнивание по левому краю
        # Только размер 58x40
        "58x40": {
            # === Левая колонка (DataMatrix + ЧЗ) ===
            "datamatrix": {"x": 1.5, "y": 16.5, "size": 22},
            "chz_code_text": {"x": 1.5, "y": 12.5, "size": 4, "max_width": 22},
            "chz_code_text_2": {"x": 1.5, "y": 10.8, "size": 4, "max_width": 22},
            "chz_logo": {"x": 1.5, "y": 5, "width": 13, "height": 4.0},
            "eac_logo": {"x": 1.5, "y": 1.5, "width": 7, "height": 3},
            "serial_number": {"x": 6, "y": 1.5, "size": 7, "bold": False},
            # === Правая колонка (текст с лейблами) ===
            # ИНН и Адрес: центрированы, жирные, 3.5pt, вплотную
            "inn": {
                "x": 40,
                "y": 37.3,
                "size": 3.5,
                "max_width": 31,
                "bold": True,
                "centered": True,
            },
            "address": {
                "x": 40,
                "y": 35.8,
                "size": 3.5,
                "max_width": 31,
                "bold": True,
                "centered": True,
            },
            # Блок полей с лейблами (начинается после отступа ~3мм от адреса)
            "text_block_start_y": 32.8,  # y для первой строки блока
            "text_block_x": 25.5,
            "text_block_size": 5,  # 5pt
            "text_block_line_height": 1.8,  # вплотную
            "text_block_max_width": 31,
            # Штрихкод WB внизу — до правого края с отступом 1.5мм
            "barcode": {"x": 20, "y": 3.5, "width": 36.5, "height": 9},
            "barcode_text": {"x": 39, "y": 1.5, "size": 4.5, "centered": True, "bold": True},
        },
    },
    "professional": {
        # Professional только для 58x40 (много информации)
        # Левая колонка: 24мм (DataMatrix 22мм + отступы)
        # Правая колонка: 32мм (58 - 24 - 2мм отступы)
        "58x40": {
            # === Вертикальная линия-разделитель ===
            "divider": {"x": 24.5, "y_start": 1, "y_end": 39, "width": 0.3},
            # === Левая колонка (x=1.5, ширина 22мм) ===
            # EAC логотип вверху слева
            "eac_logo": {"x": 1.5, "y": 35, "width": 7, "height": 3.5},
            # Серийный номер между EAC и ЧЗ
            "serial_number": {"x": 6, "y": 36, "size": 5, "bold": False},
            # Честный знак логотип — сдвинут правее (в PNG есть padding)
            "chz_logo": {"x": 12, "y": 35, "width": 13, "height": 3.5},
            # DataMatrix 22мм (ГОСТ минимум)
            "datamatrix": {"x": 1.5, "y": 11.5, "size": 22},
            # Код ЧЗ текстом под DataMatrix (0.5мм отступ)
            # Первая строка: по левому краю как DataMatrix
            "chz_code_text": {
                "x": 1.5,
                "y": 10,
                "size": 4,
                "max_width": 22,
                "centered": False,
                "bold": True,
            },
            # Вторая строка: центрировано
            "chz_code_text_2": {
                "x": 12.5,
                "y": 8.5,
                "size": 4,
                "max_width": 22,
                "centered": True,
                "bold": True,
            },
            # Страна внизу — центрировано в левой колонке, жирный
            # Центр левой колонки: (1.5 + 23) / 2 = 12.25мм
            "country": {
                "x": 12.5,
                "y": 1.5,
                "size": 4,
                "max_width": 22,
                "centered": True,
                "bold": True,
            },
            # === Правая колонка (x=26 до 56.5, ширина 30.5мм, центр=41.25мм) ===
            # Штрихкод вверху — на всю ширину правой колонки
            "barcode": {"x": 26, "y": 33, "width": 30.5, "height": 6},
            "barcode_text": {"x": 41.25, "y": 31, "size": 4, "centered": True},
            # Описание (название + размер) - поднято к штрихкоду
            "description": {
                "x": 41.25,
                "y": 29.5,
                "size": 5,
                "max_width": 30,
                "centered": True,
                "bold": True,
            },
            "description_2": {
                "x": 41.25,
                "y": 27,
                "size": 5,
                "max_width": 30,
                "centered": True,
                "bold": True,
            },
            # Поля - плотно без отступов (~2мм между строками)
            "article": {"x": 26, "y": 24, "size": 4, "max_width": 30, "label_bold": True},
            "brand": {"x": 26, "y": 22, "size": 4, "max_width": 30, "label_bold": True},
            "size_color": {"x": 26, "y": 20, "size": 4, "max_width": 30, "label_bold": True},
            # Реквизиты — плотно
            "importer": {"x": 26, "y": 18, "size": 4, "max_width": 30, "label_bold": True},
            "manufacturer": {"x": 26, "y": 16, "size": 4, "max_width": 30, "label_bold": True},
            "address": {"x": 26, "y": 14, "size": 4, "max_width": 30, "label_bold": True},
            "production_date": {"x": 26, "y": 12, "size": 4, "max_width": 30, "label_bold": True},
            # Номер сертификата — отдельная строка внизу
            "certificate": {"x": 26, "y": 10, "size": 4, "max_width": 30, "label_bold": True},
        },
    },
}

# Размеры этикеток в мм
LABEL_SIZES = {
    "58x40": (58, 40),
    "58x30": (58, 30),
    "58x60": (58, 60),
}

# === Адаптивная типографика ===
# Минимальные размеры шрифтов (pt)
MIN_FONT_SIZES = {
    "name": 6.0,  # Название — не меньше 6pt
    "field": 3.5,  # Поля (цвет, размер, артикул) — не меньше 3.5pt
    "inn": 3.0,  # ИНН/организация — не меньше 3pt
}

# Уровни адаптации
ADAPT_NORMAL = 0  # Все поля отдельно, с лейблами
ADAPT_NO_LABELS = 1  # Убираем лейблы (цвет: → просто значение)
ADAPT_MERGE = 2  # Объединяем размер + цвет в одну строку
ADAPT_SHRINK = 3  # Уменьшаем шрифт на 20%

# === Адаптация Professional 58x40 ===
# Константы для правой колонки
PROF_DIVIDER_X = 24.5  # мм — позиция разделителя
PROF_TEXT_LEFT = 26.0  # мм — левая граница текста
PROF_TEXT_RIGHT = 56.5  # мм — правая граница текста
PROF_MAX_TEXT_WIDTH = 30.5  # мм — максимальная ширина текста
PROF_BARCODE_TEXT_Y = 31  # мм — Y координата номера штрихкода
PROF_MIN_MARGIN_BOTTOM = 1.5  # мм — минимальный отступ снизу

# Шрифты Professional
PROF_MAX_NAME_FONT = 6.0  # pt — эталон
PROF_MIN_NAME_FONT = 5.0  # pt — минимум
PROF_MAX_BLOCK_FONT = 5.0  # pt — эталон
PROF_MIN_BLOCK_FONT = 4.0  # pt — минимум

# Отступы Professional
PROF_MAX_GAP_BARCODE_NAME = 4.0  # мм — эталон
PROF_MIN_GAP_BARCODE_NAME = 2.0  # мм — жёсткий минимум
PROF_MAX_GAP_NAME_BLOCK = 5.0  # мм — эталон
PROF_MIN_GAP_NAME_BLOCK = 3.0  # мм — минимум
PROF_MAX_LINE_HEIGHT = 2.0  # мм — эталон
PROF_MIN_LINE_HEIGHT = 1.5  # мм — минимум

# Лимиты строк Professional
PROF_MAX_NAME_LINES = 2  # Название — максимум 2 строки
PROF_MAX_BLOCK_LINES = 10  # Текстовый блок — максимум 10 строк


# === Адаптация Extended 58x40 ===
# Координаты текстового блока
EXT_TEXT_X = 25.5  # мм — левая граница текста
EXT_TEXT_MAX_WIDTH = 31.0  # мм — максимальная ширина текста
EXT_TEXT_START_Y = 32.8  # мм — начало текстового блока (от верха)
EXT_BARCODE_TOP = 12.5  # мм — верх штрихкода (3.5 + 9)
EXT_MIN_GAP_TO_BARCODE = 1.5  # мм — минимальный отступ до штрихкода

# Шрифты Extended
EXT_MAX_FONT = 5.5  # pt — эталон
EXT_MIN_FONT = 4.5  # pt — минимум

# Высота строки Extended
EXT_MAX_LINE_HEIGHT = 2.0  # мм
EXT_MIN_LINE_HEIGHT = 1.5  # мм (при максимуме строк)

# Лимиты Extended
EXT_MAX_LINES = 12  # максимум строк в текстовом блоке
EXT_MAX_ADDRESS_CHARS = 36  # максимум символов в адресе (3.5pt)
EXT_MAX_INN_CHARS = 36  # максимум символов в ИНН (3.5pt)


# === Адаптация Basic 58x60 ===
# Правая колонка
B60_TEXT_CENTER_X = 40  # мм — центр текста
B60_TEXT_MAX_WIDTH = 33  # мм — макс. ширина

# Вертикальные координаты (фиксированные)
B60_ORG_Y = 55.8  # мм — организация
B60_BARCODE_TOP = 12.5  # мм — верх штрихкода (3.5 + 9)
B60_MIN_GAP_TO_BARCODE = 1.5  # мм

# Шрифты Basic 58x60
B60_ORG_FONT = 4.5  # pt — организация (фиксированный)
B60_MAX_NAME_FONT = 9.5  # pt — эталон
B60_MIN_NAME_FONT = 6.0  # pt — минимум
B60_MAX_BLOCK_FONT = 5.0  # pt — эталон
B60_MIN_BLOCK_FONT = 4.5  # pt — минимум

# Высота строки
B60_MAX_LINE_HEIGHT = 2.5  # мм
B60_MIN_LINE_HEIGHT = 2.0  # мм

# Лимиты Basic 58x60
B60_MAX_NAME_LINES = 2  # название максимум 2 строки
B60_MAX_BLOCK_LINES = 4  # текстовый блок максимум 4 строки


# === Адаптация Basic 58x40 ===
# Правая колонка (отступы 1.5мм слева и справа)
B40_DIVIDER_X = 24  # мм — разделитель (левая колонка)
B40_MARGIN_LR = 1.5  # мм — отступы слева и справа
B40_TEXT_LEFT = B40_DIVIDER_X + B40_MARGIN_LR  # 25.5мм
B40_TEXT_RIGHT = 58 - B40_MARGIN_LR  # 56.5мм
B40_TEXT_MAX_WIDTH = B40_TEXT_RIGHT - B40_TEXT_LEFT  # 31мм
B40_TEXT_CENTER_X = (B40_TEXT_LEFT + B40_TEXT_RIGHT) / 2  # 41мм — центр текста

# Вертикальные координаты (фиксированные)
B40_INN_Y = 37.3  # мм — ИНН
B40_ORG_Y = 35.8  # мм — организация
B40_BARCODE_TOP = 12.5  # мм — верх штрихкода (3.5 + 9)
B40_MIN_GAP_TO_BARCODE = 1.5  # мм — минимальный отступ до штрихкода

# Шрифты Basic 58x40 — двунаправленная адаптация
# Название: от 5pt (минимум) до 8.5pt (эталон)
B40_MAX_NAME_FONT = 8.5  # pt — максимум (эталон)
B40_MIN_NAME_FONT = 5.0  # pt — минимум
B40_NAME_FONT_STEPS = [8.5, 7.5, 6.5, 5.5, 5.0]

# Блок: от 4pt (минимум) до 6pt (максимум для коротких текстов)
B40_MAX_BLOCK_FONT = 6.0  # pt — максимум
B40_MIN_BLOCK_FONT = 4.0  # pt — минимум
B40_BLOCK_FONT_STEPS = [6.0, 5.5, 5.0, 4.5, 4.0]

# Организация (фиксированный шрифт 3.8pt)
B40_ORG_FONT = 3.8  # pt

# Высота строки
B40_MAX_LINE_HEIGHT = 2.1  # мм (эталон)
B40_MIN_LINE_HEIGHT = 1.5  # мм (минимум при максимуме строк)

# Лимиты Basic 58x40
B40_MAX_NAME_LINES = 2  # название максимум 2 строки
B40_MAX_BLOCK_LINES = 4  # текстовый блок максимум 4 строки


# === Адаптация Basic 58x30 ===
# Правая колонка (отступы 1.5мм слева и справа)
# Разделитель: 26.5мм
# Левая граница: 26.5 + 1.5 = 28мм
# Правая граница: 58 - 1.5 = 56.5мм
# max_width = 56.5 - 28 = 28.5мм
B30_DIVIDER_X = 26.5  # мм — разделитель
B30_MARGIN_LR = 1.5  # мм — отступы слева и справа
B30_TEXT_LEFT = B30_DIVIDER_X + B30_MARGIN_LR  # 28мм
B30_TEXT_RIGHT = 58 - B30_MARGIN_LR  # 56.5мм
B30_TEXT_MAX_WIDTH = B30_TEXT_RIGHT - B30_TEXT_LEFT  # 28.5мм
B30_TEXT_CENTER_X = (B30_TEXT_LEFT + B30_TEXT_RIGHT) / 2  # 42.25мм — центр текста

# Вертикальные координаты (фиксированные)
B30_INN_Y = 27.3  # мм — ИНН
B30_ORG_Y = 25.8  # мм — организация
B30_BARCODE_TOP = 10  # мм — верх штрихкода (3 + 7)
B30_MIN_GAP_TO_BARCODE = 1.0  # мм — минимальный отступ до штрихкода

# Шрифты Basic 58x30 — двунаправленная адаптация
# Название: от 5pt (минимум) до 6pt (эталон)
B30_MAX_NAME_FONT = 6.0  # pt — максимум (эталон)
B30_MIN_NAME_FONT = 5.0  # pt — минимум
B30_NAME_FONT_STEPS = [6.0, 5.5, 5.0]

# Блок: фиксированный 4pt (мало места)
B30_BLOCK_FONT = 4.0  # pt — фиксированный

# Организация/ИНН (фиксированный шрифт 4pt)
B30_ORG_FONT = 4.0  # pt

# Высота строки блока
B30_BLOCK_LINE_HEIGHT = 1.9  # мм

# Лимиты Basic 58x30
B30_MAX_NAME_LINES = 2  # название максимум 2 строки
B30_MAX_BLOCK_LINES = 2  # текстовый блок максимум 2 строки (size_color + article)


# === Константы левой колонки (динамический расчёт) ===
LEFT_MARGIN = 1.5  # мм — отступ от левого края
TOP_MARGIN = 1.5  # мм — отступ от верхнего края
BOTTOM_MARGIN = 1.5  # мм — отступ от нижнего края
ELEMENT_GAP = 0.5  # мм — зазор между элементами

# DataMatrix
DM_SIZE = 22.0  # мм — размер (ГОСТ минимум для ЧЗ)

# CHZ код текстом
CHZ_CODE_LINE_HEIGHT = 1.7  # мм

# Логотипы
CHZ_LOGO_HEIGHT = 4.0  # мм
EAC_LOGO_HEIGHT = 3.0  # мм


class LeftColumnType:
    """Тип структуры левой колонки."""

    DM_TOP = "dm_top"  # DataMatrix вверху (Basic, Extended)
    LOGOS_TOP = "logos_top"  # Логотипы вверху, DM ниже (Professional)


@dataclass
class LeftColumnLayout:
    """Координаты всех элементов левой колонки."""

    # DataMatrix
    dm_x: float
    dm_y: float
    dm_size: float

    # CHZ код текстом (1-2 строки)
    chz_code_x: float
    chz_code_y: float  # первая строка
    chz_code_y2: float  # вторая строка (если есть)
    chz_code_font: float

    # Логотипы
    chz_logo_x: float
    chz_logo_y: float
    eac_logo_x: float
    eac_logo_y: float

    # Серийный номер
    serial_x: float
    serial_y: float


# Маппинг шаблонов на тип левой колонки
LAYOUT_TYPES_MAP = {
    "basic": {
        "58x30": LeftColumnType.DM_TOP,
        "58x40": LeftColumnType.DM_TOP,
        "58x60": LeftColumnType.DM_TOP,
    },
    "extended": {
        "58x40": LeftColumnType.DM_TOP,  # только 58x40
    },
    "professional": {
        "58x40": LeftColumnType.LOGOS_TOP,  # только 58x40
    },
}


def _get_chz_font_for_size(size: str) -> float:
    """Размер шрифта CHZ кода в зависимости от размера этикетки."""
    return {
        "58x30": 3.0,
        "58x40": 4.0,
        "58x60": 6.0,
    }.get(size, 4.0)


def _calc_dm_top(height_mm: float, size: str) -> LeftColumnLayout:
    """Расчёт для Basic/Extended — DataMatrix вверху."""
    # === DataMatrix (прижат к верхнему левому углу) ===
    dm_x = LEFT_MARGIN
    dm_y = height_mm - TOP_MARGIN - DM_SIZE

    # === CHZ код текстом (под DataMatrix) ===
    chz_font = _get_chz_font_for_size(size)
    chz_line_h = chz_font * 0.4

    chz_code_y = dm_y - ELEMENT_GAP - chz_line_h
    chz_code_y2 = chz_code_y - chz_line_h - 0.3

    # === Логотипы (прижаты к низу) ===
    eac_y = BOTTOM_MARGIN
    chz_logo_y = eac_y + EAC_LOGO_HEIGHT + ELEMENT_GAP

    # === Серийный номер (рядом с EAC) ===
    serial_x = LEFT_MARGIN + 4.5
    serial_y = BOTTOM_MARGIN

    return LeftColumnLayout(
        dm_x=dm_x,
        dm_y=dm_y,
        dm_size=DM_SIZE,
        chz_code_x=LEFT_MARGIN,
        chz_code_y=chz_code_y,
        chz_code_y2=chz_code_y2,
        chz_code_font=chz_font,
        chz_logo_x=LEFT_MARGIN,
        chz_logo_y=chz_logo_y,
        eac_logo_x=LEFT_MARGIN,
        eac_logo_y=eac_y,
        serial_x=serial_x,
        serial_y=serial_y,
    )


def _calc_logos_top(height_mm: float, size: str) -> LeftColumnLayout:
    """Расчёт для Professional — логотипы вверху, DataMatrix ниже."""
    # Professional использует увеличенные логотипы и gap
    prof_eac_height = 3.5  # мм — EAC для professional больше
    prof_gap = 1.5  # мм — gap между DM и логотипами

    # === Логотипы (прижаты к верху) ===
    eac_y = height_mm - TOP_MARGIN - prof_eac_height
    chz_logo_y = eac_y
    serial_y = eac_y + 1
    serial_x = LEFT_MARGIN + 4.5

    # === DataMatrix (под логотипами) ===
    dm_x = LEFT_MARGIN
    dm_y = eac_y - prof_gap - DM_SIZE

    # === CHZ код текстом (под DataMatrix) ===
    chz_font = _get_chz_font_for_size(size)
    chz_line_h = chz_font * 0.4

    chz_code_y = dm_y - ELEMENT_GAP - chz_line_h
    chz_code_y2 = chz_code_y - chz_line_h - 0.3

    return LeftColumnLayout(
        dm_x=dm_x,
        dm_y=dm_y,
        dm_size=DM_SIZE,
        chz_code_x=LEFT_MARGIN,
        chz_code_y=chz_code_y,
        chz_code_y2=chz_code_y2,
        chz_code_font=chz_font,
        chz_logo_x=LEFT_MARGIN + 10.5,  # ЧЗ лого сдвинут вправо (12мм от края)
        chz_logo_y=chz_logo_y,
        eac_logo_x=LEFT_MARGIN,
        eac_logo_y=eac_y,
        serial_x=serial_x,
        serial_y=serial_y,
    )


def calculate_left_column(layout: str, size: str) -> LeftColumnLayout:
    """
    Рассчитывает координаты всех элементов левой колонки.

    Гарантирует:
    - DataMatrix прижат к углу с отступом 1.5мм
    - Элементы не перекрываются
    - Консистентность между шаблонами
    """
    # Валидация
    if layout not in LAYOUT_TYPES_MAP:
        raise ValueError(f"Неизвестный layout: {layout}")

    if size not in LAYOUT_TYPES_MAP[layout]:
        supported = list(LAYOUT_TYPES_MAP[layout].keys())
        raise ValueError(f"Размер {size} не поддерживается для {layout}. Доступные: {supported}")

    height_mm = float(size.split("x")[1])
    layout_type = LAYOUT_TYPES_MAP[layout][size]

    if layout_type == LeftColumnType.DM_TOP:
        return _calc_dm_top(height_mm, size)
    else:
        return _calc_logos_top(height_mm, size)


@dataclass
class AdaptiveTextBlock:
    """Результат адаптации текстового блока."""

    lines: list[tuple[str, float, bool]]  # (текст, размер шрифта, bold)
    adaptation_level: int


def _calculate_text_height(
    lines_count: int,
    font_size: float,
    line_spacing_mm: float = 0.5,
) -> float:
    """Рассчитывает высоту текстового блока в мм."""
    # font_size в pt → mm: 1pt ≈ 0.353mm
    line_height_mm = font_size * 0.353 + line_spacing_mm
    return lines_count * line_height_mm


def _adapt_fields_for_space(
    item: "LabelItem",
    available_height_mm: float,
    base_font_size: float,
    show_name: bool,
    show_size: bool,
    show_color: bool,
    show_article: bool,
    show_organization: bool,
    show_inn: bool,
    organization: str | None,
    inn: str | None,
) -> AdaptiveTextBlock:
    """
    Адаптирует поля этикетки под доступное место.

    Стратегия (от нормальной к компактной):
    1. Все поля отдельно, с лейблами
    2. Убираем лейблы
    3. Объединяем размер + цвет
    4. Уменьшаем шрифт
    """
    lines: list[tuple[str, float, bool]] = []

    # === Собираем контент ===
    inn_text = f"ИНН: {inn}" if show_inn and inn else None
    org_text = organization if show_organization and organization else None
    name_text = item.name if show_name and item.name else None
    color_text = item.color if show_color and item.color else None
    size_text = item.size if show_size and item.size else None
    article_text = item.article if show_article and item.article else None

    # === Level 0: Normal — все поля отдельно с лейблами ===
    def build_normal() -> list[tuple[str, float, bool]]:
        result = []
        small_size = base_font_size * 0.7
        if inn_text:
            result.append((inn_text, small_size, True))
        if org_text:
            result.append((org_text, small_size, True))
        if name_text:
            result.append((name_text, base_font_size, True))
        if color_text:
            result.append((f"цвет: {color_text}", base_font_size * 0.6, True))
        if size_text:
            result.append((f"размер: {size_text}", base_font_size * 0.6, True))
        if article_text:
            result.append((f"арт.: {article_text}", base_font_size * 0.6, True))
        return result

    # === Level 1: No labels — убираем лейблы ===
    def build_no_labels() -> list[tuple[str, float, bool]]:
        result = []
        small_size = base_font_size * 0.7
        if inn_text:
            result.append((inn_text, small_size, True))
        if org_text:
            result.append((org_text, small_size, True))
        if name_text:
            result.append((name_text, base_font_size, True))
        if color_text:
            result.append((color_text, base_font_size * 0.6, True))
        if size_text:
            result.append((size_text, base_font_size * 0.6, True))
        if article_text:
            result.append((article_text, base_font_size * 0.6, True))
        return result

    # === Level 2: Merge — объединяем размер + цвет ===
    def build_merged() -> list[tuple[str, float, bool]]:
        result = []
        small_size = base_font_size * 0.7
        if inn_text:
            result.append((inn_text, small_size, True))
        if org_text:
            result.append((org_text, small_size, True))
        if name_text:
            result.append((name_text, base_font_size, True))
        # Объединяем цвет и размер
        size_color_parts = []
        if size_text:
            size_color_parts.append(size_text)
        if color_text:
            size_color_parts.append(color_text)
        if size_color_parts:
            result.append((" / ".join(size_color_parts), base_font_size * 0.6, True))
        if article_text:
            result.append((article_text, base_font_size * 0.6, True))
        return result

    # === Level 3: Shrink — уменьшаем шрифт на 20% ===
    def build_shrunk() -> list[tuple[str, float, bool]]:
        shrink_factor = 0.8
        result = []
        small_size = base_font_size * 0.7 * shrink_factor
        if inn_text:
            result.append((inn_text, max(small_size, MIN_FONT_SIZES["inn"]), True))
        if org_text:
            result.append((org_text, max(small_size, MIN_FONT_SIZES["inn"]), True))
        if name_text:
            result.append(
                (name_text, max(base_font_size * shrink_factor, MIN_FONT_SIZES["name"]), True)
            )
        size_color_parts = []
        if size_text:
            size_color_parts.append(size_text)
        if color_text:
            size_color_parts.append(color_text)
        if size_color_parts:
            result.append(
                (
                    " / ".join(size_color_parts),
                    max(base_font_size * 0.6 * shrink_factor, MIN_FONT_SIZES["field"]),
                    True,
                )
            )
        if article_text:
            result.append(
                (
                    article_text,
                    max(base_font_size * 0.6 * shrink_factor, MIN_FONT_SIZES["field"]),
                    True,
                )
            )
        return result

    # === Выбираем уровень адаптации ===
    for level, builder in enumerate([build_normal, build_no_labels, build_merged, build_shrunk]):
        lines = builder()
        if not lines:
            return AdaptiveTextBlock(lines=[], adaptation_level=level)

        # Рассчитываем высоту
        total_height = sum(_calculate_text_height(1, size) for _, size, _ in lines)
        if total_height <= available_height_mm:
            return AdaptiveTextBlock(lines=lines, adaptation_level=level)

    # Если даже shrunk не помещается — возвращаем его
    return AdaptiveTextBlock(lines=lines, adaptation_level=ADAPT_SHRINK)


# === Функции адаптации Professional 58x40 ===


def _wrap_text_professional(
    text: str, font_name: str, font_size: float, max_width_mm: float
) -> list[str]:
    """Переносит текст по словам для Professional шаблона."""
    max_width_pt = max_width_mm * mm
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        width = pdfmetrics.stringWidth(test_line, font_name, font_size)

        if width <= max_width_pt:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def _collect_professional_block_lines(
    font_size: float,
    item: "LabelItem",
    organization: str | None,
    organization_address: str | None,
    importer: str | None,
    manufacturer: str | None,
    production_date: str | None,
    certificate_number: str | None,
    show_article: bool,
    show_brand: bool,
    show_size: bool,
    show_color: bool,
    show_importer: bool,
    show_manufacturer: bool,
    show_address: bool,
    show_production_date: bool,
    show_certificate: bool,
    merge_size_color: bool = False,
) -> list[str]:
    """
    Собирает все строки текстового блока Professional с переносами.

    Args:
        merge_size_color: Если True — объединяет размер и цвет в формат "S / Белый"
                          Если False — показывает "Размер: S  Цвет: Белый"
    """
    lines = []
    font = FONT_NAME_BOLD

    # Артикул
    if show_article and item.article:
        text = f"Артикул: {item.article}"
        wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
        lines.extend(wrapped)

    # Бренд
    if show_brand and item.brand:
        text = f"Бренд: {item.brand}"
        wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
        lines.extend(wrapped)

    # Размер / Цвет — адаптивное объединение
    if merge_size_color:
        # Компактный формат "S / Белый"
        parts = []
        if show_size and item.size:
            parts.append(item.size)
        if show_color and item.color:
            parts.append(item.color)
        if parts:
            text = " / ".join(parts)
            wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
            lines.extend(wrapped)
    else:
        # Стандартный формат "Размер: S  Цвет: Белый"
        parts = []
        if show_size and item.size:
            parts.append(f"Размер: {item.size}")
        if show_color and item.color:
            parts.append(f"Цвет: {item.color}")
        if parts:
            text = "  ".join(parts)
            wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
            lines.extend(wrapped)

    # Импортер
    imp_value = importer or organization
    if show_importer and imp_value:
        text = f"Импортер: {imp_value}"
        wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
        lines.extend(wrapped)

    # Производитель
    mfr_value = manufacturer or organization
    if show_manufacturer and mfr_value:
        text = f"Производитель: {mfr_value}"
        wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
        lines.extend(wrapped)

    # Адрес (поддержка многострочного через \n)
    addr_value = organization_address or item.organization_address
    if show_address and addr_value:
        addr_lines = addr_value.split("\n")
        for i, line in enumerate(addr_lines):
            prefix = "Адрес: " if i == 0 else ""
            text = f"{prefix}{line}"
            wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
            lines.extend(wrapped)

    # Дата производства
    date_value = production_date or item.production_date
    if show_production_date and date_value:
        text = f"Дата производства: {date_value}"
        wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
        lines.extend(wrapped)

    # Номер сертификата
    cert_value = certificate_number or item.certificate_number
    if show_certificate and cert_value:
        text = f"Номер сертификата: {cert_value}"
        wrapped = _wrap_text_professional(text, font, font_size, PROF_MAX_TEXT_WIDTH)
        lines.extend(wrapped)

    return lines


@dataclass
class ProfessionalLayout:
    """Результат расчёта адаптивного layout для Professional 58x40."""

    fits: bool
    name_font: float
    block_font: float
    gap_barcode_name: float
    gap_name_block: float
    line_height: float
    name_lines: list[str]
    block_lines: list[str]
    name_top_y: float  # Y координата верхней строки названия
    block_top_y: float  # Y координата верхней строки блока
    preflight_errors: list[str]


def _calculate_professional_layout(
    item: "LabelItem",
    organization: str | None,
    organization_address: str | None,
    importer: str | None,
    manufacturer: str | None,
    production_date: str | None,
    certificate_number: str | None,
    show_name: bool,
    show_article: bool,
    show_brand: bool,
    show_size: bool,
    show_color: bool,
    show_importer: bool,
    show_manufacturer: bool,
    show_address: bool,
    show_production_date: bool,
    show_certificate: bool,
) -> ProfessionalLayout:
    """
    Рассчитывает адаптивный layout для Professional 58x40.

    Алгоритм:
    1. Проверяем лимиты строк с минимальным шрифтом
    2. Пробуем эталонные параметры
    3. Если не влезает — уменьшаем отступы
    4. Если не влезает — уменьшаем шрифты
    5. Если всё равно не влезает — preflight error
    """
    preflight_errors = []

    # === Проверка лимитов строк ===
    name_text = item.name or ""

    # Проверяем с минимальным шрифтом (больше символов на строку)
    name_lines_min = _wrap_text_professional(
        name_text, FONT_NAME_BOLD, PROF_MIN_NAME_FONT, PROF_MAX_TEXT_WIDTH
    )
    block_lines_min = _collect_professional_block_lines(
        PROF_MIN_BLOCK_FONT,
        item,
        organization,
        organization_address,
        importer,
        manufacturer,
        production_date,
        certificate_number,
        show_article,
        show_brand,
        show_size,
        show_color,
        show_importer,
        show_manufacturer,
        show_address,
        show_production_date,
        show_certificate,
    )

    if len(name_lines_min) > PROF_MAX_NAME_LINES:
        preflight_errors.append(
            f"Название слишком длинное: {len(name_lines_min)} строк (макс. {PROF_MAX_NAME_LINES})"
        )

    if len(block_lines_min) > PROF_MAX_BLOCK_LINES:
        preflight_errors.append(
            f"Текстовый блок: {len(block_lines_min)} строк (макс. {PROF_MAX_BLOCK_LINES})"
        )

    if preflight_errors:
        return ProfessionalLayout(
            fits=False,
            name_font=PROF_MIN_NAME_FONT,
            block_font=PROF_MIN_BLOCK_FONT,
            gap_barcode_name=PROF_MIN_GAP_BARCODE_NAME,
            gap_name_block=PROF_MIN_GAP_NAME_BLOCK,
            line_height=PROF_MIN_LINE_HEIGHT,
            name_lines=name_lines_min if show_name else [],
            block_lines=block_lines_min,
            name_top_y=0,
            block_top_y=0,
            preflight_errors=preflight_errors,
        )

    # === Эталонные параметры ===
    name_font = PROF_MAX_NAME_FONT
    block_font = PROF_MAX_BLOCK_FONT
    gap_bn = PROF_MAX_GAP_BARCODE_NAME
    gap_nb = PROF_MAX_GAP_NAME_BLOCK
    line_height = PROF_MAX_LINE_HEIGHT

    name_lines = (
        _wrap_text_professional(name_text, FONT_NAME_BOLD, name_font, PROF_MAX_TEXT_WIDTH)
        if show_name
        else []
    )
    block_lines = _collect_professional_block_lines(
        block_font,
        item,
        organization,
        organization_address,
        importer,
        manufacturer,
        production_date,
        certificate_number,
        show_article,
        show_brand,
        show_size,
        show_color,
        show_importer,
        show_manufacturer,
        show_address,
        show_production_date,
        show_certificate,
    )

    def check_fits(n_lines, b_lines, n_font, gap_bn_, gap_nb_, lh_) -> bool:
        """Проверяет влезает ли контент."""
        name_height = len(n_lines) * (n_font * 0.353 + 0.5)
        block_height = len(b_lines) * lh_
        total = gap_bn_ + name_height + gap_nb_ + block_height + PROF_MIN_MARGIN_BOTTOM
        return total <= PROF_BARCODE_TEXT_Y

    def calc_positions(n_lines, b_lines, n_font, gap_nb_, lh_):
        """Рассчитывает Y координаты."""
        # Блок от низа
        block_top_y = PROF_MIN_MARGIN_BOTTOM + (len(b_lines) - 1) * lh_

        # Название центрируем между barcode_text и блоком
        barcode_bottom = PROF_BARCODE_TEXT_Y - 1  # 30мм
        name_line_h = n_font * 0.353 + 0.5
        name_total_height = len(n_lines) * name_line_h if n_lines else 0

        available_for_name = barcode_bottom - block_top_y - gap_nb_
        name_center = block_top_y + gap_nb_ + available_for_name / 2
        name_top_y = name_center + name_total_height / 2 - name_line_h / 2 if n_lines else 0

        return name_top_y, block_top_y

    # === Шаг 1: Эталонные параметры ===
    if check_fits(name_lines, block_lines, name_font, gap_bn, gap_nb, line_height):
        name_top_y, block_top_y = calc_positions(
            name_lines, block_lines, name_font, gap_nb, line_height
        )
        return ProfessionalLayout(
            fits=True,
            name_font=name_font,
            block_font=block_font,
            gap_barcode_name=gap_bn,
            gap_name_block=gap_nb,
            line_height=line_height,
            name_lines=name_lines,
            block_lines=block_lines,
            name_top_y=name_top_y,
            block_top_y=block_top_y,
            preflight_errors=[],
        )

    # === Шаг 2: Уменьшаем отступы ===
    gap_bn = PROF_MIN_GAP_BARCODE_NAME
    gap_nb = PROF_MIN_GAP_NAME_BLOCK
    line_height = 1.8

    if check_fits(name_lines, block_lines, name_font, gap_bn, gap_nb, line_height):
        name_top_y, block_top_y = calc_positions(
            name_lines, block_lines, name_font, gap_nb, line_height
        )
        return ProfessionalLayout(
            fits=True,
            name_font=name_font,
            block_font=block_font,
            gap_barcode_name=gap_bn,
            gap_name_block=gap_nb,
            line_height=line_height,
            name_lines=name_lines,
            block_lines=block_lines,
            name_top_y=name_top_y,
            block_top_y=block_top_y,
            preflight_errors=[],
        )

    # === Шаг 3: Уменьшаем шрифты ===
    name_font = PROF_MIN_NAME_FONT
    block_font = PROF_MIN_BLOCK_FONT
    line_height = PROF_MIN_LINE_HEIGHT

    name_lines = (
        _wrap_text_professional(name_text, FONT_NAME_BOLD, name_font, PROF_MAX_TEXT_WIDTH)
        if show_name
        else []
    )
    block_lines = _collect_professional_block_lines(
        block_font,
        item,
        organization,
        organization_address,
        importer,
        manufacturer,
        production_date,
        certificate_number,
        show_article,
        show_brand,
        show_size,
        show_color,
        show_importer,
        show_manufacturer,
        show_address,
        show_production_date,
        show_certificate,
        merge_size_color=False,
    )

    if check_fits(name_lines, block_lines, name_font, gap_bn, gap_nb, line_height):
        name_top_y, block_top_y = calc_positions(
            name_lines, block_lines, name_font, gap_nb, line_height
        )
        return ProfessionalLayout(
            fits=True,
            name_font=name_font,
            block_font=block_font,
            gap_barcode_name=gap_bn,
            gap_name_block=gap_nb,
            line_height=line_height,
            name_lines=name_lines,
            block_lines=block_lines,
            name_top_y=name_top_y,
            block_top_y=block_top_y,
            preflight_errors=[],
        )

    # === Шаг 4: Объединяем размер и цвет в одну строку ===
    # Адаптивное объединение: "Размер: S  Цвет: Белый" -> "S / Белый"
    block_lines_merged = _collect_professional_block_lines(
        block_font,
        item,
        organization,
        organization_address,
        importer,
        manufacturer,
        production_date,
        certificate_number,
        show_article,
        show_brand,
        show_size,
        show_color,
        show_importer,
        show_manufacturer,
        show_address,
        show_production_date,
        show_certificate,
        merge_size_color=True,
    )

    if check_fits(name_lines, block_lines_merged, name_font, gap_bn, gap_nb, line_height):
        name_top_y, block_top_y = calc_positions(
            name_lines, block_lines_merged, name_font, gap_nb, line_height
        )
        return ProfessionalLayout(
            fits=True,
            name_font=name_font,
            block_font=block_font,
            gap_barcode_name=gap_bn,
            gap_name_block=gap_nb,
            line_height=line_height,
            name_lines=name_lines,
            block_lines=block_lines_merged,
            name_top_y=name_top_y,
            block_top_y=block_top_y,
            preflight_errors=[],
        )

    # === Не влезает даже с минимумом и объединением ===
    return ProfessionalLayout(
        fits=False,
        name_font=name_font,
        block_font=block_font,
        gap_barcode_name=gap_bn,
        gap_name_block=gap_nb,
        line_height=line_height,
        name_lines=name_lines,
        block_lines=block_lines_merged,
        name_top_y=0,
        block_top_y=0,
        preflight_errors=["Контент не влезает даже с минимальными параметрами"],
    )


# === Extended 58x40 адаптивные функции ===


@dataclass
class ExtendedLayout:
    """Результат расчёта layout для Extended 58x40."""

    fits: bool  # True если контент влезает
    lines: list[str]  # Все строки текста
    font_size: float  # Размер шрифта
    line_height: float  # Высота строки в мм
    start_y: float  # Y координата первой строки
    preflight_errors: list[str]  # Ошибки если не влезает


def _wrap_text_extended(text: str, font_size: float, max_width_mm: float) -> list[str]:
    """
    Переносит текст по словам для Extended шаблона.
    Возвращает список строк.
    """
    max_width_pt = max_width_mm * mm
    words = text.split()

    if not words:
        return []

    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = current_line + " " + word
        if pdfmetrics.stringWidth(test_line, FONT_NAME, font_size) <= max_width_pt:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def _collect_extended_block_lines(
    item: "LabelItem",
    font_size: float,
    custom_lines: list[str] | None,
    show_name: bool = True,
    show_article: bool = True,
    show_size: bool = True,
    show_color: bool = True,
    show_brand: bool = False,
    show_composition: bool = True,
    show_country: bool = False,
    show_manufacturer: bool = True,
) -> list[str]:
    """
    Собирает все строки текстового блока Extended с переносами.

    Доступные поля для Extended шаблона (согласно таблице):
    - ИНН, Название, Артикул, Размер, Цвет, Бренд, Состав, Страна, Производитель, Адрес

    Дата производства недоступна для Extended (только Professional).
    """
    lines = []

    # Название (с лейблом)
    if show_name and item.name:
        name_lines = _wrap_text_extended(f"Название: {item.name}", font_size, EXT_TEXT_MAX_WIDTH)
        lines.extend(name_lines)

    # Бренд
    if show_brand and item.brand:
        brand_lines = _wrap_text_extended(f"Бренд: {item.brand}", font_size, EXT_TEXT_MAX_WIDTH)
        lines.extend(brand_lines)

    # Состав (с лейблом)
    if show_composition and item.composition:
        comp_lines = _wrap_text_extended(
            f"Состав: {item.composition}", font_size, EXT_TEXT_MAX_WIDTH
        )
        lines.extend(comp_lines)

    # Артикул (с лейблом)
    if show_article and item.article:
        art_lines = _wrap_text_extended(f"Артикул: {item.article}", font_size, EXT_TEXT_MAX_WIDTH)
        lines.extend(art_lines)

    # Размер и цвет на одной строке (адаптивно объединённые)
    size_color_parts = []
    if show_size and item.size:
        size_color_parts.append(f"Размер: {item.size}")
    if show_color and item.color:
        size_color_parts.append(f"Цвет: {item.color}")
    if size_color_parts:
        sc_text = ", ".join(size_color_parts)
        sc_lines = _wrap_text_extended(sc_text, font_size, EXT_TEXT_MAX_WIDTH)
        lines.extend(sc_lines)

    # Страна
    if show_country and item.country:
        country_lines = _wrap_text_extended(
            f"Страна: {item.country}", font_size, EXT_TEXT_MAX_WIDTH
        )
        lines.extend(country_lines)

    # Производитель (на 2 строки: лейбл + значение)
    if show_manufacturer and item.manufacturer:
        lines.append("Производитель:")
        mfr_lines = _wrap_text_extended(item.manufacturer, font_size, EXT_TEXT_MAX_WIDTH)
        lines.extend(mfr_lines)

    # Кастомные строки
    if custom_lines:
        for custom in custom_lines:
            custom_wrapped = _wrap_text_extended(f"+ {custom}", font_size, EXT_TEXT_MAX_WIDTH)
            lines.extend(custom_wrapped)

    return lines


def _calculate_extended_layout(
    item: "LabelItem",
    custom_lines: list[str] | None,
    address: str | None,
    show_name: bool = True,
    show_article: bool = True,
    show_size: bool = True,
    show_color: bool = True,
    show_brand: bool = False,
    show_composition: bool = True,
    show_country: bool = False,
    show_manufacturer: bool = True,
) -> ExtendedLayout:
    """
    Рассчитывает адаптивный layout для Extended 58x40.

    Алгоритм:
    1. Проверяем длину адреса (preflight)
    2. Пробуем эталонный шрифт (5.5pt)
    3. Если строк > max_lines, уменьшаем шрифт до минимума (4.5pt)
    4. Если всё равно > max_lines, возвращаем preflight error
    5. Рассчитываем line_height чтобы последняя строка была на MIN_GAP от штрихкода
    """
    preflight_errors = []

    # === Проверка адреса (фиксированный 3.5pt) ===
    if address:
        # Адрес включает "Адрес: " префикс
        full_address = f"Адрес: {address}"
        if len(full_address) > EXT_MAX_ADDRESS_CHARS:
            preflight_errors.append(
                f"Адрес слишком длинный: {len(full_address)} символов (макс. {EXT_MAX_ADDRESS_CHARS})"
            )

    # Формируем kwargs для collect функции
    collect_kwargs = {
        "show_name": show_name,
        "show_article": show_article,
        "show_size": show_size,
        "show_color": show_color,
        "show_brand": show_brand,
        "show_composition": show_composition,
        "show_country": show_country,
        "show_manufacturer": show_manufacturer,
    }

    # === Пробуем эталонный шрифт ===
    font_size = EXT_MAX_FONT
    lines = _collect_extended_block_lines(item, font_size, custom_lines, **collect_kwargs)

    # Если много строк - уменьшаем шрифт
    if len(lines) > EXT_MAX_LINES:
        font_size = EXT_MIN_FONT
        lines = _collect_extended_block_lines(item, font_size, custom_lines, **collect_kwargs)

    # Проверяем лимит строк
    if len(lines) > EXT_MAX_LINES:
        preflight_errors.append(
            f"Текстовый блок: {len(lines)} строк (макс. {EXT_MAX_LINES}). Сократите текст!"
        )

    # Если есть preflight ошибки — не генерируем
    if preflight_errors:
        return ExtendedLayout(
            fits=False,
            lines=[],
            font_size=font_size,
            line_height=EXT_MIN_LINE_HEIGHT,
            start_y=EXT_TEXT_START_Y,
            preflight_errors=preflight_errors,
        )

    # === Рассчитываем line_height ===
    if len(lines) > 1:
        target_last_y = EXT_BARCODE_TOP + EXT_MIN_GAP_TO_BARCODE
        calculated_lh = (EXT_TEXT_START_Y - target_last_y) / (len(lines) - 1)
        line_height = max(EXT_MIN_LINE_HEIGHT, min(EXT_MAX_LINE_HEIGHT, calculated_lh))
    else:
        line_height = EXT_MAX_LINE_HEIGHT

    return ExtendedLayout(
        fits=True,
        lines=lines,
        font_size=font_size,
        line_height=line_height,
        start_y=EXT_TEXT_START_Y,
        preflight_errors=[],
    )


# === Basic 58x60 адаптивные функции ===


@dataclass
class Basic60Layout:
    """Результат расчёта layout для Basic 58x60."""

    fits: bool  # True если контент влезает
    name_lines: list[str]  # Строки названия
    block_lines: list[str]  # Строки текстового блока
    name_font: float  # Размер шрифта названия
    block_font: float  # Размер шрифта блока
    line_height: float  # Высота строки блока в мм
    name_top_y: float  # Y первой строки названия
    block_top_y: float  # Y первой строки блока
    preflight_errors: list[str]  # Ошибки если не влезает


def _wrap_text_basic60(
    text: str,
    font_name: str,
    font_size: float,
    max_width_mm: float,
) -> list[str]:
    """Переносит текст по словам для Basic 58x60."""
    max_width_pt = max_width_mm * mm
    words = text.split()

    if not words:
        return []

    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = current_line + " " + word
        if pdfmetrics.stringWidth(test_line, font_name, font_size) <= max_width_pt:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def _collect_basic60_block_lines(
    item: "LabelItem",
    font_size: float,
    show_size: bool = True,
    show_color: bool = True,
    show_article: bool = True,
    show_composition: bool = False,
    show_brand: bool = False,
    show_country: bool = False,
    merge_size_color: bool = False,
) -> list[str]:
    """
    Собирает строки текстового блока Basic 58x60.

    Args:
        item: Данные товара
        font_size: Размер шрифта
        show_size: Показывать размер
        show_color: Показывать цвет
        show_article: Показывать артикул
        show_composition: Показывать состав (доступен для 58x60)
        show_brand: Показывать бренд
        show_country: Показывать страну
        merge_size_color: Объединять размер и цвет в одну строку при нехватке места
    """
    lines = []

    # Размер и цвет — адаптивное объединение
    if merge_size_color:
        # Объединённый формат "S / Белый" — для экономии места
        parts = []
        if show_size and item.size:
            parts.append(item.size)
        if show_color and item.color:
            parts.append(item.color)
        if parts:
            lines.append(" / ".join(parts))
    else:
        # Раздельные строки "Цвет: X" и "Размер: Y"
        if show_color and item.color:
            lines.append(f"Цвет: {item.color}")
        if show_size and item.size:
            lines.append(f"Размер: {item.size}")

    # Артикул
    if show_article and item.article:
        lines.append(f"Артикул: {item.article}")

    # Бренд
    if show_brand and item.brand:
        lines.append(f"Бренд: {item.brand}")

    # Страна
    if show_country and item.country:
        lines.append(f"Страна: {item.country}")

    # Состав (может быть длинным — переносим)
    if show_composition and item.composition:
        comp_lines = _wrap_text_basic60(
            f"Состав: {item.composition}",
            FONT_NAME_BOLD,
            font_size,
            B60_TEXT_MAX_WIDTH - 2,  # Немного меньше для центрирования
        )
        lines.extend(comp_lines)

    return lines


def _calculate_basic60_layout(
    item: "LabelItem",
    organization: str | None = None,
    show_size: bool = True,
    show_color: bool = True,
    show_article: bool = True,
    show_composition: bool = False,
    show_brand: bool = False,
    show_country: bool = False,
) -> Basic60Layout:
    """
    Рассчитывает адаптивный layout для Basic 58x60.

    Алгоритм:
    1. Проверяем ширину организации
    2. Пробуем раздельные строки для размера/цвета
    3. Если не влезает — объединяем размер и цвет в одну строку
    4. Рассчитываем позицию блока (прижат к 1.5мм от штрихкода)
    5. Центрируем название между организацией и блоком
    """
    preflight_errors = []

    # === Проверка организации (ширина при фиксированном шрифте 4.5pt) ===
    org_text = organization or ""
    if org_text:
        org_width_pt = pdfmetrics.stringWidth(org_text, FONT_NAME_BOLD, B60_ORG_FONT)
        org_width_mm = org_width_pt / mm
        if org_width_mm > B60_TEXT_MAX_WIDTH:
            preflight_errors.append(
                f"Организация: {org_width_mm:.1f}мм (макс. {B60_TEXT_MAX_WIDTH}мм)"
            )

    # === Проверяем с минимальными шрифтами ===
    name_text = item.name or ""
    name_lines_min = _wrap_text_basic60(
        name_text, FONT_NAME_BOLD, B60_MIN_NAME_FONT, B60_TEXT_MAX_WIDTH
    )

    if len(name_lines_min) > B60_MAX_NAME_LINES:
        preflight_errors.append(
            f"Название: {len(name_lines_min)} строк (макс. {B60_MAX_NAME_LINES})"
        )

    # === Адаптивное объединение size/color ===
    # Сначала пробуем раздельные строки
    merge_size_color = False
    block_lines_separate = _collect_basic60_block_lines(
        item,
        B60_MIN_BLOCK_FONT,
        show_size=show_size,
        show_color=show_color,
        show_article=show_article,
        show_composition=show_composition,
        show_brand=show_brand,
        show_country=show_country,
        merge_size_color=False,
    )

    # Если не влезает — пробуем объединённый формат
    if len(block_lines_separate) > B60_MAX_BLOCK_LINES:
        block_lines_merged = _collect_basic60_block_lines(
            item,
            B60_MIN_BLOCK_FONT,
            show_size=show_size,
            show_color=show_color,
            show_article=show_article,
            show_composition=show_composition,
            show_brand=show_brand,
            show_country=show_country,
            merge_size_color=True,
        )
        if len(block_lines_merged) <= B60_MAX_BLOCK_LINES:
            merge_size_color = True
            block_lines_min = block_lines_merged
        else:
            block_lines_min = block_lines_separate
    else:
        block_lines_min = block_lines_separate

    if len(block_lines_min) > B60_MAX_BLOCK_LINES:
        preflight_errors.append(
            f"Текстовый блок: {len(block_lines_min)} строк (макс. {B60_MAX_BLOCK_LINES})"
        )

    if preflight_errors:
        return Basic60Layout(
            fits=False,
            name_lines=[],
            block_lines=[],
            name_font=B60_MIN_NAME_FONT,
            block_font=B60_MIN_BLOCK_FONT,
            line_height=B60_MIN_LINE_HEIGHT,
            name_top_y=0,
            block_top_y=0,
            preflight_errors=preflight_errors,
        )

    # === Эталонные параметры ===
    name_font = B60_MAX_NAME_FONT
    block_font = B60_MAX_BLOCK_FONT
    line_height = B60_MAX_LINE_HEIGHT

    name_lines = _wrap_text_basic60(name_text, FONT_NAME_BOLD, name_font, B60_TEXT_MAX_WIDTH)
    block_lines = _collect_basic60_block_lines(
        item,
        block_font,
        show_size=show_size,
        show_color=show_color,
        show_article=show_article,
        show_composition=show_composition,
        show_brand=show_brand,
        show_country=show_country,
        merge_size_color=merge_size_color,
    )

    # === Позиция текстового блока (прижат к штрихкоду) ===
    # Последняя строка на 1.5мм от штрихкода
    block_bottom_y = B60_BARCODE_TOP + B60_MIN_GAP_TO_BARCODE  # 14мм
    block_top_y = block_bottom_y + (len(block_lines) - 1) * line_height

    # === Центрирование названия ===
    # Доступное пространство: от организации до блока
    org_bottom = B60_ORG_Y - 2  # ~2мм под организацией
    gap_above_block = 3  # мм — минимальный отступ над блоком

    name_line_height = name_font * 0.353 + 1  # высота строки в мм
    name_total_height = len(name_lines) * name_line_height

    # Центр доступного пространства
    name_center = (org_bottom + block_top_y + gap_above_block) / 2
    name_top_y = name_center + name_total_height / 2 - name_line_height / 2

    return Basic60Layout(
        fits=True,
        name_lines=name_lines,
        block_lines=block_lines,
        name_font=name_font,
        block_font=block_font,
        line_height=line_height,
        name_top_y=name_top_y,
        block_top_y=block_top_y,
        preflight_errors=[],
    )


# === Basic 58x40 адаптивные функции ===


@dataclass
class Basic40Layout:
    """Результат расчёта layout для Basic 58x40."""

    fits: bool  # True если контент влезает
    name_lines: list[str]  # Строки названия
    block_lines: list[str]  # Строки текстового блока
    name_font: float  # Размер шрифта названия
    block_font: float  # Размер шрифта блока
    line_height: float  # Высота строки блока в мм
    name_top_y: float  # Y первой строки названия
    block_top_y: float  # Y первой строки блока
    preflight_errors: list[str]  # Ошибки если не влезает


def _wrap_text_basic40(
    text: str,
    font_name: str,
    font_size: float,
    max_width_mm: float,
) -> list[str]:
    """Переносит текст по словам для Basic 58x40."""
    max_width_pt = max_width_mm * mm
    words = text.split()

    if not words:
        return []

    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = current_line + " " + word
        if pdfmetrics.stringWidth(test_line, font_name, font_size) <= max_width_pt:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def _check_line_fits_basic40(text: str, font_size: float) -> bool:
    """Проверяет влезает ли строка в max_width."""
    width_pt = pdfmetrics.stringWidth(text, FONT_NAME_BOLD, font_size)
    width_mm = width_pt / mm
    return width_mm <= B40_TEXT_MAX_WIDTH


def _check_block_lines_fit_basic40(lines: list[str], font_size: float) -> bool:
    """Проверяет все ли строки блока влезают в max_width."""
    return all(_check_line_fits_basic40(line, font_size) for line in lines)


def _collect_basic40_block_lines(item: "LabelItem", font_size: float) -> list[str]:
    """
    Собирает строки текстового блока Basic 58x40 (4 характеристики).
    """
    lines = []

    # Цвет + размер (объединяем в одну строку)
    parts = []
    if item.color:
        parts.append(f"цвет: {item.color}")
    if item.size:
        parts.append(f"размер {item.size}")
    if parts:
        lines.append(", ".join(parts))

    # Артикул
    if item.article:
        lines.append(f"арт.: {item.article}")

    # Состав (может быть длинным — переносим)
    if item.composition:
        comp_lines = _wrap_text_basic40(
            f"Состав: {item.composition}",
            FONT_NAME_BOLD,
            font_size,
            B40_TEXT_MAX_WIDTH,
        )
        lines.extend(comp_lines)

    return lines


def _calculate_basic40_layout(item: "LabelItem", organization: str | None) -> Basic40Layout:
    """
    Рассчитывает адаптивный layout для Basic 58x40.

    Алгоритм двунаправленной адаптации:
    1. Проверяем ширину организации (PREFLIGHT если > max_width)
    2. Перебираем шрифты названия от большего к меньшему
    3. Перебираем шрифты блока от большего к меньшему
    4. Рассчитываем позиции: блок прижат к штрихкоду, название центрировано
    """
    preflight_errors = []
    name_text = item.name or ""
    org_text = organization or ""

    # === Проверка организации (ширина при фиксированном шрифте 3.8pt) ===
    if org_text:
        org_width_pt = pdfmetrics.stringWidth(org_text, FONT_NAME_BOLD, B40_ORG_FONT)
        org_width_mm = org_width_pt / mm
        if org_width_mm > B40_TEXT_MAX_WIDTH:
            preflight_errors.append(
                f"Организация: {org_width_mm:.1f}мм (макс. {B40_TEXT_MAX_WIDTH}мм)"
            )

    # === Адаптация шрифта названия (двунаправленная) ===
    # Перебираем шрифты от большего к меньшему: 8.5 → 7.5 → 6.5 → 5.5 → 5.0
    name_font = B40_MIN_NAME_FONT
    name_lines: list[str] = []
    found_name_fit = False

    for try_font in B40_NAME_FONT_STEPS:
        try_lines = _wrap_text_basic40(name_text, FONT_NAME_BOLD, try_font, B40_TEXT_MAX_WIDTH)
        if len(try_lines) <= B40_MAX_NAME_LINES:
            name_font = try_font
            name_lines = try_lines
            found_name_fit = True
            break

    if not found_name_fit:
        name_font = B40_MIN_NAME_FONT
        name_lines = _wrap_text_basic40(name_text, FONT_NAME_BOLD, name_font, B40_TEXT_MAX_WIDTH)

    if len(name_lines) > B40_MAX_NAME_LINES:
        preflight_errors.append(
            f"Название: {len(name_lines)} строк (макс. {B40_MAX_NAME_LINES}) даже при {name_font}pt"
        )

    # === Адаптация шрифта блока (двунаправленная) ===
    # Перебираем шрифты от большего к меньшему: 6.0 → 5.5 → 5.0 → 4.5 → 4.0
    block_font = B40_MIN_BLOCK_FONT
    block_lines: list[str] = []
    found_block_fit = False

    for try_font in B40_BLOCK_FONT_STEPS:
        try_lines = _collect_basic40_block_lines(item, try_font)
        lines_count_ok = len(try_lines) <= B40_MAX_BLOCK_LINES
        lines_width_ok = _check_block_lines_fit_basic40(try_lines, try_font)

        if lines_count_ok and lines_width_ok:
            block_font = try_font
            block_lines = try_lines
            found_block_fit = True
            break

    if not found_block_fit:
        block_font = B40_MIN_BLOCK_FONT
        block_lines = _collect_basic40_block_lines(item, block_font)

    # Проверяем количество строк
    if len(block_lines) > B40_MAX_BLOCK_LINES:
        preflight_errors.append(
            f"Текстовый блок: {len(block_lines)} строк (макс. {B40_MAX_BLOCK_LINES})"
        )

    # Проверяем ширину строк при минимальном шрифте
    if not _check_block_lines_fit_basic40(block_lines, block_font):
        for line in block_lines:
            if not _check_line_fits_basic40(line, block_font):
                width_pt = pdfmetrics.stringWidth(line, FONT_NAME_BOLD, block_font)
                width_mm = width_pt / mm
                preflight_errors.append(
                    f"Строка '{line[:20]}...' = {width_mm:.1f}мм (макс. {B40_TEXT_MAX_WIDTH}мм)"
                )

    # === Если есть preflight ошибки — возвращаем ===
    if preflight_errors:
        return Basic40Layout(
            fits=False,
            name_lines=[],
            block_lines=[],
            name_font=name_font,
            block_font=block_font,
            line_height=B40_MIN_LINE_HEIGHT,
            name_top_y=0,
            block_top_y=0,
            preflight_errors=preflight_errors,
        )

    # === Рассчитываем line_height от размера шрифта ===
    if block_font >= 6.0:
        line_height = 2.5
    elif block_font >= 5.0:
        line_height = 2.0
    else:  # 4pt и меньше
        line_height = 1.5

    # === Позиция текстового блока (последняя строка прижата к штрихкоду) ===
    block_last_y = B40_BARCODE_TOP + B40_MIN_GAP_TO_BARCODE  # 14мм
    block_top_y = block_last_y + (len(block_lines) - 1) * line_height

    # === Центрирование названия по вертикали ===
    org_font_height = B40_ORG_FONT * 0.353  # ~1.3мм для 3.8pt
    available_top = B40_ORG_Y - org_font_height - 1.0

    min_gap_name_to_block = 2.0  # мм
    available_bottom = block_top_y + min_gap_name_to_block

    name_line_height = name_font * 0.353 + 0.8
    name_total_height = len(name_lines) * name_line_height

    available_center = (available_top + available_bottom) / 2
    name_top_y = available_center + name_total_height / 2 - name_line_height / 2

    return Basic40Layout(
        fits=True,
        name_lines=name_lines,
        block_lines=block_lines,
        name_font=name_font,
        block_font=block_font,
        line_height=line_height,
        name_top_y=name_top_y,
        block_top_y=block_top_y,
        preflight_errors=[],
    )


# === Basic 58x30 адаптивные функции ===


@dataclass
class Basic30Layout:
    """Результат расчёта layout для Basic 58x30."""

    fits: bool  # True если контент влезает
    name_lines: list[str]  # Строки названия
    block_lines: list[str]  # Строки текстового блока (size_color + article)
    name_font: float  # Размер шрифта названия
    block_font: float  # Размер шрифта блока (фиксированный)
    line_height: float  # Высота строки блока в мм
    name_top_y: float  # Y первой строки названия
    block_top_y: float  # Y первой строки блока
    preflight_errors: list[str]  # Ошибки если не влезает


def _wrap_text_basic30(
    text: str,
    font_name: str,
    font_size: float,
    max_width_mm: float,
) -> list[str]:
    """Переносит текст по словам для Basic 58x30."""
    max_width_pt = max_width_mm * mm
    words = text.split()

    if not words:
        return []

    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = current_line + " " + word
        if pdfmetrics.stringWidth(test_line, font_name, font_size) <= max_width_pt:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def _check_line_fits_basic30(text: str, font_size: float) -> bool:
    """Проверяет влезает ли строка в max_width."""
    width_pt = pdfmetrics.stringWidth(text, FONT_NAME_BOLD, font_size)
    width_mm = width_pt / mm
    return width_mm <= B30_TEXT_MAX_WIDTH


def _collect_basic30_block_lines(item: "LabelItem") -> list[str]:
    """
    Собирает строки текстового блока Basic 58x30 (2 строки).
    Добавляет ключи: "размер/цвет:" и "арт.:"
    """
    lines = []

    # Размер + цвет с ключом
    parts = []
    if item.size:
        parts.append(item.size)
    if item.color:
        parts.append(item.color)
    if parts:
        lines.append(f"размер/цвет: {' / '.join(parts)}")

    # Артикул с ключом
    if item.article:
        lines.append(f"арт.: {item.article}")

    return lines


def _calculate_basic30_layout(item: "LabelItem", organization: str | None) -> Basic30Layout:
    """
    Рассчитывает адаптивный layout для Basic 58x30.

    Алгоритм двунаправленной адаптации:
    1. Проверяем ширину организации (PREFLIGHT если > max_width)
    2. Перебираем шрифты названия от большего к меньшему
    3. Блок — фиксированный 4pt, проверяем ширину строк
    4. Рассчитываем позиции
    """
    preflight_errors = []
    name_text = item.name or ""
    org_text = organization or ""

    # === Проверка организации (ширина при фиксированном шрифте 4pt) ===
    if org_text:
        org_width_pt = pdfmetrics.stringWidth(org_text, FONT_NAME_BOLD, B30_ORG_FONT)
        org_width_mm = org_width_pt / mm
        if org_width_mm > B30_TEXT_MAX_WIDTH:
            preflight_errors.append(
                f"Организация: {org_width_mm:.1f}мм (макс. {B30_TEXT_MAX_WIDTH}мм)"
            )

    # === Адаптация шрифта названия (двунаправленная) ===
    name_font = B30_MIN_NAME_FONT
    name_lines: list[str] = []
    found_name_fit = False

    for try_font in B30_NAME_FONT_STEPS:
        try_lines = _wrap_text_basic30(name_text, FONT_NAME_BOLD, try_font, B30_TEXT_MAX_WIDTH)
        if len(try_lines) <= B30_MAX_NAME_LINES:
            name_font = try_font
            name_lines = try_lines
            found_name_fit = True
            break

    if not found_name_fit:
        name_font = B30_MIN_NAME_FONT
        name_lines = _wrap_text_basic30(name_text, FONT_NAME_BOLD, name_font, B30_TEXT_MAX_WIDTH)

    if len(name_lines) > B30_MAX_NAME_LINES:
        preflight_errors.append(
            f"Название: {len(name_lines)} строк (макс. {B30_MAX_NAME_LINES}) даже при {name_font}pt"
        )

    # === Блок — фиксированный 4pt ===
    block_font = B30_BLOCK_FONT
    block_lines = _collect_basic30_block_lines(item)

    # Проверяем ширину каждой строки блока
    for line in block_lines:
        if not _check_line_fits_basic30(line, block_font):
            width_pt = pdfmetrics.stringWidth(line, FONT_NAME_BOLD, block_font)
            width_mm = width_pt / mm
            preflight_errors.append(
                f"Строка '{line[:25]}...' = {width_mm:.1f}мм (макс. {B30_TEXT_MAX_WIDTH}мм)"
            )

    # === Если есть preflight ошибки — возвращаем ===
    if preflight_errors:
        return Basic30Layout(
            fits=False,
            name_lines=[],
            block_lines=[],
            name_font=name_font,
            block_font=block_font,
            line_height=B30_BLOCK_LINE_HEIGHT,
            name_top_y=0,
            block_top_y=0,
            preflight_errors=preflight_errors,
        )

    line_height = B30_BLOCK_LINE_HEIGHT

    # === Позиция текстового блока (последняя строка прижата к штрихкоду) ===
    block_last_y = B30_BARCODE_TOP + B30_MIN_GAP_TO_BARCODE  # 11мм
    block_top_y = block_last_y + (len(block_lines) - 1) * line_height

    # === Центрирование названия по вертикали ===
    org_font_height = B30_ORG_FONT * 0.353
    available_top = B30_ORG_Y - org_font_height - 1.0

    min_gap_name_to_block = 1.5  # мм (меньше места на 58x30)
    available_bottom = block_top_y + min_gap_name_to_block

    name_line_height = name_font * 0.353 + 0.8
    name_total_height = len(name_lines) * name_line_height

    available_center = (available_top + available_bottom) / 2
    name_top_y = available_center + name_total_height / 2 - name_line_height / 2

    return Basic30Layout(
        fits=True,
        name_lines=name_lines,
        block_lines=block_lines,
        name_font=name_font,
        block_font=block_font,
        line_height=line_height,
        name_top_y=name_top_y,
        block_top_y=block_top_y,
        preflight_errors=[],
    )


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
        layout: Literal["basic", "professional", "extended"] = "basic",
        label_format: Literal["combined", "separate"] = "combined",
        show_article: bool = True,
        show_size: bool = True,
        show_color: bool = True,
        show_name: bool = True,
        show_organization: bool = True,
        show_inn: bool = False,
        show_country: bool = False,
        show_composition: bool = False,
        show_chz_code_text: bool = True,
        # Режим нумерации: none, sequential, per_product, continue
        numbering_mode: Literal["none", "sequential", "per_product", "continue"] = "none",
        start_number: int = 1,
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
        custom_lines: list[str] | None = None,  # Кастомные строки для extended шаблона
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

        # Professional и Extended шаблоны поддерживают только 58x40
        if layout in ("professional", "extended") and size != "58x40":
            size = "58x40"

        width_mm, height_mm = LABEL_SIZES[size]
        layout_config = LAYOUTS[layout][size]

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(width_mm * mm, height_mm * mm))

        # Матчинг товаров и кодов ЧЗ по GTIN
        # Количество этикеток = количество кодов ЧЗ (не минимум!)
        matched_pairs = self._match_items_with_codes(items, codes)

        # Счётчики для режима per_product
        barcode_counters: dict[str, int] = {}

        for i, (item, code) in enumerate(matched_pairs):

            # Вычисляем серийный номер по режиму нумерации
            serial: int | None = None
            if numbering_mode == "none":
                serial = None
            elif numbering_mode == "sequential":
                serial = i + 1
            elif numbering_mode == "per_product":
                # Счётчик для каждого баркода
                barcode = item.barcode
                if barcode not in barcode_counters:
                    barcode_counters[barcode] = 0
                barcode_counters[barcode] += 1
                serial = barcode_counters[barcode]
            elif numbering_mode == "continue":
                serial = start_number + i

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
                        show_size=show_size,
                        show_color=show_color,
                        show_name=show_name,
                        show_organization=show_organization,
                        show_inn=show_inn,
                        show_country=show_country,
                        show_composition=show_composition,
                        show_brand=show_brand,
                        show_chz_code_text=show_chz_code_text,
                        size=size,
                    )
                elif layout == "extended":
                    self._draw_extended_label(
                        c=c,
                        item=item,
                        code=code,
                        layout_config=layout_config,
                        inn=inn,
                        address=organization_address or organization,  # Адрес или организация
                        serial_number=serial,
                        show_chz_code_text=show_chz_code_text,
                        custom_lines=custom_lines,
                        show_name=show_name,
                        show_article=show_article,
                        show_size=show_size,
                        show_color=show_color,
                        show_brand=show_brand,
                        show_composition=show_composition,
                        show_country=show_country,
                        show_manufacturer=show_manufacturer,
                    )
                elif layout == "professional":
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
                        serial_number=serial,
                        show_article=show_article,
                        show_size=show_size,
                        show_color=show_color,
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
                    show_size=show_size,
                    show_color=show_color,
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

    def preflight_check(
        self,
        items: list[LabelItem],
        size: str = "58x40",
        organization: str | None = None,
        layout: Literal["basic", "professional", "extended"] = "basic",
        show_article: bool = True,
        show_size: bool = True,
        show_color: bool = True,
        show_name: bool = True,
        show_brand: bool = False,
        show_composition: bool = False,
        show_country: bool = False,
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
        custom_lines: list[str] | None = None,
    ) -> list[PreflightErrorInfo]:
        """
        Проверяет данные этикеток без генерации PDF.

        Возвращает список структурированных ошибок с привязкой к полям.
        Если список пустой — данные прошли проверку.

        Args:
            items: Список товаров (баркоды WB)
            size: Размер этикетки (58x40, 58x30, 58x60)
            organization: Название организации
            layout: Шаблон (basic, professional, extended)
            show_*: Флаги отображения полей
            organization_address: Адрес производства (professional)
            importer: Импортер (professional)
            manufacturer: Производитель (professional)
            production_date: Дата производства (professional)
            certificate_number: Номер сертификата (professional)
            custom_lines: Кастомные строки для extended шаблона

        Returns:
            list[PreflightErrorInfo]: Список ошибок с field_id
        """
        all_errors: list[PreflightErrorInfo] = []

        if size not in LABEL_SIZES:
            size = "58x40"
        if layout not in LAYOUTS:
            layout = "basic"

        # Professional и Extended поддерживают только 58x40
        if layout in ("professional", "extended") and size != "58x40":
            size = "58x40"

        # Проверяем каждый item
        for idx, item in enumerate(items):
            item_errors: list[str] = []

            if layout == "basic":
                if size == "58x40":
                    layout_result = _calculate_basic40_layout(item, organization)
                    item_errors = layout_result.preflight_errors
                elif size == "58x30":
                    layout_result = _calculate_basic30_layout(item, organization)
                    item_errors = layout_result.preflight_errors
                elif size == "58x60":
                    layout_result = _calculate_basic60_layout(
                        item,
                        organization,
                        show_size=show_size,
                        show_color=show_color,
                        show_article=show_article,
                        show_brand=show_brand,
                        show_composition=show_composition,
                        show_country=show_country,
                    )
                    item_errors = layout_result.preflight_errors

            elif layout == "extended":
                layout_result = _calculate_extended_layout(
                    item=item,
                    address=organization_address or organization,
                    custom_lines=custom_lines,
                    show_name=show_name,
                    show_article=show_article,
                    show_size=show_size,
                    show_color=show_color,
                    show_brand=show_brand,
                    show_composition=show_composition,
                    show_country=show_country,
                    show_manufacturer=show_manufacturer,
                )
                item_errors = layout_result.preflight_errors

            elif layout == "professional":
                layout_result = _calculate_professional_layout(
                    item=item,
                    organization=organization,
                    organization_address=organization_address,
                    importer=importer or organization,
                    manufacturer=manufacturer or organization,
                    production_date=production_date,
                    certificate_number=certificate_number,
                    show_name=show_name,
                    show_article=show_article,
                    show_brand=show_brand,
                    show_size=show_size,
                    show_color=show_color,
                    show_importer=show_importer,
                    show_manufacturer=show_manufacturer,
                    show_address=show_address,
                    show_production_date=show_production_date,
                    show_certificate=show_certificate,
                )
                item_errors = layout_result.preflight_errors

            # Парсим ошибки и добавляем в общий список
            for error_text in item_errors:
                parsed = parse_preflight_error(error_text)
                # Добавляем индекс товара к сообщению если товаров несколько
                if len(items) > 1:
                    parsed = PreflightErrorInfo(
                        field_id=parsed.field_id,
                        message=f"[Этикетка {idx + 1}] {parsed.message}",
                        suggestion=parsed.suggestion,
                    )
                all_errors.append(parsed)

            # Оптимизация: если уже есть ошибки и это не первый item —
            # возвращаем результат, чтобы не проверять все N этикеток
            if all_errors and idx > 0:
                break

        return all_errors

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
        show_size: bool,
        show_color: bool,
        show_name: bool,
        show_organization: bool,
        show_inn: bool,
        show_country: bool,
        show_composition: bool,
        show_brand: bool,
        show_chz_code_text: bool,
        size: str = "58x40",
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
        # Адаптивная типографика только для 58x40 и 58x60
        # Для 58x30 используем фиксированные размеры с усечением текста
        use_adaptive = size != "58x30"

        # === ЛЕВАЯ КОЛОНКА ===
        # DataMatrix — динамический расчёт (гарантирует отступ 1.5мм)
        left_col = calculate_left_column("basic", size)
        self._draw_datamatrix(c, code, left_col.dm_x, left_col.dm_y, left_col.dm_size)

        # === Вертикальная линия-разделитель (если есть) ===
        if "divider" in layout_config:
            div = layout_config["divider"]
            self._draw_vertical_line(
                c, div["x"], div["y_start"], div["y_end"], div.get("width", 0.3)
            )

        # Код ЧЗ текстом под DataMatrix (из конфига — разная структура для размеров)
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

        # Логотип "ЧЕСТНЫЙ ЗНАК" (из конфига)
        if "chz_logo" in layout_config:
            logo = layout_config["chz_logo"]
            self._draw_chz_logo(c, logo["x"], logo["y"], logo["width"], logo["height"])

        # Логотип EAC (из конфига)
        if "eac_logo" in layout_config:
            eac = layout_config["eac_logo"]
            self._draw_eac_logo(c, eac["x"], eac["y"], eac["width"], eac["height"])

        # Серийный номер (из конфига)
        if serial_number is not None and "serial_number" in layout_config:
            sn = layout_config["serial_number"]
            bold = sn.get("bold", False)
            self._draw_text(c, f"№ {serial_number}", sn["x"], sn["y"], sn["size"], False, bold)

        # === Справа сверху: ИНН + организация (адаптивное позиционирование) ===
        # Если ИНН не показывается — организация поднимается на место ИНН (к верху)
        inn_value = inn or item.inn
        inn_is_shown = show_inn and inn_value and "inn" in layout_config

        if inn_is_shown:
            inn_cfg = layout_config["inn"]
            max_w = inn_cfg.get("max_width", 30)
            centered = inn_cfg.get("centered", False)
            bold = inn_cfg.get("bold", False)
            text = self._truncate_text(c, f"ИНН: {inn_value}", inn_cfg["size"], max_w)
            self._draw_text(c, text, inn_cfg["x"], inn_cfg["y"], inn_cfg["size"], centered, bold)

        if show_organization and organization and "organization" in layout_config:
            org = layout_config["organization"]
            max_w = org.get("max_width", 30)
            centered = org.get("centered", False)
            bold = org.get("bold", False)
            text = self._truncate_text(c, organization, org["size"], max_w)

            # Адаптивная Y координата: если ИНН не показан — организация на месте ИНН
            org_y = org["y"]
            if not inn_is_shown and "inn" in layout_config:
                org_y = layout_config["inn"]["y"]

            self._draw_text(c, text, org["x"], org_y, org["size"], centered, bold)

        # === АДАПТИВНАЯ ЛОГИКА ДЛЯ BASIC 58x40 ===
        if size == "58x40" and show_name:
            layout40 = _calculate_basic40_layout(item, organization)

            if not layout40.fits:
                # PREFLIGHT ERROR — рисуем ошибку вместо контента
                c.setFillColorRGB(1, 0, 0)
                c.setFont(FONT_NAME_BOLD, 5)
                c.drawCentredString(B40_TEXT_CENTER_X * mm, 28 * mm, "PREFLIGHT ERROR")
                c.setFont(FONT_NAME, 3.5)
                error_y = 25
                for error in layout40.preflight_errors:
                    c.drawCentredString(B40_TEXT_CENTER_X * mm, error_y * mm, error)
                    error_y -= 2.5
                c.setFillColorRGB(0, 0, 0)
            else:
                # === Название (центрировано по вертикали) ===
                c.setFont(FONT_NAME_BOLD, layout40.name_font)
                name_y = layout40.name_top_y
                name_line_h = layout40.name_font * 0.353 + 0.8
                for line in layout40.name_lines:
                    c.drawCentredString(B40_TEXT_CENTER_X * mm, name_y * mm, line)
                    name_y -= name_line_h

                # === Текстовый блок (прижат к штрихкоду) ===
                c.setFont(FONT_NAME_BOLD, layout40.block_font)
                block_y = layout40.block_top_y
                for line in layout40.block_lines:
                    c.drawCentredString(B40_TEXT_CENTER_X * mm, block_y * mm, line)
                    block_y -= layout40.line_height

            # Штрихкод WB справа внизу (для 58x40 адаптивного)
            bc = layout_config["barcode"]
            self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

            bc_text = layout_config["barcode_text"]
            bc_centered = bc_text.get("centered", False)
            bc_bold = bc_text.get("bold", False)
            self._draw_text(
                c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], bc_centered, bc_bold
            )
            return  # Выход из метода — всё нарисовано для 58x40

        # === АДАПТИВНАЯ ЛОГИКА ДЛЯ BASIC 58x30 ===
        if size == "58x30" and show_name:
            layout30 = _calculate_basic30_layout(item, organization)

            if not layout30.fits:
                # PREFLIGHT ERROR — рисуем ошибку вместо контента
                c.setFillColorRGB(1, 0, 0)
                c.setFont(FONT_NAME_BOLD, 4)
                c.drawCentredString(B30_TEXT_CENTER_X * mm, 20 * mm, "PREFLIGHT ERROR")
                c.setFont(FONT_NAME, 3)
                error_y = 17
                for error in layout30.preflight_errors:
                    c.drawCentredString(B30_TEXT_CENTER_X * mm, error_y * mm, error)
                    error_y -= 2
                c.setFillColorRGB(0, 0, 0)
            else:
                # === Название (центрировано по вертикали) ===
                c.setFont(FONT_NAME_BOLD, layout30.name_font)
                name_y = layout30.name_top_y
                name_line_h = layout30.name_font * 0.353 + 0.8
                for line in layout30.name_lines:
                    c.drawCentredString(B30_TEXT_CENTER_X * mm, name_y * mm, line)
                    name_y -= name_line_h

                # === Текстовый блок (прижат к штрихкоду) ===
                c.setFont(FONT_NAME_BOLD, layout30.block_font)
                block_y = layout30.block_top_y
                for line in layout30.block_lines:
                    c.drawCentredString(B30_TEXT_CENTER_X * mm, block_y * mm, line)
                    block_y -= layout30.line_height

            # Штрихкод WB справа внизу (для 58x30 адаптивного)
            bc = layout_config["barcode"]
            self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

            bc_text = layout_config["barcode_text"]
            bc_centered = bc_text.get("centered", False)
            bc_bold = bc_text.get("bold", False)
            self._draw_text(
                c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], bc_centered, bc_bold
            )
            return  # Выход из метода — всё нарисовано для 58x30

        # === АДАПТИВНАЯ ЛОГИКА ДЛЯ BASIC 58x60 ===
        if size == "58x60" and show_name:
            layout60 = _calculate_basic60_layout(
                item,
                organization,
                show_size=show_size,
                show_color=show_color,
                show_article=show_article,
                show_composition=show_composition,
                show_brand=show_brand,
                show_country=show_country,
            )

            if not layout60.fits:
                # PREFLIGHT ERROR — рисуем ошибку вместо контента
                c.setFillColorRGB(1, 0, 0)
                c.setFont(FONT_NAME_BOLD, 6)
                c.drawCentredString(B60_TEXT_CENTER_X * mm, 45 * mm, "PREFLIGHT ERROR")
                c.setFont(FONT_NAME, 4)
                error_y = 42
                for error in layout60.preflight_errors:
                    c.drawCentredString(B60_TEXT_CENTER_X * mm, error_y * mm, error)
                    error_y -= 3
                c.setFillColorRGB(0, 0, 0)
            else:
                # === Название (центрировано по вертикали) ===
                c.setFont(FONT_NAME_BOLD, layout60.name_font)
                name_y = layout60.name_top_y
                name_line_h = layout60.name_font * 0.353 + 1
                for line in layout60.name_lines:
                    c.drawCentredString(B60_TEXT_CENTER_X * mm, name_y * mm, line)
                    name_y -= name_line_h

                # === Текстовый блок (прижат к штрихкоду) ===
                c.setFont(FONT_NAME_BOLD, layout60.block_font)
                block_y = layout60.block_top_y
                for line in layout60.block_lines:
                    c.drawCentredString(B60_TEXT_CENTER_X * mm, block_y * mm, line)
                    block_y -= layout60.line_height

            # Штрихкод WB справа внизу (для 58x60 адаптивного)
            bc = layout_config["barcode"]
            self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

            bc_text = layout_config["barcode_text"]
            bc_centered = bc_text.get("centered", False)
            bc_bold = bc_text.get("bold", False)
            self._draw_text(
                c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], bc_centered, bc_bold
            )
            return  # Выход из метода — всё нарисовано для 58x60

        # === Название товара (может быть в две строки) ===
        if show_name and item.name and "name" in layout_config:
            nm = layout_config["name"]
            max_w = nm.get("max_width", 30)
            centered = nm.get("centered", False)
            bold = nm.get("bold", False)
            base_size = nm["size"]
            font = FONT_NAME_BOLD if bold else FONT_NAME

            if use_adaptive:
                # Адаптивно подбираем размер шрифта для названия
                fitted_name, final_size = self._fit_text_adaptive(
                    c, item.name, base_size, MIN_FONT_SIZES["name"], max_w, bold
                )

                # Если текст не обрезан — рисуем в одну строку
                if not fitted_name.endswith("..."):
                    self._draw_text(c, fitted_name, nm["x"], nm["y"], final_size, centered, bold)
                else:
                    # Текст не помещается — разбиваем на две строки
                    c.setFont(font, base_size)
                    words = item.name.split()
                    line1_words = []
                    line2_words = []

                    for word in words:
                        test_line = " ".join(line1_words + [word])
                        if c.stringWidth(test_line) <= max_w * mm:
                            line1_words.append(word)
                        else:
                            line2_words.append(word)

                    if line1_words:
                        self._draw_text(
                            c,
                            " ".join(line1_words),
                            nm["x"],
                            nm["y"],
                            base_size,
                            centered,
                            bold,
                        )
                    if line2_words and "name_2" in layout_config:
                        nm2 = layout_config["name_2"]
                        centered2 = nm2.get("centered", False)
                        bold2 = nm2.get("bold", False)
                        self._draw_text_adaptive(
                            c,
                            " ".join(line2_words),
                            nm2["x"],
                            nm2["y"],
                            nm2["size"],
                            nm2.get("max_width", 30),
                            MIN_FONT_SIZES["name"],
                            centered2,
                            bold2,
                        )
            else:
                # Без адаптивной типографики (58x30) — разбиваем на две строки без изменений
                c.setFont(font, base_size)
                words = item.name.split()
                line1_words = []
                line2_words = []

                for word in words:
                    test_line = " ".join(line1_words + [word])
                    if c.stringWidth(test_line) <= max_w * mm:
                        line1_words.append(word)
                    else:
                        line2_words.append(word)

                if line1_words:
                    self._draw_text(
                        c, " ".join(line1_words), nm["x"], nm["y"], base_size, centered, bold
                    )

                if line2_words and "name_2" in layout_config:
                    nm2 = layout_config["name_2"]
                    centered2 = nm2.get("centered", False)
                    bold2 = nm2.get("bold", False)
                    self._draw_text(
                        c, " ".join(line2_words), nm2["x"], nm2["y"], nm2["size"], centered2, bold2
                    )

        # === Характеристики ===
        # Для 58x30 — используем size_color (объединённый)
        if "size_color" in layout_config:
            parts = []
            if show_size and item.size:
                parts.append(item.size)
            if show_color and item.color:
                parts.append(item.color)
            if parts:
                sc = layout_config["size_color"]
                self._draw_text(
                    c,
                    " / ".join(parts),
                    sc["x"],
                    sc["y"],
                    sc["size"],
                    sc.get("centered", False),
                    sc.get("bold", False),
                )
            # Артикул для 58x30
            if show_article and item.article and "article" in layout_config:
                art = layout_config["article"]
                self._draw_text(
                    c,
                    f"арт.: {item.article}",
                    art["x"],
                    art["y"],
                    art["size"],
                    art.get("centered", False),
                    art.get("bold", False),
                )
        else:
            # Для 58x40, 58x60 — 4 строки характеристик
            # Строка 1: цвет + размер
            if "char_line_1" in layout_config:
                cfg = layout_config["char_line_1"]
                parts = []
                if show_color and item.color:
                    parts.append(f"цвет: {item.color}")
                if show_size and item.size:
                    parts.append(f"размер {item.size}")
                if parts:
                    self._draw_text(
                        c,
                        ", ".join(parts),
                        cfg["x"],
                        cfg["y"],
                        cfg["size"],
                        cfg.get("centered", False),
                        cfg.get("bold", False),
                    )

            # Строка 2: артикул + страна
            if "char_line_2" in layout_config:
                cfg = layout_config["char_line_2"]
                parts = []
                if show_article and item.article:
                    parts.append(f"арт.: {item.article}")
                if show_country and item.country:
                    parts.append(f"страна: {item.country}")
                if parts:
                    self._draw_text(
                        c,
                        ", ".join(parts),
                        cfg["x"],
                        cfg["y"],
                        cfg["size"],
                        cfg.get("centered", False),
                        cfg.get("bold", False),
                    )

            # Строка 3: состав
            if "char_line_3" in layout_config and show_composition and item.composition:
                cfg = layout_config["char_line_3"]
                self._draw_text(
                    c,
                    f"Состав: {item.composition}",
                    cfg["x"],
                    cfg["y"],
                    cfg["size"],
                    cfg.get("centered", False),
                    cfg.get("bold", False),
                )

            # Строка 4: бренд
            if "char_line_4" in layout_config and show_brand and item.brand:
                cfg = layout_config["char_line_4"]
                self._draw_text(
                    c,
                    f"Бренд: {item.brand}",
                    cfg["x"],
                    cfg["y"],
                    cfg["size"],
                    cfg.get("centered", False),
                    cfg.get("bold", False),
                )

            # Строка 5: производитель (только для 58x60)
            if "char_line_5" in layout_config and item.manufacturer:
                cfg = layout_config["char_line_5"]
                self._draw_text(
                    c,
                    f"Изг.: {item.manufacturer}",
                    cfg["x"],
                    cfg["y"],
                    cfg["size"],
                    cfg.get("centered", False),
                    cfg.get("bold", False),
                )

        # Страна (для 58x60)
        if show_country and item.country and "country" in layout_config:
            cnt = layout_config["country"]
            max_w = cnt.get("max_width", 22)
            centered = cnt.get("centered", False)
            text = self._truncate_text(c, f"Страна: {item.country}", cnt["size"], max_w)
            self._draw_text(c, text, cnt["x"], cnt["y"], cnt["size"], centered)

        # === Штрихкод WB справа внизу ===
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        bc_text = layout_config["barcode_text"]
        bc_centered = bc_text.get("centered", False)
        bc_bold = bc_text.get("bold", False)
        self._draw_text(
            c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], bc_centered, bc_bold
        )

    def _draw_extended_label(
        self,
        c: canvas.Canvas,
        item: LabelItem,
        code: str,
        layout_config: dict,
        inn: str | None,
        address: str | None,
        serial_number: int | None,
        show_chz_code_text: bool,
        # Данные для текстового блока
        custom_lines: list[str] | None = None,
        # Флаги отображения полей
        show_name: bool = True,
        show_article: bool = True,
        show_size: bool = True,
        show_color: bool = True,
        show_brand: bool = False,
        show_composition: bool = True,
        show_country: bool = False,
        show_manufacturer: bool = True,
    ) -> None:
        """
        Рисует EXTENDED этикетку:
        - Левая колонка: DataMatrix, код ЧЗ, логотипы, номер
        - Правая колонка: ИНН, адрес, блок текста с лейблами, штрихкод

        Доступные поля для Extended (согласно таблице):
        ИНН, Название, Артикул, Размер, Цвет, Бренд, Состав, Страна, Производитель, Адрес
        """
        # === ЛЕВАЯ КОЛОНКА ===
        # DataMatrix — динамический расчёт (гарантирует отступ 1.5мм)
        left_col = calculate_left_column("extended", "58x40")
        self._draw_datamatrix(c, code, left_col.dm_x, left_col.dm_y, left_col.dm_size)

        # === Код ЧЗ текстом (из конфига) ===
        if show_chz_code_text:
            if "chz_code_text" in layout_config:
                chz = layout_config["chz_code_text"]
                max_w = chz.get("max_width", DM_SIZE)
                line1 = self._truncate_text(c, code[:16], chz["size"], max_w)
                self._draw_text(c, line1, chz["x"], chz["y"], chz["size"], False, False)

            if "chz_code_text_2" in layout_config:
                chz2 = layout_config["chz_code_text_2"]
                max_w2 = chz2.get("max_width", DM_SIZE)
                line2 = self._truncate_text(c, code[16:31], chz2["size"], max_w2)
                self._draw_text(c, line2, chz2["x"], chz2["y"], chz2["size"], False, False)

        # === Логотип ЧЗ (из конфига) ===
        if "chz_logo" in layout_config:
            logo = layout_config["chz_logo"]
            self._draw_chz_logo(c, logo["x"], logo["y"], logo["width"], logo["height"])

        # === Логотип EAC (из конфига) ===
        if "eac_logo" in layout_config:
            eac = layout_config["eac_logo"]
            self._draw_eac_logo(c, eac["x"], eac["y"], eac["width"], eac["height"])

        # === Серийный номер (из конфига) ===
        if serial_number is not None and "serial_number" in layout_config:
            sn = layout_config["serial_number"]
            self._draw_text(
                c, f"№ {serial_number}", sn["x"], sn["y"], sn["size"], False, sn.get("bold", False)
            )

        # === Правая колонка: ИНН + Адрес (адаптивное позиционирование) ===
        # Если ИНН не показывается — адрес поднимается на место ИНН (к верху)
        inn_is_shown = bool(inn) and "inn" in layout_config

        if inn_is_shown:
            inn_cfg = layout_config["inn"]
            centered = inn_cfg.get("centered", False)
            bold = inn_cfg.get("bold", False)
            self._draw_text(
                c, f"ИНН: {inn}", inn_cfg["x"], inn_cfg["y"], inn_cfg["size"], centered, bold
            )

        # === Адрес ===
        if address and "address" in layout_config:
            addr_cfg = layout_config["address"]
            centered = addr_cfg.get("centered", False)
            bold = addr_cfg.get("bold", False)

            # Адаптивная Y координата: если ИНН не показан — адрес на месте ИНН
            addr_y = addr_cfg["y"]
            if not inn_is_shown and "inn" in layout_config:
                addr_y = layout_config["inn"]["y"]

            self._draw_text(
                c,
                f"Адрес: {address}",
                addr_cfg["x"],
                addr_y,
                addr_cfg["size"],
                centered,
                bold,
            )

        # === Текстовый блок с адаптивной логикой ===
        # Рассчитываем layout
        layout = _calculate_extended_layout(
            item,
            custom_lines,
            address,
            show_name=show_name,
            show_article=show_article,
            show_size=show_size,
            show_color=show_color,
            show_brand=show_brand,
            show_composition=show_composition,
            show_country=show_country,
            show_manufacturer=show_manufacturer,
        )

        if not layout.fits:
            # PREFLIGHT ERROR — рисуем ошибку вместо контента
            c.setFillColorRGB(1, 0, 0)
            c.setFont(FONT_NAME_BOLD, 5)
            c.drawString(EXT_TEXT_X * mm, 28 * mm, "PREFLIGHT ERROR")
            c.setFont(FONT_NAME, 4)
            error_y = 25
            for error in layout.preflight_errors:
                c.drawString(EXT_TEXT_X * mm, error_y * mm, error)
                error_y -= 2.5
            c.setFillColorRGB(0, 0, 0)
        else:
            # Нормальная отрисовка текстового блока
            c.setFont(FONT_NAME, layout.font_size)
            current_y = layout.start_y
            for line in layout.lines:
                self._draw_text(c, line, EXT_TEXT_X, current_y, layout.font_size, False, False)
                current_y -= layout.line_height

        # === Штрихкод WB справа внизу ===
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        bc_text = layout_config["barcode_text"]
        bc_centered = bc_text.get("centered", False)
        bc_bold = bc_text.get("bold", False)
        self._draw_text(
            c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], bc_centered, bc_bold
        )

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
        serial_number: int | None,
        show_article: bool,
        show_size: bool,
        show_color: bool,
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
        Рисует PROFESSIONAL этикетку (двухколоночный) с адаптивной типографикой:
        Левая колонка: EAC, "ЧЕСТНЫЙ ЗНАК", DataMatrix, код ЧЗ, страна
        Правая колонка: штрихкод, название (центрировано), текстовый блок (от низа)

        Адаптация для 58x40:
        1. Эталон: название 6pt, блок 5pt, отступы 4мм/5мм
        2. Уменьшаем отступы: 2мм/3мм
        3. Уменьшаем шрифты: 5pt/4pt
        """
        # === Вертикальная линия-разделитель ===
        if "divider" in layout_config:
            div = layout_config["divider"]
            self._draw_vertical_line(
                c, div["x"], div["y_start"], div["y_end"], div.get("width", 0.3)
            )

        # === ЛЕВАЯ КОЛОНКА ===
        # DataMatrix — динамический расчёт (гарантирует отступ 1.5мм)
        left_col = calculate_left_column("professional", "58x40")
        self._draw_datamatrix(c, code, left_col.dm_x, left_col.dm_y, left_col.dm_size)

        # EAC логотип (из конфига)
        if "eac_logo" in layout_config:
            eac = layout_config["eac_logo"]
            self._draw_eac_logo(c, eac["x"], eac["y"], eac["width"], eac["height"])

        # Честный знак логотип (из конфига)
        if "chz_logo" in layout_config:
            logo = layout_config["chz_logo"]
            if "width" in logo:
                self._draw_chz_logo(c, logo["x"], logo["y"], logo["width"], logo["height"])

        # Серийный номер (из конфига)
        if serial_number is not None and "serial_number" in layout_config:
            sn = layout_config["serial_number"]
            self._draw_text(
                c, f"№{serial_number}", sn["x"], sn["y"], sn["size"], False, sn.get("bold", False)
            )

        # Код ЧЗ текстом (из конфига)
        if show_chz_code_text and "chz_code_text" in layout_config:
            chz_cfg = layout_config["chz_code_text"]
            max_w = chz_cfg.get("max_width", DM_SIZE)
            font_size = chz_cfg["size"]
            centered = chz_cfg.get("centered", False)
            bold = chz_cfg.get("bold", True)
            font = FONT_NAME_BOLD if bold else FONT_NAME
            c.setFont(font, font_size)

            line1 = ""
            for char in code[:31]:
                test = line1 + char
                if c.stringWidth(test) <= max_w * mm:
                    line1 = test
                else:
                    break

            self._draw_text(c, line1, chz_cfg["x"], chz_cfg["y"], font_size, centered, bold)

            if len(line1) < len(code[:31]) and "chz_code_text_2" in layout_config:
                chz2 = layout_config["chz_code_text_2"]
                line2 = code[len(line1) : 31]
                self._draw_text(
                    c,
                    line2,
                    chz2["x"],
                    chz2["y"],
                    chz2["size"],
                    chz2.get("centered", True),
                    chz2.get("bold", bold),
                )

        # Страна производства
        if show_country and "country" in layout_config:
            cnt = layout_config["country"]
            text = self._truncate_text(c, "Сделано в России", cnt["size"], cnt.get("max_width", 22))
            self._draw_text(
                c,
                text,
                cnt["x"],
                cnt["y"],
                cnt["size"],
                cnt.get("centered", False),
                cnt.get("bold", False),
            )

        # === Правая колонка ===

        # Штрихкод WB (вверху — фиксированная позиция)
        bc = layout_config["barcode"]
        self._draw_barcode(c, item.barcode, bc["x"], bc["y"], bc["width"], bc["height"])

        bc_text = layout_config["barcode_text"]
        self._draw_text(
            c,
            item.barcode,
            bc_text["x"],
            bc_text["y"],
            bc_text["size"],
            bc_text.get("centered", False),
            bc_text.get("bold", False),
        )

        # === Адаптивная отрисовка названия и блока ===
        layout = _calculate_professional_layout(
            item=item,
            organization=organization,
            organization_address=organization_address,
            importer=importer,
            manufacturer=manufacturer,
            production_date=production_date,
            certificate_number=certificate_number,
            show_name=show_name,
            show_article=show_article,
            show_brand=show_brand,
            show_size=show_size,
            show_color=show_color,
            show_importer=show_importer,
            show_manufacturer=show_manufacturer,
            show_address=show_address,
            show_production_date=show_production_date,
            show_certificate=show_certificate,
        )

        # Если preflight error — не рисуем контент (этикетка будет с пустой правой частью)
        # В production это должно быть перехвачено раньше, но для безопасности проверяем
        if layout.preflight_errors:
            # Рисуем сообщение об ошибке вместо контента
            c.setFont(FONT_NAME_BOLD, 5)
            c.drawString(PROF_TEXT_LEFT * mm, 20 * mm, "ОШИБКА:")
            c.setFont(FONT_NAME, 4)
            y_err = 17
            for err in layout.preflight_errors[:2]:  # Максимум 2 строки ошибок
                # Обрезаем длинные сообщения
                if len(err) > 40:
                    err = err[:37] + "..."
                c.drawString(PROF_TEXT_LEFT * mm, y_err * mm, err)
                y_err -= 2.5
            return

        # === Рисуем название (центрировано по горизонтали и вертикали) ===
        if layout.name_lines:
            name_line_h = layout.name_font * 0.353 + 0.5
            y = layout.name_top_y

            for line in layout.name_lines:
                c.setFont(FONT_NAME_BOLD, layout.name_font)
                width = pdfmetrics.stringWidth(line, FONT_NAME_BOLD, layout.name_font)
                x = PROF_TEXT_LEFT + (PROF_MAX_TEXT_WIDTH - width / mm) / 2
                c.drawString(x * mm, y * mm, line)
                y -= name_line_h

        # === Рисуем текстовый блок (от верха вниз, выравнивание слева) ===
        y = layout.block_top_y

        for line in layout.block_lines:
            c.setFont(FONT_NAME_BOLD, layout.block_font)
            c.drawString(PROF_TEXT_LEFT * mm, y * mm, line)
            y -= layout.line_height

    def _draw_label_wb_only(
        self,
        c: canvas.Canvas,
        item: LabelItem,
        layout_config: dict,
        organization: str | None,
        inn: str | None,
        serial_number: int | None,
        show_article: bool,
        show_size: bool,
        show_color: bool,
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
        bold = bc_text.get("bold", False)
        self._draw_text(
            c, item.barcode, bc_text["x"], bc_text["y"], bc_text["size"], centered, bold
        )

        # Серийный номер (№ 1, № 2, ...)
        if serial_number is not None and "serial_number" in layout_config:
            sn = layout_config["serial_number"]
            bold = sn.get("bold", False)
            self._draw_text(c, f"№ {serial_number}", sn["x"], sn["y"], sn["size"], False, bold)

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

        # Цвет / Размер (раздельно контролируемые)
        if "size_color" in layout_config:
            parts = []
            if show_color and item.color:
                parts.append(f"Цв: {item.color}")
            if show_size and item.size:
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
        """Code128 штрихкод — растянут на указанную ширину."""
        # Создаём тестовый штрихкод с barWidth=1 чтобы узнать реальное кол-во модулей
        test_barcode = code128.Code128(value, barWidth=1, barHeight=1, quiet=False)
        real_modules = test_barcode.width  # Реальная ширина в points при barWidth=1

        # Точно рассчитываем barWidth для нужной ширины
        bar_width = (width * mm) / real_modules

        barcode = code128.Code128(
            value,
            barHeight=height * mm,
            barWidth=bar_width,
            humanReadable=False,
            quiet=False,
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

    def _draw_chz_logo(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        """Рисует логотип Честный Знак из PNG файла."""
        if os.path.exists(CHZ_LOGO_PATH):
            try:
                img_reader = ImageReader(CHZ_LOGO_PATH)
                c.drawImage(
                    img_reader,
                    x * mm,
                    y * mm,
                    width=width * mm,
                    height=height * mm,
                    preserveAspectRatio=True,
                    anchor="sw",
                    mask="auto",  # Прозрачность
                )
            except Exception:
                # Fallback на текст если логотип не загрузился
                c.setFont(FONT_NAME, 3.5)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x * mm, y * mm, "ЧЕСТНЫЙ ЗНАК")
        else:
            # Fallback на текст если файл не найден
            c.setFont(FONT_NAME, 3.5)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(x * mm, y * mm, "ЧЕСТНЫЙ ЗНАК")

    def _draw_eac_logo(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        """Рисует логотип EAC из PNG файла."""
        if os.path.exists(EAC_LOGO_PATH):
            try:
                img_reader = ImageReader(EAC_LOGO_PATH)
                c.drawImage(
                    img_reader,
                    x * mm,
                    y * mm,
                    width=width * mm,
                    height=height * mm,
                    preserveAspectRatio=True,
                    anchor="sw",
                    mask="auto",
                )
            except Exception:
                c.setFont(FONT_NAME, 6)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x * mm, y * mm, "EAC")
        else:
            c.setFont(FONT_NAME, 6)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(x * mm, y * mm, "EAC")

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

    def _fit_text_adaptive(
        self,
        c: canvas.Canvas,
        text: str,
        base_font_size: float,
        min_font_size: float,
        max_width_mm: float,
        bold: bool = False,
    ) -> tuple[str, float]:
        """
        Адаптивно подбирает размер шрифта чтобы текст поместился.

        Стратегия:
        1. Пытаемся с базовым размером
        2. Уменьшаем шрифт до минимума
        3. Если всё равно не помещается — обрезаем

        Returns:
            (текст, финальный_размер_шрифта)
        """
        font = FONT_NAME_BOLD if bold else FONT_NAME
        max_width = max_width_mm * mm

        # Пробуем уменьшать шрифт
        current_size = base_font_size
        step = 0.5  # Шаг уменьшения

        while current_size >= min_font_size:
            c.setFont(font, current_size)
            if c.stringWidth(text) <= max_width:
                return text, current_size
            current_size -= step

        # Шрифт минимальный, обрезаем текст
        c.setFont(font, min_font_size)
        truncated = text
        while len(truncated) > 3 and c.stringWidth(truncated + "...") > max_width:
            truncated = truncated[:-1]

        if len(truncated) < len(text):
            truncated += "..."

        return truncated, min_font_size

    def _draw_text_adaptive(
        self,
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        base_font_size: float,
        max_width_mm: float,
        min_font_size: float | None = None,
        centered: bool = False,
        bold: bool = False,
    ) -> float:
        """
        Рисует текст с адаптивным размером шрифта.

        Returns:
            Финальный размер шрифта (для последующих вычислений)
        """
        if min_font_size is None:
            min_font_size = MIN_FONT_SIZES["field"]

        fitted_text, final_size = self._fit_text_adaptive(
            c, text, base_font_size, min_font_size, max_width_mm, bold
        )

        self._draw_text(c, fitted_text, x, y, final_size, centered, bold)
        return final_size

    def _extract_gtin_from_code(self, code: str) -> str | None:
        """Извлекает GTIN (14 цифр) из кода маркировки ЧЗ."""
        # Код ЧЗ начинается с "01" + 14 цифр GTIN
        if code.startswith("01") and len(code) >= 16:
            return code[2:16]
        return None

    def _match_items_with_codes(
        self,
        items: list[LabelItem],
        codes: list[str],
    ) -> list[tuple[LabelItem, str]]:
        """
        Матчинг товаров и кодов ЧЗ по GTIN.

        Логика:
        1. Извлекаем GTIN из каждого кода ЧЗ
        2. GTIN без ведущего 0 = EAN-13 баркод
        3. Сопоставляем с баркодами из items
        4. Количество этикеток = количество кодов ЧЗ

        Returns:
            Список пар (item, code) для генерации этикеток

        Raises:
            ValueError: Если есть коды ЧЗ без соответствующего товара в Excel
        """
        # Индекс товаров по баркоду
        items_by_barcode: dict[str, LabelItem] = {}
        for item in items:
            if item.barcode:
                # Нормализуем баркод (убираем пробелы, ведущие нули)
                normalized = item.barcode.strip().lstrip("0")
                items_by_barcode[normalized] = item
                # Также добавляем оригинальный баркод
                items_by_barcode[item.barcode.strip()] = item

        result: list[tuple[LabelItem, str]] = []
        missing_barcodes: set[str] = set()
        skipped_codes = 0

        for code in codes:
            gtin = self._extract_gtin_from_code(code)
            if not gtin:
                # Невалидный код ЧЗ — пропускаем
                skipped_codes += 1
                continue

            # GTIN → баркод: убираем ведущий 0
            # "04670049774802" → "4670049774802"
            barcode = gtin.lstrip("0")

            item = items_by_barcode.get(barcode)
            if not item:
                # Попробуем найти с полным GTIN
                item = items_by_barcode.get(gtin)

            if item:
                result.append((item, code))
            else:
                missing_barcodes.add(barcode)

        if missing_barcodes:
            barcodes_list = ", ".join(sorted(missing_barcodes)[:5])
            if len(missing_barcodes) > 5:
                barcodes_list += f" и ещё {len(missing_barcodes) - 5}"
            raise ValueError(
                f"Не найдены товары для баркодов: {barcodes_list}. "
                "Добавьте их в Excel файл."
            )

        return result

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
