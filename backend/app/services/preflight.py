"""
Pre-flight проверка качества этикеток.

Killer feature: проверяем качество ДО печати, чтобы избежать штрафов.
"""

from dataclasses import dataclass

from PIL import Image

from app.config import LABEL
from app.models.schemas import PreflightCheck, PreflightResult, PreflightStatus
from app.services.csv_parser import CSVParser
from app.services.datamatrix import DataMatrixGenerator, validate_datamatrix_readability
from app.services.pdf_parser import PDFParser


@dataclass
class ContrastResult:
    """Результат проверки контрастности."""

    contrast_percent: float
    is_valid: bool
    black_level: int
    white_level: int


class PreflightChecker:
    """
    Pre-flight проверка качества этикеток.

    Проверяет:
    1. Размер DataMatrix (минимум 22x22мм)
    2. Контрастность (минимум 80%)
    3. Наличие quiet zone (3мм)
    4. Читаемость DataMatrix (декодирование)
    5. Соответствие количества страниц и кодов
    """

    def __init__(self):
        self.pdf_parser = PDFParser()
        self.csv_parser = CSVParser()
        self.dm_generator = DataMatrixGenerator()

    async def check(
        self,
        wb_pdf_bytes: bytes,
        codes_bytes: bytes,
        codes_filename: str = "codes.csv",
    ) -> PreflightResult:
        """
        Полная Pre-flight проверка.

        Args:
            wb_pdf_bytes: PDF с этикетками WB
            codes_bytes: Файл с кодами ЧЗ
            codes_filename: Имя файла с кодами

        Returns:
            PreflightResult с результатами всех проверок
        """
        checks: list[PreflightCheck] = []
        overall_status = PreflightStatus.OK
        can_proceed = True

        # 1. Проверка PDF
        try:
            pdf_result = self.pdf_parser.parse(wb_pdf_bytes)
            checks.append(
                PreflightCheck(
                    name="pdf_parse",
                    status=PreflightStatus.OK,
                    message=f"PDF успешно прочитан: {pdf_result.page_count} страниц",
                    details={"page_count": pdf_result.page_count},
                )
            )
        except ValueError as e:
            checks.append(
                PreflightCheck(
                    name="pdf_parse",
                    status=PreflightStatus.ERROR,
                    message=f"Ошибка чтения PDF: {str(e)}",
                )
            )
            overall_status = PreflightStatus.ERROR
            can_proceed = False
            return PreflightResult(
                overall_status=overall_status,
                checks=checks,
                can_proceed=can_proceed,
            )

        # 2. Проверка кодов
        try:
            codes_result = self.csv_parser.parse(codes_bytes, codes_filename)
            checks.append(
                PreflightCheck(
                    name="codes_parse",
                    status=PreflightStatus.OK,
                    message=f"Коды успешно прочитаны: {codes_result.count} шт",
                    details={
                        "count": codes_result.count,
                        "duplicates_removed": codes_result.duplicates_removed,
                        "invalid_removed": codes_result.invalid_removed,
                    },
                )
            )

            # Предупреждение о дубликатах
            if codes_result.duplicates_removed > 0:
                checks.append(
                    PreflightCheck(
                        name="duplicates",
                        status=PreflightStatus.WARNING,
                        message=f"Удалено {codes_result.duplicates_removed} дубликатов кодов",
                    )
                )
                if overall_status == PreflightStatus.OK:
                    overall_status = PreflightStatus.WARNING

        except ValueError as e:
            checks.append(
                PreflightCheck(
                    name="codes_parse",
                    status=PreflightStatus.ERROR,
                    message=f"Ошибка чтения кодов: {str(e)}",
                )
            )
            overall_status = PreflightStatus.ERROR
            can_proceed = False
            return PreflightResult(
                overall_status=overall_status,
                checks=checks,
                can_proceed=can_proceed,
            )

        # 3. Проверка соответствия количества
        if pdf_result.page_count != codes_result.count:
            if pdf_result.page_count < codes_result.count:
                checks.append(
                    PreflightCheck(
                        name="count_match",
                        status=PreflightStatus.WARNING,
                        message=(
                            f"Кодов ({codes_result.count}) больше чем страниц PDF "
                            f"({pdf_result.page_count}). Лишние коды будут пропущены."
                        ),
                        details={
                            "pages": pdf_result.page_count,
                            "codes": codes_result.count,
                        },
                    )
                )
            else:
                checks.append(
                    PreflightCheck(
                        name="count_match",
                        status=PreflightStatus.ERROR,
                        message=(
                            f"Страниц PDF ({pdf_result.page_count}) больше чем кодов "
                            f"({codes_result.count}). Не хватает кодов для всех этикеток."
                        ),
                        details={
                            "pages": pdf_result.page_count,
                            "codes": codes_result.count,
                        },
                    )
                )
                overall_status = PreflightStatus.ERROR
                can_proceed = False
        else:
            checks.append(
                PreflightCheck(
                    name="count_match",
                    status=PreflightStatus.OK,
                    message=f"Количество совпадает: {pdf_result.page_count} этикеток",
                )
            )

        # 4. Проверка первого DataMatrix (sample check)
        if codes_result.codes:
            try:
                dm = self.dm_generator.generate(codes_result.codes[0])

                # Проверка размера
                size_check = self._check_datamatrix_size(dm.width_mm, dm.height_mm)
                checks.append(size_check)
                if size_check.status == PreflightStatus.ERROR:
                    overall_status = PreflightStatus.ERROR
                    can_proceed = False
                elif size_check.status == PreflightStatus.WARNING:
                    if overall_status == PreflightStatus.OK:
                        overall_status = PreflightStatus.WARNING

                # Проверка читаемости
                readability_check = self._check_readability(dm.image)
                checks.append(readability_check)
                if readability_check.status == PreflightStatus.ERROR:
                    overall_status = PreflightStatus.ERROR
                    can_proceed = False

                # Проверка зоны покоя (quiet zone)
                quiet_zone_check = self._check_quiet_zone(dm.image)
                checks.append(quiet_zone_check)
                if quiet_zone_check.status == PreflightStatus.ERROR:
                    overall_status = PreflightStatus.ERROR
                    can_proceed = False
                elif quiet_zone_check.status == PreflightStatus.WARNING:
                    if overall_status == PreflightStatus.OK:
                        overall_status = PreflightStatus.WARNING

            except Exception as e:
                checks.append(
                    PreflightCheck(
                        name="datamatrix_generate",
                        status=PreflightStatus.ERROR,
                        message=f"Ошибка генерации DataMatrix: {str(e)}",
                    )
                )
                overall_status = PreflightStatus.ERROR
                can_proceed = False

        # 5. Проверка контрастности первой страницы PDF
        if pdf_result.pages:
            contrast_check = self._check_contrast(pdf_result.pages[0])
            checks.append(contrast_check)
            if (
                contrast_check.status == PreflightStatus.WARNING
                and overall_status == PreflightStatus.OK
            ):
                overall_status = PreflightStatus.WARNING

        return PreflightResult(
            overall_status=overall_status,
            checks=checks,
            can_proceed=can_proceed,
        )

    def _check_datamatrix_size(self, width_mm: float, height_mm: float) -> PreflightCheck:
        """Проверка размера DataMatrix."""
        min_size = LABEL.DATAMATRIX_MIN_MM

        if width_mm < min_size or height_mm < min_size:
            return PreflightCheck(
                name="datamatrix_size",
                status=PreflightStatus.ERROR,
                message=(
                    f"DataMatrix слишком маленький: {width_mm:.1f}x{height_mm:.1f}мм. "
                    f"Минимум: {min_size}x{min_size}мм"
                ),
                details={
                    "width_mm": round(width_mm, 1),
                    "height_mm": round(height_mm, 1),
                    "min_mm": min_size,
                },
            )

        return PreflightCheck(
            name="datamatrix_size",
            status=PreflightStatus.OK,
            message=f"Размер DataMatrix OK: {width_mm:.1f}x{height_mm:.1f}мм",
            details={
                "width_mm": round(width_mm, 1),
                "height_mm": round(height_mm, 1),
            },
        )

    def _check_readability(self, img: Image.Image) -> PreflightCheck:
        """Проверка читаемости DataMatrix."""
        is_readable = validate_datamatrix_readability(img)

        if is_readable:
            return PreflightCheck(
                name="datamatrix_readable",
                status=PreflightStatus.OK,
                message="DataMatrix успешно декодируется",
            )
        else:
            return PreflightCheck(
                name="datamatrix_readable",
                status=PreflightStatus.ERROR,
                message="DataMatrix НЕ читается сканером! Проверьте код.",
            )

    def _check_contrast(self, img: Image.Image) -> PreflightCheck:
        """Проверка контрастности изображения."""
        result = self._calculate_contrast(img)

        if result.contrast_percent >= LABEL.MIN_CONTRAST_PERCENT:
            return PreflightCheck(
                name="contrast",
                status=PreflightStatus.OK,
                message=f"Контрастность OK: {result.contrast_percent:.0f}%",
                details={"contrast_percent": round(result.contrast_percent)},
            )
        elif result.contrast_percent >= LABEL.MIN_CONTRAST_PERCENT - 10:
            return PreflightCheck(
                name="contrast",
                status=PreflightStatus.WARNING,
                message=(
                    f"Контрастность на границе: {result.contrast_percent:.0f}%. "
                    f"Рекомендуется минимум {LABEL.MIN_CONTRAST_PERCENT}%"
                ),
                details={"contrast_percent": round(result.contrast_percent)},
            )
        else:
            return PreflightCheck(
                name="contrast",
                status=PreflightStatus.ERROR,
                message=(
                    f"Контрастность слишком низкая: {result.contrast_percent:.0f}%. "
                    f"Минимум {LABEL.MIN_CONTRAST_PERCENT}%"
                ),
                details={"contrast_percent": round(result.contrast_percent)},
            )

    def _check_quiet_zone(self, img: Image.Image) -> PreflightCheck:
        """
        Проверка зоны покоя (quiet zone) вокруг DataMatrix.

        Требование: минимум 3мм белого пространства вокруг кода.
        При 203 DPI это ~24 пикселя.
        """
        min_quiet_zone_px = LABEL.QUIET_ZONE_PIXELS  # 24px = 3мм при 203 DPI

        # Конвертируем в grayscale и бинаризуем
        gray = img.convert("L")
        # Порог бинаризации: всё темнее 200 считается "чёрным"
        threshold = 200

        # Находим bounding box чёрных пикселей (DataMatrix)
        pixels = gray.load()
        width, height = gray.size

        min_x, min_y = width, height
        max_x, max_y = 0, 0

        for y in range(height):
            for x in range(width):
                if pixels[x, y] < threshold:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        # Если DataMatrix не найден
        if max_x == 0 and max_y == 0:
            return PreflightCheck(
                name="quiet_zone",
                status=PreflightStatus.WARNING,
                message="Не удалось определить границы DataMatrix для проверки quiet zone",
            )

        # Проверяем отступы от краёв
        left_margin = min_x
        right_margin = width - max_x - 1
        top_margin = min_y
        bottom_margin = height - max_y - 1

        margins = {
            "left": left_margin,
            "right": right_margin,
            "top": top_margin,
            "bottom": bottom_margin,
        }

        # Находим минимальный отступ
        min_margin = min(margins.values())
        min_margin_mm = LABEL.pixels_to_mm(min_margin)
        required_mm = LABEL.QUIET_ZONE_MM

        # Проверяем, достаточна ли зона покоя
        if min_margin >= min_quiet_zone_px:
            return PreflightCheck(
                name="quiet_zone",
                status=PreflightStatus.OK,
                message=f"Зона покоя OK: минимум {min_margin_mm:.1f}мм (требуется {required_mm}мм)",
                details={
                    "min_margin_px": min_margin,
                    "min_margin_mm": round(min_margin_mm, 1),
                    "required_mm": required_mm,
                    "margins_px": margins,
                },
            )
        elif min_margin >= min_quiet_zone_px * 0.7:  # 70% от нормы — warning
            return PreflightCheck(
                name="quiet_zone",
                status=PreflightStatus.WARNING,
                message=(
                    f"Зона покоя мала: {min_margin_mm:.1f}мм. "
                    f"Рекомендуется минимум {required_mm}мм для надёжного сканирования"
                ),
                details={
                    "min_margin_px": min_margin,
                    "min_margin_mm": round(min_margin_mm, 1),
                    "required_mm": required_mm,
                    "margins_px": margins,
                },
            )
        else:
            return PreflightCheck(
                name="quiet_zone",
                status=PreflightStatus.ERROR,
                message=(
                    f"Зона покоя недостаточна: {min_margin_mm:.1f}мм! "
                    f"Требуется минимум {required_mm}мм. Код может не сканироваться!"
                ),
                details={
                    "min_margin_px": min_margin,
                    "min_margin_mm": round(min_margin_mm, 1),
                    "required_mm": required_mm,
                    "margins_px": margins,
                },
            )

    def _calculate_contrast(self, img: Image.Image) -> ContrastResult:
        """
        Расчёт контрастности изображения.

        Для штрихкодов важна разница между самыми тёмными и самыми светлыми пикселями,
        а не процентили. Этикетка может быть 95% белой с тонкими чёрными линиями.
        """
        # Конвертируем в grayscale
        gray = img.convert("L")

        # Получаем гистограмму
        histogram = gray.histogram()

        # Находим фактические минимум и максимум (не процентили!)
        # Ищем самый тёмный пиксель (black_level)
        black_level = 0
        for i in range(256):
            if histogram[i] > 0:
                black_level = i
                break

        # Ищем самый светлый пиксель (white_level)
        white_level = 255
        for i in range(255, -1, -1):
            if histogram[i] > 0:
                white_level = i
                break

        # Контрастность как разница между белым и черным
        contrast = (white_level - black_level) / 255.0 * 100

        return ContrastResult(
            contrast_percent=contrast,
            is_valid=contrast >= LABEL.MIN_CONTRAST_PERCENT,
            black_level=black_level,
            white_level=white_level,
        )
