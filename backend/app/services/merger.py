"""
Сервис объединения этикеток WB и кодов Честного Знака.

Основная бизнес-логика: склейка штрихкода WB и DataMatrix ЧЗ на одной этикетке.
"""

import io
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from PIL import Image

from app.config import LABEL, get_settings
from app.models.schemas import LabelMergeResponse, PreflightResult, PreflightStatus
from app.services.csv_parser import CSVParser
from app.services.datamatrix import DataMatrixGenerator
from app.services.pdf_parser import PDFParser, images_to_pdf
from app.services.preflight import PreflightChecker

settings = get_settings()


@dataclass
class MergeResult:
    """Результат объединения одной этикетки."""

    image: Image.Image
    index: int
    success: bool
    error: str | None = None


class LabelMerger:
    """
    Сервис объединения этикеток WB и ЧЗ.

    Workflow:
    1. Парсинг PDF от WB → изображения этикеток
    2. Парсинг CSV/Excel → коды DataMatrix
    3. Генерация DataMatrix для каждого кода
    4. Компоновка: WB слева + DataMatrix справа
    5. Генерация итогового PDF
    """

    def __init__(self):
        self.pdf_parser = PDFParser()
        self.csv_parser = CSVParser()
        self.dm_generator = DataMatrixGenerator()
        self.preflight_checker = PreflightChecker()

    async def merge(
        self,
        wb_pdf_bytes: bytes,
        codes_bytes: bytes,
        codes_filename: str = "codes.csv",
        template: str = "58x40",
        run_preflight: bool = True,
    ) -> LabelMergeResponse:
        """
        Объединение этикеток WB и кодов ЧЗ.

        Args:
            wb_pdf_bytes: PDF с этикетками WB
            codes_bytes: CSV/Excel с кодами ЧЗ
            codes_filename: Имя файла с кодами
            template: Шаблон этикетки (58x40, 58x30, 58x60)
            run_preflight: Выполнять Pre-flight проверку

        Returns:
            LabelMergeResponse с результатом
        """
        # Pre-flight проверка
        preflight_result: PreflightResult | None = None
        if run_preflight:
            preflight_result = await self.preflight_checker.check(
                wb_pdf_bytes, codes_bytes, codes_filename
            )

            # Если критическая ошибка — прерываем
            if not preflight_result.can_proceed:
                return LabelMergeResponse(
                    success=False,
                    labels_count=0,
                    preflight=preflight_result,
                    message="Pre-flight проверка не пройдена. Исправьте ошибки.",
                )

        # Парсим PDF
        try:
            pdf_data = self.pdf_parser.parse(wb_pdf_bytes)
        except ValueError as e:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                preflight=preflight_result,
                message=f"Ошибка чтения PDF: {str(e)}",
            )

        # Парсим коды
        try:
            codes_data = self.csv_parser.parse(codes_bytes, codes_filename)
        except ValueError as e:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                preflight=preflight_result,
                message=f"Ошибка чтения кодов: {str(e)}",
            )

        # Определяем количество этикеток
        labels_count = min(pdf_data.page_count, codes_data.count)

        if labels_count == 0:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                preflight=preflight_result,
                message="Нет данных для генерации этикеток",
            )

        # Проверяем лимит
        if labels_count > settings.max_batch_size:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                preflight=preflight_result,
                message=f"Превышен лимит: {labels_count} этикеток. Максимум: {settings.max_batch_size}",
            )

        # Получаем размеры шаблона
        template_width, template_height = self._get_template_size(template)

        # Объединяем этикетки (параллельно для скорости)
        merged_images = await self._merge_batch(
            wb_images=pdf_data.pages[:labels_count],
            codes=codes_data.codes[:labels_count],
            template_width=template_width,
            template_height=template_height,
        )

        if not merged_images:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                preflight=preflight_result,
                message="Не удалось объединить этикетки",
            )

        # Генерируем PDF
        try:
            pdf_bytes = images_to_pdf(merged_images)
        except Exception as e:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                preflight=preflight_result,
                message=f"Ошибка генерации PDF: {str(e)}",
            )

        # Сохраняем файл и генерируем ID
        file_id = str(uuid.uuid4())

        # TODO: Сохранить pdf_bytes в хранилище (Redis / S3 / файловая система)
        # Пока просто возвращаем file_id

        return LabelMergeResponse(
            success=True,
            labels_count=len(merged_images),
            preflight=preflight_result,
            file_id=file_id,
            download_url=f"/api/v1/labels/download/{file_id}",
            message=f"Успешно сгенерировано {len(merged_images)} этикеток",
        )

    async def _merge_batch(
        self,
        wb_images: list[Image.Image],
        codes: list[str],
        template_width: int,
        template_height: int,
    ) -> list[Image.Image]:
        """
        Параллельное объединение этикеток.

        Использует ThreadPoolExecutor для ускорения.
        """
        # Генерируем все DataMatrix заранее
        dm_images: list[Image.Image] = []
        for code in codes:
            try:
                dm = self.dm_generator.generate(code, with_quiet_zone=False)
                dm_images.append(dm.image)
            except Exception:
                # Создаём placeholder для невалидных кодов
                placeholder = Image.new("RGB", (LABEL.DATAMATRIX_PIXELS, LABEL.DATAMATRIX_PIXELS), "white")
                dm_images.append(placeholder)

        # Объединяем параллельно
        results: list[Image.Image] = []

        def merge_single(index: int) -> MergeResult:
            try:
                merged = self._merge_single_label(
                    wb_image=wb_images[index],
                    dm_image=dm_images[index],
                    template_width=template_width,
                    template_height=template_height,
                )
                return MergeResult(image=merged, index=index, success=True)
            except Exception as e:
                return MergeResult(
                    image=Image.new("RGB", (template_width, template_height), "white"),
                    index=index,
                    success=False,
                    error=str(e),
                )

        # Используем ThreadPool для параллельной обработки
        with ThreadPoolExecutor(max_workers=4) as executor:
            merge_results = list(executor.map(merge_single, range(len(wb_images))))

        # Сортируем по индексу и извлекаем изображения
        merge_results.sort(key=lambda x: x.index)
        results = [r.image for r in merge_results if r.success]

        return results

    def _merge_single_label(
        self,
        wb_image: Image.Image,
        dm_image: Image.Image,
        template_width: int,
        template_height: int,
    ) -> Image.Image:
        """
        Объединение одной этикетки WB с DataMatrix.

        Компоновка:
        - WB штрихкод: левая часть этикетки
        - DataMatrix: правая часть этикетки
        - Зона покоя между кодами
        """
        # Создаём чистую этикетку
        label = Image.new("RGB", (template_width, template_height), "white")

        # Размеры DataMatrix с зоной покоя
        dm_with_quiet = LABEL.DATAMATRIX_PIXELS + 2 * LABEL.QUIET_ZONE_PIXELS

        # Позиция DataMatrix (справа, по центру вертикально)
        dm_x = template_width - dm_with_quiet - LABEL.QUIET_ZONE_PIXELS
        dm_y = (template_height - dm_with_quiet) // 2

        # Доступная ширина для WB штрихкода
        wb_available_width = dm_x - LABEL.QUIET_ZONE_PIXELS * 2

        # Масштабируем WB изображение
        wb_aspect = wb_image.width / wb_image.height
        wb_new_height = template_height - 2 * LABEL.QUIET_ZONE_PIXELS
        wb_new_width = min(int(wb_new_height * wb_aspect), wb_available_width)

        wb_resized = wb_image.resize(
            (wb_new_width, wb_new_height),
            Image.Resampling.LANCZOS,
        )

        # Позиция WB (слева, по центру)
        wb_x = LABEL.QUIET_ZONE_PIXELS
        wb_y = (template_height - wb_new_height) // 2

        # Вставляем WB
        label.paste(wb_resized, (wb_x, wb_y))

        # Масштабируем DataMatrix
        dm_resized = dm_image.resize(
            (dm_with_quiet, dm_with_quiet),
            Image.Resampling.NEAREST,  # NEAREST для сохранения чёткости
        )

        # Вставляем DataMatrix
        label.paste(dm_resized, (dm_x, dm_y))

        return label

    def _get_template_size(self, template: str) -> tuple[int, int]:
        """Получение размеров шаблона в пикселях."""
        templates = {
            "58x40": (LABEL.mm_to_pixels(58), LABEL.mm_to_pixels(40)),
            "58x30": (LABEL.mm_to_pixels(58), LABEL.mm_to_pixels(30)),
            "58x60": (LABEL.mm_to_pixels(58), LABEL.mm_to_pixels(60)),
        }

        return templates.get(template, templates["58x40"])
