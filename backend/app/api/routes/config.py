# backend/app/api/routes/config.py
"""
API endpoint для конфигурации layouts этикеток.

Возвращает конфигурацию шаблонов для фронтенда.
"""

from typing import Any

from fastapi import APIRouter

from app.services.label_generator import LABEL_SIZES, LAYOUTS

router = APIRouter(prefix="/api/v1/config", tags=["Config"])

# DPI термопринтера (константа)
DPI = 203


def mm_to_px(mm: float) -> int:
    """Конвертирует миллиметры в пиксели при 203 DPI."""
    return round(mm * DPI / 25.4)


@router.get("/layouts")
async def get_layouts_config() -> dict[str, Any]:
    """
    Возвращает конфигурацию шаблонов для фронтенда.

    Публичный endpoint, авторизация не требуется.

    Returns:
        Структура с размерами этикеток, списком layouts и зонами для каждого layout/size.
    """
    # Конвертируем размеры этикеток в пиксели
    sizes = {}
    for size_name, (width_mm, height_mm) in LABEL_SIZES.items():
        sizes[size_name] = {
            "width_mm": width_mm,
            "height_mm": height_mm,
            "width_px": mm_to_px(width_mm),
            "height_px": mm_to_px(height_mm),
        }

    # Список доступных layouts
    layout_names = list(LAYOUTS.keys())

    # Зоны для каждого layout и размера
    zones: dict[str, dict[str, Any]] = {}
    for layout_name, layout_config in LAYOUTS.items():
        zones[layout_name] = {}
        for size_name, size_config in layout_config.items():
            # Конвертируем координаты зон из мм в пиксели
            zones[layout_name][size_name] = _convert_zones_to_px(size_config)

    return {
        "dpi": DPI,
        "sizes": sizes,
        "layouts": layout_names,
        "zones": zones,
    }


def _convert_zones_to_px(config: dict[str, Any]) -> dict[str, Any]:
    """
    Конвертирует координаты зон из мм в пиксели.

    Сохраняет также исходные значения в мм для удобства отладки.
    """
    result: dict[str, Any] = {}

    for zone_name, zone_config in config.items():
        if not isinstance(zone_config, dict):
            # Скалярные значения (например, text_block_start_y)
            result[zone_name] = {
                "mm": zone_config,
                "px": mm_to_px(zone_config)
                if isinstance(zone_config, (int, float))
                else zone_config,
            }
            continue

        zone_px: dict[str, Any] = {}
        for key, value in zone_config.items():
            if key in ("x", "y", "width", "height", "size", "max_width", "y_start", "y_end"):
                # Координаты и размеры — конвертируем в px
                zone_px[f"{key}_mm"] = value
                zone_px[f"{key}_px"] = mm_to_px(value)
            else:
                # Остальные параметры (centered, bold, text и т.д.) — оставляем как есть
                zone_px[key] = value

        result[zone_name] = zone_px

    return result
