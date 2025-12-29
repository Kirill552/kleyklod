# backend/app/models/label_types.py
"""
Типы данных для генерации этикеток из Excel.
"""

from dataclasses import dataclass
from enum import Enum


class LabelLayout(str, Enum):
    """Варианты layout этикетки."""

    CLASSIC = "classic"  # Вертикальный: штрихкод сверху, текст снизу
    COMPACT = "compact"  # Горизонтальный: штрихкод слева, текст справа
    MINIMAL = "minimal"  # Только штрихкод + артикул


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
    organization: str | None = None


@dataclass
class ShowFields:
    """Какие поля показывать на этикетке."""

    article: bool = True
    size_color: bool = True
    name: bool = True
