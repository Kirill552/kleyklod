# backend/app/services/layout_preflight.py
"""
Pre-flight проверка данных этикетки ПЕРЕД генерацией.

Цель: проверить данные до генерации, чтобы не тратить лимит пользователя
на заведомо плохие этикетки.

Проверки:
1. Количество активных полей vs лимит шаблона
2. Ширина текста — поместится ли при минимальном шрифте
3. Размер DataMatrix (>= 22мм) — проверяется в основном preflight
"""

from dataclasses import dataclass
from typing import Literal

# ReportLab для измерения ширины текста
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Константы шрифтов из label_generator
FONT_NAME = "LabelFont"
FONT_NAME_BOLD = "LabelFont-Bold"

# Путь к шрифтам (совпадает с label_generator)
DEJAVU_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEJAVU_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LIBERATION_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
LIBERATION_BOLD_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
ARIAL_PATH = "C:/Windows/Fonts/arial.ttf"
ARIAL_BOLD_PATH = "C:/Windows/Fonts/arialbd.ttf"

# Флаг инициализации шрифта
_font_registered = False


def _ensure_font_registered() -> None:
    """Регистрирует шрифты для измерения ширины текста."""
    global _font_registered
    if _font_registered:
        return

    import os

    font_options = [
        (ARIAL_PATH, ARIAL_BOLD_PATH),
        (LIBERATION_PATH, LIBERATION_BOLD_PATH),
        (DEJAVU_PATH, DEJAVU_BOLD_PATH),
    ]

    for font_path, bold_path in font_options:
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

    _font_registered = True


# === Лимиты полей по шаблонам (из Excel) ===
# Структура: {layout: {template: max_fields}}
# Включает название товара + текстовый блок
# ИНН не считается — он из настроек пользователя, не из Excel
FIELD_LIMITS = {
    "basic": {
        "58x30": 4,  # название + 3 поля (артикул, размер, цвет)
        "58x40": 5,  # название + 4 поля
        "58x60": 5,  # название + 4 поля
    },
    "extended": {
        "58x40": 12,  # до 12 полей включая название
        "58x60": 12,
    },
    "professional": {
        "58x40": 11,  # название + 10 полей текст. блока
    },
}

# === Максимальная ширина текста (мм) по шаблонам ===
# Используем значения max_width из LAYOUTS в label_generator.py
MAX_TEXT_WIDTH_MM = {
    "basic": {
        "58x30": 28.0,  # B30_TEXT_MAX_WIDTH
        "58x40": 31.0,  # B40_TEXT_MAX_WIDTH
        "58x60": 33.0,  # Правая колонка basic 58x60
    },
    "extended": {
        "58x40": 31.0,  # EXT_TEXT_MAX_WIDTH
        "58x60": 31.0,
    },
    "professional": {
        "58x40": 30.0,  # PROF_MAX_TEXT_WIDTH
    },
}

# === Минимальные размеры шрифтов (pt) ===
# При этих размерах текст должен влезать
MIN_FONT_SIZES = {
    "basic": {
        "organization": 3.5,  # pt
        "inn": 3.5,
        "name": 5.0,
        "field": 4.0,  # цвет, размер, артикул
    },
    "extended": {
        "organization": 3.5,
        "inn": 3.5,
        "field": 4.5,
    },
    "professional": {
        "organization": 4.0,
        "inn": 4.0,
        "name": 5.0,
        "field": 4.0,
    },
}


@dataclass
class PreflightError:
    """Ошибка preflight проверки."""

    field_id: str  # ID поля для привязки к UI
    message: str  # Сообщение об ошибке
    suggestion: str | None = None  # Предложение по исправлению


@dataclass
class PreflightResult:
    """Результат preflight проверки."""

    success: bool
    errors: list[PreflightError]
    suggestions: list[str]  # Глобальные предложения


