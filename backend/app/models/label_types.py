# backend/app/models/label_types.py
"""
Типы данных для генерации этикеток из Excel.
"""

from dataclasses import dataclass
from enum import Enum


class LabelLayout(str, Enum):
    """Варианты шаблона этикетки."""

    BASIC = "basic"  # Базовый: вертикальный, DataMatrix слева, штрихкод справа внизу
    PROFESSIONAL = "professional"  # Профессиональный: двухколоночный с реквизитами
    EXTENDED = "extended"  # Расширенный: 12 полей с лейблами, выравнивание влево


class LabelSize(str, Enum):
    """Размеры этикеток."""

    SIZE_58x40 = "58x40"
    SIZE_58x30 = "58x30"
    SIZE_58x60 = "58x60"

    @property
    def dimensions_mm(self) -> tuple[float, float]:
        """Возвращает (ширина, высота) в мм."""
        sizes = {
            "58x40": (58.0, 40.0),
            "58x30": (58.0, 30.0),
            "58x60": (58.0, 60.0),
        }
        return sizes[self.value]


@dataclass
class LabelData:
    """Данные для одной этикетки."""

    barcode: str
    article: str | None = None
    size: str | None = None
    color: str | None = None
    name: str | None = None
    brand: str | None = None
    composition: str | None = None  # Состав изделия
    organization: str | None = None
    # Реквизиты для профессионального шаблона
    inn: str | None = None
    organization_address: str | None = None
    production_country: str | None = None
    importer: str | None = None
    manufacturer: str | None = None
    production_date: str | None = None
    certificate_number: str | None = None


@dataclass
class ShowFields:
    """Какие поля показывать на этикетке."""

    # Основные поля
    article: bool = True
    size_color: bool = True
    name: bool = True
    brand: bool = False  # Бренд

    # Расширенные поля (как у конкурентов)
    organization: bool = True  # Название организации
    inn: bool = False  # ИНН (по умолчанию выключен)
    country: bool = False  # Страна производства
    composition: bool = False  # Состав
    chz_code_text: bool = True  # Код ЧЗ текстом под DataMatrix
    serial_number: bool = False  # Серийный номер (№ 0001)

    # Реквизиты для профессионального шаблона
    importer: bool = False  # Импортер
    manufacturer: bool = False  # Производитель
    address: bool = False  # Адрес производства
    production_date: bool = False  # Дата производства
    certificate: bool = False  # Номер сертификата
