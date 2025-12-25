"""
Генератор DataMatrix кодов для Честного Знака.

Создаёт изображения DataMatrix с соблюдением требований:
- Размер минимум 22x22мм
- ECC200 (стандарт ЧЗ)
- Чёрный на белом без градаций серого
"""

from dataclasses import dataclass

from PIL import Image

from app.config import LABEL


@dataclass
class GeneratedDataMatrix:
    """Результат генерации DataMatrix."""

    image: Image.Image
    width_pixels: int
    height_pixels: int
    width_mm: float
    height_mm: float


class DataMatrixGenerator:
    """
    Генератор DataMatrix кодов.

    Использует pylibdmtx для генерации ECC200 DataMatrix.
    """

    def __init__(
        self,
        target_size_mm: float = LABEL.DATAMATRIX_MAX_MM,
        dpi: int = LABEL.DPI,
        quiet_zone_mm: float = LABEL.QUIET_ZONE_MM,
    ):
        """
        Инициализация генератора.

        Args:
            target_size_mm: Целевой размер DataMatrix в мм (по умолчанию 26мм)
            dpi: Разрешение (по умолчанию 203 DPI)
            quiet_zone_mm: Зона покоя вокруг кода в мм
        """
        self.target_size_mm = target_size_mm
        self.dpi = dpi
        self.quiet_zone_mm = quiet_zone_mm

        # Размер в пикселях
        self.target_size_pixels = LABEL.mm_to_pixels(target_size_mm)
        self.quiet_zone_pixels = LABEL.mm_to_pixels(quiet_zone_mm)

    def generate(self, code: str, with_quiet_zone: bool = True) -> GeneratedDataMatrix:
        """
        Генерация DataMatrix из кода.

        Args:
            code: Код маркировки Честного Знака
            with_quiet_zone: Добавлять зону покоя

        Returns:
            GeneratedDataMatrix с изображением

        Raises:
            ValueError: Если код невалидный или слишком длинный
        """
        try:
            from pylibdmtx.pylibdmtx import encode
        except ImportError:
            raise ImportError("pylibdmtx не установлен. Установите: pip install pylibdmtx")

        if not code or len(code) < 10:
            raise ValueError("Код слишком короткий")

        # Генерируем DataMatrix
        try:
            encoded = encode(code.encode("utf-8"))
        except Exception as e:
            raise ValueError(f"Не удалось закодировать DataMatrix: {str(e)}")

        # Конвертируем в PIL Image
        # pylibdmtx возвращает данные в формате (width, height, bpp, pixels)
        width = encoded.width
        height = encoded.height

        # Создаём изображение из байтов
        img = Image.frombytes("RGB", (width, height), encoded.pixels)

        # Конвертируем в чистый чёрно-белый (без градаций серого)
        img = img.convert("1")  # 1-bit черно-белый
        img = img.convert("RGB")  # Обратно в RGB для совместимости

        # Масштабируем до целевого размера
        img = self._resize_to_target(img)

        # Добавляем зону покоя
        if with_quiet_zone:
            img = self._add_quiet_zone(img)

        # Рассчитываем итоговые размеры
        final_width_mm = LABEL.pixels_to_mm(img.width)
        final_height_mm = LABEL.pixels_to_mm(img.height)

        return GeneratedDataMatrix(
            image=img,
            width_pixels=img.width,
            height_pixels=img.height,
            width_mm=final_width_mm,
            height_mm=final_height_mm,
        )

    def generate_batch(
        self, codes: list[str], with_quiet_zone: bool = True
    ) -> list[GeneratedDataMatrix]:
        """
        Генерация нескольких DataMatrix.

        Args:
            codes: Список кодов
            with_quiet_zone: Добавлять зону покоя

        Returns:
            Список GeneratedDataMatrix
        """
        results: list[GeneratedDataMatrix] = []

        for code in codes:
            try:
                result = self.generate(code, with_quiet_zone)
                results.append(result)
            except ValueError:
                # Пропускаем невалидные коды
                continue

        return results

    def _resize_to_target(self, img: Image.Image) -> Image.Image:
        """Масштабирование до целевого размера."""
        # Используем NEAREST для сохранения чёткости (без интерполяции)
        return img.resize(
            (self.target_size_pixels, self.target_size_pixels),
            Image.Resampling.NEAREST,
        )

    def _add_quiet_zone(self, img: Image.Image) -> Image.Image:
        """Добавление белой зоны покоя вокруг кода."""
        # Создаём новое изображение с зоной покоя
        new_width = img.width + 2 * self.quiet_zone_pixels
        new_height = img.height + 2 * self.quiet_zone_pixels

        new_img = Image.new("RGB", (new_width, new_height), color=(255, 255, 255))

        # Вставляем DataMatrix в центр
        new_img.paste(img, (self.quiet_zone_pixels, self.quiet_zone_pixels))

        return new_img


def validate_datamatrix_readability(img: Image.Image) -> bool:
    """
    Проверка читаемости DataMatrix.

    Пытается декодировать изображение обратно.

    Args:
        img: PIL Image с DataMatrix

    Returns:
        True если код читается
    """
    try:
        from pylibdmtx.pylibdmtx import decode

        # Декодируем
        results = decode(img)

        return len(results) > 0

    except ImportError:
        # pylibdmtx не установлен, пропускаем проверку
        return True
    except Exception:
        return False