class LayoutPreflightChecker:
    """
    Проверка данных этикетки ПЕРЕД генерацией.

    Позволяет выявить проблемы до того, как лимит будет потрачен.
    """

    def __init__(self):
        _ensure_font_registered()

    def check(
        self,
        template: Literal["58x30", "58x40", "58x60"],
        layout: Literal["basic", "professional", "extended"],
        fields: list[dict],  # [{"id": "article", "key": "Артикул", "value": "..."}]
        organization: str | None = None,
        inn: str | None = None,
    ) -> PreflightResult:
        """
        Выполнить preflight проверку.

        Args:
            template: Размер этикетки (58x30, 58x40, 58x60)
            layout: Шаблон (basic, professional, extended)
            fields: Список полей с id, key и value
            organization: Название организации
            inn: ИНН организации

        Returns:
            PreflightResult с ошибками и предложениями
        """
        errors: list[PreflightError] = []
        suggestions: list[str] = []

        # === 1. Проверка доступности шаблона для layout ===
        if layout not in FIELD_LIMITS:
            errors.append(
                PreflightError(
                    field_id="layout",
                    message=f"Неизвестный шаблон: {layout}",
                    suggestion="Используйте basic, professional или extended",
                )
            )
            return PreflightResult(success=False, errors=errors, suggestions=suggestions)

        if template not in FIELD_LIMITS.get(layout, {}):
            available = list(FIELD_LIMITS.get(layout, {}).keys())
            errors.append(
                PreflightError(
                    field_id="template",
                    message=f"Шаблон {layout} не поддерживает размер {template}",
                    suggestion=f"Доступные размеры для {layout}: {', '.join(available)}",
                )
            )
            return PreflightResult(success=False, errors=errors, suggestions=suggestions)

        # === 2. Проверка количества полей ===
        max_fields = FIELD_LIMITS[layout][template]
        active_fields = [f for f in fields if f.get("value")]

        if len(active_fields) > max_fields:
            errors.append(
                PreflightError(
                    field_id="fields_count",
                    message=f"Слишком много полей: {len(active_fields)} из {max_fields} максимум",
                    suggestion=self._suggest_layout_for_fields(len(active_fields), template),
                )
            )

        # === 3. Проверка ширины текста полей ===
        max_width_mm = MAX_TEXT_WIDTH_MM.get(layout, {}).get(template, 30.0)
        min_font_sizes = MIN_FONT_SIZES.get(layout, {})

        for field in active_fields:
            field_id = field.get("id", "unknown")
            value = field.get("value", "")

            if not value:
                continue

            # Определяем минимальный шрифт для типа поля
            if field_id in ("organization",):
                min_font = min_font_sizes.get("organization", 3.5)
            elif field_id in ("inn",):
                min_font = min_font_sizes.get("inn", 3.5)
            elif field_id in ("name",):
                min_font = min_font_sizes.get("name", 5.0)
            else:
                min_font = min_font_sizes.get("field", 4.0)

            # Проверяем поместится ли текст
            text_error = self._check_text_width(
                text=value,
                max_width_mm=max_width_mm,
                min_font_pt=min_font,
                field_id=field_id,
            )
            if text_error:
                errors.append(text_error)

        # === 4. Проверка организации ===
        if organization:
            min_org_font = min_font_sizes.get("organization", 3.5)
            org_error = self._check_text_width(
                text=organization,
                max_width_mm=max_width_mm,
                min_font_pt=min_org_font,
                field_id="organization",
            )
            if org_error:
                errors.append(org_error)

        # === 5. Проверка ИНН ===
        if inn:
            # ИНН обычно короткий (10-12 цифр), но проверим на всякий случай
            min_inn_font = min_font_sizes.get("inn", 3.5)
            inn_error = self._check_text_width(
                text=f"ИНН {inn}",
                max_width_mm=max_width_mm,
                min_font_pt=min_inn_font,
                field_id="inn",
            )
            if inn_error:
                errors.append(inn_error)

        # === 6. Глобальные предложения ===
        if errors:
            # Предложить больший размер если текущий маленький
            if template == "58x30" and layout == "basic":
                suggestions.append(
                    "Размер 58x30 очень компактный. Рассмотрите 58x40 для большего количества информации."
                )

            # Предложить extended если много полей
            if layout == "basic" and len(active_fields) > 4:
                suggestions.append(
                    "Для большего количества полей используйте шаблон Extended (до 12 полей)."
                )

        return PreflightResult(
            success=len(errors) == 0,
            errors=errors,
            suggestions=suggestions,
        )

    def _check_text_width(
        self,
        text: str,
        max_width_mm: float,
        min_font_pt: float,
        field_id: str,
    ) -> PreflightError | None:
        """
        Проверяет, влезает ли текст в указанную ширину при минимальном шрифте.

        Args:
            text: Текст для проверки
            max_width_mm: Максимальная ширина в мм
            min_font_pt: Минимальный размер шрифта в pt
            field_id: ID поля для ошибки

        Returns:
            PreflightError если текст не влезает, иначе None
        """
        if not text:
            return None

        try:
            # Измеряем ширину текста при минимальном шрифте
            text_width_pt = pdfmetrics.stringWidth(text, FONT_NAME, min_font_pt)
            text_width_mm = text_width_pt / mm

            if text_width_mm > max_width_mm:
                # Считаем на сколько нужно сократить
                overflow_percent = int((text_width_mm / max_width_mm - 1) * 100)
                max_chars = self._estimate_max_chars(max_width_mm, min_font_pt)

                return PreflightError(
                    field_id=field_id,
                    message=f"Текст не влезает в ширину ({max_width_mm:.0f}мм)",
                    suggestion=f"Сократите текст на ~{overflow_percent}% (макс. ~{max_chars} символов)",
                )
        except Exception:
            # Если не удалось измерить — пропускаем проверку
            pass

        return None

    def _estimate_max_chars(self, max_width_mm: float, font_pt: float) -> int:
        """
        Оценивает максимальное количество символов для ширины.

        Использует среднюю ширину символа для кириллицы.
        """
        # Средняя ширина символа примерно 0.5 * font_size для кириллицы
        avg_char_width_pt = font_pt * 0.55
        avg_char_width_mm = avg_char_width_pt / mm
        return int(max_width_mm / avg_char_width_mm)

    def _suggest_layout_for_fields(self, fields_count: int, template: str) -> str:
        """Предлагает подходящий layout для количества полей."""
        if fields_count <= 4:
            return "Используйте шаблон Basic для 4 полей"
        elif fields_count <= 10:
            if template in ("58x40",):
                return "Используйте шаблон Professional для 10 полей"
            else:
                return "Используйте шаблон Extended для 12 полей"
        else:
            return "Используйте шаблон Extended (до 12 полей) на размере 58x40 или 58x60"


