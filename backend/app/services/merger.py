"""
Сервис объединения этикеток WB и кодов Честного Знака.

Основная бизнес-логика: склейка штрихкода WB и DataMatrix ЧЗ на одной этикетке.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from PIL import Image

from app.config import LABEL, get_settings
from app.models.schemas import LabelFormat, LabelMergeResponse, PreflightResult
from app.services.csv_parser import CSVParser
from app.services.datamatrix import DataMatrixGenerator
from app.services.file_storage import file_storage
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
        label_format: str = "combined",
    ) -> LabelMergeResponse:
        """
        Объединение этикеток WB и кодов ЧЗ.

        Args:
            wb_pdf_bytes: PDF с этикетками WB
            codes_bytes: CSV/Excel с кодами ЧЗ
            codes_filename: Имя файла с кодами
            template: Шаблон этикетки (58x40, 58x30, 58x60)
            run_preflight: Выполнять Pre-flight проверку
            label_format: Формат (combined — на одной, separate — раздельные)

        Returns:
            LabelMergeResponse с результатом
        """
        # Нормализуем label_format
        format_enum = LabelFormat.SEPARATE if label_format == "separate" else LabelFormat.COMBINED
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
                    pages_count=0,
                    label_format=format_enum,
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
                pages_count=0,
                label_format=format_enum,
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
                pages_count=0,
                label_format=format_enum,
                preflight=preflight_result,
                message=f"Ошибка чтения кодов: {str(e)}",
            )

        # Определяем количество этикеток
        labels_count = min(pdf_data.page_count, codes_data.count)

        if labels_count == 0:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                pages_count=0,
                label_format=format_enum,
                preflight=preflight_result,
                message="Нет данных для генерации этикеток",
            )

        # Проверяем лимит
        if labels_count > settings.max_batch_size:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                pages_count=0,
                label_format=format_enum,
                preflight=preflight_result,
                message=f"Превышен лимит: {labels_count} этикеток. Максимум: {settings.max_batch_size}",
            )

        # Получаем размеры шаблона
        template_width, template_height = self._get_template_size(template)

        # Объединяем этикетки в зависимости от формата
        if format_enum == LabelFormat.SEPARATE:
            # Раздельные этикетки: WB1, DM1, WB2, DM2, ...
            merged_images = await self._merge_batch_separate(
                wb_images=pdf_data.pages[:labels_count],
                codes=codes_data.codes[:labels_count],
                template_width=template_width,
                template_height=template_height,
            )
            pages_count = labels_count * 2
        else:
            # Объединённые этикетки (по умолчанию)
            merged_images = await self._merge_batch(
                wb_images=pdf_data.pages[:labels_count],
                codes=codes_data.codes[:labels_count],
                template_width=template_width,
                template_height=template_height,
            )
            pages_count = labels_count

        if not merged_images:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                pages_count=0,
                label_format=format_enum,
                preflight=preflight_result,
                message="Не удалось объединить этикетки",
            )

        # Генерируем PDF
        try:
            _pdf_bytes = images_to_pdf(merged_images)
        except Exception as e:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                pages_count=0,
                label_format=format_enum,
                preflight=preflight_result,
                message=f"Ошибка генерации PDF: {str(e)}",
            )

        # Сохраняем файл и генерируем ID
        file_id = str(uuid.uuid4())

        # Сохраняем в хранилище (1 час TTL)
        file_storage.save(
            file_id=file_id,
            data=_pdf_bytes,
            filename="labels.pdf",
            content_type="application/pdf",
            ttl_seconds=3600,
        )

        format_text = "раздельном" if format_enum == LabelFormat.SEPARATE else "объединённом"
        return LabelMergeResponse(
            success=True,
            labels_count=labels_count,
            pages_count=pages_count,
            label_format=format_enum,
            preflight=preflight_result,
            file_id=file_id,
            download_url=f"/api/v1/labels/download/{file_id}",
            message=f"Успешно сгенерировано {labels_count} этикеток ({pages_count} стр.) в {format_text} формате",
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
                placeholder = Image.new(
                    "RGB", (LABEL.DATAMATRIX_PIXELS, LABEL.DATAMATRIX_PIXELS), "white"
                )
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
                    code=codes[index],
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
        code: str = "",
    ) -> Image.Image:
        """
        Объединение одной этикетки WB с DataMatrix.

        Компоновка (side-by-side):
        - WB этикетка слева
        - DataMatrix справа с подписью "Честный знак" и кодом
        """
        from PIL import ImageDraw, ImageFont

        # Создаём чистую белую этикетку
        label = Image.new("RGB", (template_width, template_height), "white")
        draw = ImageDraw.Draw(label)

        # Размеры текста под DataMatrix
        text_height = LABEL.mm_to_pixels(5)  # 5мм на текст

        # DataMatrix = 22мм (минимум по ЧЗ)
        dm_size = LABEL.mm_to_pixels(22)  # ~176px
        dm_margin = LABEL.mm_to_pixels(1)  # 8px = 1мм отступ

        # Область для DataMatrix справа (с текстом под ним)
        dm_area_width = dm_size + 2 * dm_margin

        # Область для WB слева
        wb_area_width = template_width - dm_area_width
        small_margin = LABEL.mm_to_pixels(1)

        # Обрезаем пустые поля (whitespace) у WB этикетки
        wb_trimmed = self._trim_whitespace(wb_image)

        # Масштабируем WB изображение, сохраняя пропорции
        wb_aspect = wb_trimmed.width / wb_trimmed.height
        max_wb_width = wb_area_width - small_margin
        max_wb_height = template_height - 2 * small_margin

        if wb_aspect > (max_wb_width / max_wb_height):
            new_width = max_wb_width
            new_height = int(new_width / wb_aspect)
        else:
            new_height = max_wb_height
            new_width = int(new_height * wb_aspect)

        wb_resized = wb_trimmed.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS,
        )

        # Позиция WB: прижимаем к левому краю
        wb_x = 0
        wb_y = (template_height - new_height) // 2
        label.paste(wb_resized, (wb_x, wb_y))

        # Масштабируем DataMatrix
        dm_resized = dm_image.resize(
            (dm_size, dm_size),
            Image.Resampling.NEAREST,
        )

        # Позиция DataMatrix: справа, по центру вертикально (с учётом текста снизу)
        dm_x = template_width - dm_size - dm_margin
        # Центрируем: (высота - размер DM - место под текст) / 2
        dm_y = (template_height - dm_size - text_height) // 2
        label.paste(dm_resized, (dm_x, dm_y))

        # Добавляем текст под DataMatrix
        try:
            # Пробуем загрузить шрифт из assets
            import os

            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(current_dir, "..", "assets", "fonts", "arial.ttf")

            font_size = LABEL.mm_to_pixels(2)  # ~16px
            font = ImageFont.truetype(font_path, font_size)
            small_font = ImageFont.truetype(font_path, font_size - 2)  # Увеличен размер
        except OSError:
            try:
                # Fallback на системный arial
                font = ImageFont.truetype("arial.ttf", font_size)
                small_font = ImageFont.truetype("arial.ttf", font_size - 2)
            except OSError:
                # Если нет шрифта — используем встроенный
                font = ImageFont.load_default()
                small_font = font

        # Текст "Честный знак"
        text_y = dm_y + dm_size + 2
        text_center_x = dm_x + dm_size // 2

        # Рисуем "ЧЕСТНЫЙ ЗНАК"
        label_text = "ЧЕСТНЫЙ ЗНАК"
        bbox = draw.textbbox((0, 0), label_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (text_center_x - text_width // 2, text_y),
            label_text,
            fill="black",
            font=small_font,
        )

        # Код (первые 14 символов — GTIN)
        if code and len(code) >= 16:
            gtin = code[2:16]  # Извлекаем GTIN из кода (после 01)
            text_y += font_size - 2
            bbox = draw.textbbox((0, 0), gtin, font=small_font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (text_center_x - text_width // 2, text_y),
                gtin,
                fill="black",
                font=small_font,
            )

        return label

    def _get_template_size(self, template: str) -> tuple[int, int]:
        """Получение размеров шаблона в пикселях."""
        templates = {
            "58x40": (LABEL.mm_to_pixels(58), LABEL.mm_to_pixels(40)),
            "58x30": (LABEL.mm_to_pixels(58), LABEL.mm_to_pixels(30)),
            "58x60": (LABEL.mm_to_pixels(58), LABEL.mm_to_pixels(60)),
        }

        return templates.get(template, templates["58x40"])

    async def _merge_batch_separate(
        self,
        wb_images: list[Image.Image],
        codes: list[str],
        template_width: int,
        template_height: int,
    ) -> list[Image.Image]:
        """
        Генерация раздельных этикеток (WB и DataMatrix отдельно).

        Результат чередуется: WB1, DM1, WB2, DM2, ...
        """
        # Генерируем все DataMatrix заранее
        dm_images: list[Image.Image] = []
        for code in codes:
            try:
                dm = self.dm_generator.generate(code, with_quiet_zone=True)
                dm_images.append(dm.image)
            except Exception:
                # Placeholder для невалидных кодов
                placeholder = Image.new(
                    "RGB", (LABEL.DATAMATRIX_PIXELS, LABEL.DATAMATRIX_PIXELS), "white"
                )
                dm_images.append(placeholder)

        results: list[Image.Image] = []
        total = len(wb_images)

        for i in range(total):
            # 1. Страница с WB штрихкодом
            wb_page = self._create_wb_only_label(
                wb_image=wb_images[i],
                template_width=template_width,
                template_height=template_height,
            )
            results.append(wb_page)

            # 2. Страница с DataMatrix (с надписями и нумерацией)
            dm_page = self._create_dm_only_label(
                dm_image=dm_images[i],
                template_width=template_width,
                template_height=template_height,
                code=codes[i],
                index=i,
                total=total,
            )
            results.append(dm_page)

        return results

    def _create_wb_only_label(
        self,
        wb_image: Image.Image,
        template_width: int,
        template_height: int,
    ) -> Image.Image:
        """
        Создание этикетки только с WB штрихкодом.

        WB размещается по центру с quiet zone.
        """
        label = Image.new("RGB", (template_width, template_height), "white")

        # Масштабируем WB с сохранением пропорций
        wb_aspect = wb_image.width / wb_image.height
        max_width = template_width - 2 * LABEL.QUIET_ZONE_PIXELS
        max_height = template_height - 2 * LABEL.QUIET_ZONE_PIXELS

        if wb_aspect > (max_width / max_height):
            new_width = max_width
            new_height = int(max_width / wb_aspect)
        else:
            new_height = max_height
            new_width = int(max_height * wb_aspect)

        wb_resized = wb_image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS,
        )

        # Центрируем
        x = (template_width - new_width) // 2
        y = (template_height - new_height) // 2

        label.paste(wb_resized, (x, y))
        return label

    def _create_dm_only_label(
        self,
        dm_image: Image.Image,
        template_width: int,
        template_height: int,
        code: str = "",
        index: int = 0,
        total: int = 0,
    ) -> Image.Image:
        """
        Создание этикетки только с DataMatrix.

        DataMatrix размещается по центру с текстом "Честный знак", GTIN и нумерацией.
        """
        from PIL import ImageDraw, ImageFont

        label = Image.new("RGB", (template_width, template_height), "white")
        draw = ImageDraw.Draw(label)

        # Размеры для расчёта компоновки
        text_height = LABEL.mm_to_pixels(8)  # 8мм на текст под DataMatrix

        # Размер DataMatrix
        dm_size = min(
            template_width - 2 * LABEL.QUIET_ZONE_PIXELS,
            template_height - 2 * LABEL.QUIET_ZONE_PIXELS - text_height,
            LABEL.DATAMATRIX_PIXELS + 2 * LABEL.QUIET_ZONE_PIXELS,
        )

        dm_resized = dm_image.resize(
            (dm_size, dm_size),
            Image.Resampling.NEAREST,  # NEAREST для сохранения чёткости
        )

        # Позиция DataMatrix: по центру горизонтально, смещён вверх для текста снизу
        x = (template_width - dm_size) // 2
        y = (template_height - dm_size - text_height) // 2

        label.paste(dm_resized, (x, y))

        # Загрузка шрифта
        try:
            import os

            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(current_dir, "..", "assets", "fonts", "arial.ttf")

            font_size = LABEL.mm_to_pixels(2)  # ~16px
            font = ImageFont.truetype(font_path, font_size)
            small_font = ImageFont.truetype(font_path, font_size - 2)
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", LABEL.mm_to_pixels(2))
                small_font = ImageFont.truetype("arial.ttf", LABEL.mm_to_pixels(2) - 2)
            except OSError:
                font = ImageFont.load_default()
                small_font = font

        # Центр для текста
        text_center_x = template_width // 2
        text_y = y + dm_size + 4

        # Текст "ЧЕСТНЫЙ ЗНАК"
        label_text = "ЧЕСТНЫЙ ЗНАК"
        bbox = draw.textbbox((0, 0), label_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (text_center_x - text_width // 2, text_y),
            label_text,
            fill="black",
            font=small_font,
        )

        # GTIN (первые 14 символов после 01)
        if code and len(code) >= 16:
            gtin = code[2:16]
            text_y += LABEL.mm_to_pixels(2)
            bbox = draw.textbbox((0, 0), gtin, font=small_font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (text_center_x - text_width // 2, text_y),
                gtin,
                fill="black",
                font=small_font,
            )

        # Нумерация "1 из N"
        if total > 0:
            number_text = f"{index + 1} из {total}"
            text_y += LABEL.mm_to_pixels(2)
            bbox = draw.textbbox((0, 0), number_text, font=small_font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (text_center_x - text_width // 2, text_y),
                number_text,
                fill="black",
                font=small_font,
            )

        return label

    def _trim_whitespace(self, image: Image.Image) -> Image.Image:
        """Обрезает белые поля вокруг изображения."""
        from PIL import ImageChops

        # Создаем белую подложку той же модели
        bg = Image.new(image.mode, image.size, (255, 255, 255))
        diff = ImageChops.difference(image, bg)
        # Усиливаем разницу
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()

        if bbox:
            return image.crop(bbox)
        return image