def count_excel_fields(sample_item: dict | None) -> int:
    """
    Подсчитывает количество заполненных полей в первом элементе Excel.

    Учитываемые поля (11 из Excel):
    - name (название)
    - article (артикул)
    - size (размер)
    - color (цвет)
    - brand (бренд)
    - composition (состав)
    - country (страна)
    - manufacturer (производитель)
    - production_date (дата производства)
    - importer (импортёр)
    - certificate_number (сертификат)

    НЕ учитываются:
    - barcode (служебное)
    - organization, inn, address (из настроек пользователя)
    """
    if not sample_item:
        return 0

    excel_field_names = [
        "name",
        "article",
        "size",
        "color",
        "brand",
        "composition",
        "country",
        "manufacturer",
        "production_date",
        "importer",
        "certificate_number",
    ]

    count = 0
    for field in excel_field_names:
        value = (
            sample_item.get(field)
            if isinstance(sample_item, dict)
            else getattr(sample_item, field, None)
        )
        if value and str(value).strip():
            count += 1

    return count


def check_field_limits(
    layout: Literal["basic", "professional", "extended"],
    template: Literal["58x30", "58x40", "58x60"],
    filled_fields_count: int,
) -> PreflightError | None:
    """
    Проверяет количество полей против лимита шаблона.

    Args:
        layout: Шаблон (basic, professional, extended)
        template: Размер этикетки (58x30, 58x40, 58x60)
        filled_fields_count: Количество заполненных полей из Excel

    Returns:
        PreflightError если лимит превышен, иначе None
    """
    # Получаем лимит для комбинации layout + template
    layout_limits = FIELD_LIMITS.get(layout, {})
    max_fields = layout_limits.get(template)

    if max_fields is None:
        # Нет лимита для этой комбинации — пропускаем
        return None

    if filled_fields_count > max_fields:
        # Формируем рекомендацию
        suggestions = []

        # Предлагаем другой layout
        if layout == "basic":
            if filled_fields_count <= 11:
                suggestions.append("Professional (до 11 полей)")
            suggestions.append("Extended (до 12 полей)")
        elif layout == "professional":
            suggestions.append("Extended (до 12 полей)")

        suggestion_text = (
            f"Используйте шаблон {' или '.join(suggestions)}"
            if suggestions
            else "Уберите лишние колонки из Excel"
        )

        return PreflightError(
            field_id="fields_count",
            message=(
                f"Слишком много полей в Excel: {filled_fields_count} из {max_fields} максимум "
                f"для шаблона {layout.capitalize()} {template}"
            ),
            suggestion=suggestion_text,
        )
