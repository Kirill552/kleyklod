"""
Парсер Excel файлов с баркодами Wildberries.

Извлекает баркоды и артикулы из Excel-выгрузок WB.
"""

from dataclasses import dataclass
from io import BytesIO

import pandas as pd


@dataclass
class ExcelBarcodeItem:
    """Элемент из Excel с баркодом."""

    barcode: str
    article: str | None = None
    size: str | None = None
    color: str | None = None
    name: str | None = None
    country: str | None = None
    composition: str | None = None
    row_number: int = 0  # Номер строки в Excel (для отладки)


@dataclass
class ExcelBarcodeData:
    """Результат парсинга Excel файла."""

    items: list[ExcelBarcodeItem]
    count: int
    filename: str
    has_articles: bool = False
    has_sizes: bool = False

    @property
    def barcodes(self) -> list[str]:
        """Список баркодов для генерации."""
        return [item.barcode for item in self.items]


class ExcelBarcodeParser:
    """
    Парсер Excel файлов с баркодами WB.

    Автоматически определяет колонку с баркодами по названию.
    Поддерживает форматы: xlsx, xls.
    """

    # Варианты названий колонки с баркодами
    BARCODE_COLUMNS = [
        "баркод",
        "barcode",
        "штрихкод",
        "шк",
        "ean",
        "ean13",
        "ean-13",
        "код",
        "bar_code",
        "bar-code",
    ]

    # Варианты названий колонки с артикулом
    ARTICLE_COLUMNS = [
        "артикул",
        "article",
        "арт",
        "sku",
        "артикул продавца",
        "артикул поставщика",
        "vendor_code",
        "vendorcode",
    ]

    # Варианты названий колонки с размером
    SIZE_COLUMNS = [
        "размер",
        "size",
        "размер товара",
        "размер (рус.)",
        "размер рус",
        "tech_size",
        "techsize",
    ]

    # Варианты названий колонки с цветом
    COLOR_COLUMNS = [
        "цвет",
        "color",
        "цвет товара",
        "colour",
    ]

    # Варианты названий колонки с названием
    NAME_COLUMNS = [
        "название",
        "name",
        "наименование",
        "товар",
        "наименование товара",
        "title",
    ]

    # Варианты названий колонки со страной
    COUNTRY_COLUMNS = [
        "страна",
        "country",
        "страна производства",
        "страна производитель",
        "производство",
    ]

    # Варианты названий колонки с составом
    COMPOSITION_COLUMNS = [
        "состав",
        "composition",
        "материал",
        "material",
        "ткань",
        "fabric",
    ]

    def get_columns_info(self, excel_bytes: bytes, filename: str) -> dict:
        """
        Анализирует Excel и возвращает информацию о колонках.

        Используется для human-in-the-loop workflow: пользователь может
        подтвердить или выбрать другую колонку с баркодами.

        Args:
            excel_bytes: Содержимое Excel файла
            filename: Имя файла (для определения формата)

        Returns:
            Словарь с информацией о колонках:
            - detected_column: Автоопределённая колонка с баркодами
            - all_columns: Список всех колонок (оригинальные названия)
            - barcode_candidates: Колонки похожие на баркоды
            - total_rows: Количество строк с данными
            - sample_items: Примеры данных (первые 5 строк)

        Raises:
            ValueError: Если файл невалидный
        """
        engine = self._get_engine(filename)

        try:
            df = pd.read_excel(
                BytesIO(excel_bytes),
                engine=engine,
                dtype=str,
            )
        except Exception as e:
            raise ValueError(f"Не удалось прочитать Excel файл: {str(e)}")

        if df.empty:
            raise ValueError("Excel файл пустой")

        # Сохраняем оригинальные названия колонок
        original_columns = [str(col).strip() for col in df.columns]

        # Создаём маппинг: нижний регистр -> оригинал
        columns_mapping = {str(col).lower().strip(): str(col).strip() for col in df.columns}

        # Приводим названия колонок к нижнему регистру для поиска
        df.columns = [str(col).lower().strip() for col in df.columns]

        # Ищем колонку с баркодами
        barcode_col = self._find_column(df.columns, self.BARCODE_COLUMNS)
        detected_column = columns_mapping.get(barcode_col) if barcode_col else None

        # Ищем все колонки, похожие на баркоды
        barcode_candidates = []
        for col_lower, col_original in columns_mapping.items():
            for candidate in self.BARCODE_COLUMNS:
                if candidate in col_lower:
                    if col_original not in barcode_candidates:
                        barcode_candidates.append(col_original)
                    break

        # Ищем дополнительные колонки
        article_col = self._find_column(df.columns, self.ARTICLE_COLUMNS)
        size_col = self._find_column(df.columns, self.SIZE_COLUMNS)
        color_col = self._find_column(df.columns, self.COLOR_COLUMNS)
        name_col = self._find_column(df.columns, self.NAME_COLUMNS)
        country_col = self._find_column(df.columns, self.COUNTRY_COLUMNS)
        composition_col = self._find_column(df.columns, self.COMPOSITION_COLUMNS)

        # Считаем строки с данными (непустые строки в колонке баркодов или первой колонке)
        check_col = barcode_col if barcode_col else df.columns[0]
        total_rows = df[check_col].dropna().count()

        # Собираем примеры данных (первые 5 строк)
        sample_items = []
        sample_count = 0

        for idx, row in df.iterrows():
            if sample_count >= 5:
                break

            # Получаем баркод из автоопределённой колонки или первой колонки
            barcode_raw = row.get(barcode_col) if barcode_col else row.get(df.columns[0])

            # Пропускаем пустые строки
            if pd.isna(barcode_raw) or not str(barcode_raw).strip():
                continue

            barcode_value = self._clean_barcode(str(barcode_raw))

            # Пропускаем невалидные баркоды
            if not barcode_value or len(barcode_value) < 8:
                continue

            sample_items.append(
                {
                    "barcode": barcode_value,
                    "article": self._get_str_value(row, article_col),
                    "size": self._get_str_value(row, size_col),
                    "color": self._get_str_value(row, color_col),
                    "name": self._get_str_value(row, name_col),
                    "country": self._get_str_value(row, country_col),
                    "composition": self._get_str_value(row, composition_col),
                    "row_number": int(idx) + 2,  # +2: Excel начинается с 1 + заголовок
                }
            )
            sample_count += 1

        return {
            "detected_column": detected_column,
            "all_columns": original_columns,
            "barcode_candidates": barcode_candidates,
            "total_rows": int(total_rows),
            "sample_items": sample_items,
        }

    def parse(
        self,
        excel_bytes: bytes,
        filename: str = "barcodes.xlsx",
        column_name: str | None = None,
    ) -> ExcelBarcodeData:
        """
        Парсит Excel файл с баркодами.

        Args:
            excel_bytes: Содержимое Excel файла
            filename: Имя файла (для определения формата)
            column_name: Название колонки с баркодами (если указано — использовать эту колонку,
                        иначе автоопределение)

        Returns:
            ExcelBarcodeData с извлечёнными данными

        Raises:
            ValueError: Если файл невалидный или не найдена колонка с баркодами
        """
        # Определяем движок по расширению
        engine = self._get_engine(filename)

        try:
            df = pd.read_excel(
                BytesIO(excel_bytes),
                engine=engine,
                dtype=str,  # Читаем всё как строки (важно для баркодов!)
            )
        except Exception as e:
            raise ValueError(f"Не удалось прочитать Excel файл: {str(e)}")

        if df.empty:
            raise ValueError("Excel файл пустой")

        # Сохраняем оригинальные названия колонок для маппинга
        original_to_lower = {str(col).strip(): str(col).lower().strip() for col in df.columns}

        # Приводим названия колонок к нижнему регистру
        df.columns = [str(col).lower().strip() for col in df.columns]

        # Определяем колонку с баркодами
        barcode_col: str | None = None

        if column_name:
            # Пользователь указал конкретную колонку
            column_name_lower = column_name.lower().strip()
            if column_name_lower in df.columns:
                barcode_col = column_name_lower
            elif column_name in original_to_lower:
                barcode_col = original_to_lower[column_name]

            if not barcode_col:
                raise ValueError(
                    f"Колонка '{column_name}' не найдена в Excel файле. "
                    f"Доступные колонки: {', '.join(original_to_lower.keys())}"
                )
        else:
            # Автоопределение колонки с баркодами
            barcode_col = self._find_column(df.columns, self.BARCODE_COLUMNS)
            if not barcode_col:
                raise ValueError(
                    f"Не найдена колонка с баркодами. Ожидаются: {', '.join(self.BARCODE_COLUMNS[:5])}"
                )

        # Ищем дополнительные колонки (опционально)
        article_col = self._find_column(df.columns, self.ARTICLE_COLUMNS)
        size_col = self._find_column(df.columns, self.SIZE_COLUMNS)
        color_col = self._find_column(df.columns, self.COLOR_COLUMNS)
        name_col = self._find_column(df.columns, self.NAME_COLUMNS)
        country_col = self._find_column(df.columns, self.COUNTRY_COLUMNS)
        composition_col = self._find_column(df.columns, self.COMPOSITION_COLUMNS)

        # Извлекаем данные
        items: list[ExcelBarcodeItem] = []

        for idx, row in df.iterrows():
            # Получаем баркод
            barcode_raw = row.get(barcode_col)

            # Пропускаем пустые строки
            if pd.isna(barcode_raw) or not str(barcode_raw).strip():
                continue

            # Обрабатываем баркод
            barcode = self._clean_barcode(str(barcode_raw))

            # Пропускаем невалидные баркоды
            if not barcode or len(barcode) < 8:
                continue

            # Создаём элемент
            item = ExcelBarcodeItem(
                barcode=barcode,
                article=self._get_str_value(row, article_col),
                size=self._get_str_value(row, size_col),
                color=self._get_str_value(row, color_col),
                name=self._get_str_value(row, name_col),
                country=self._get_str_value(row, country_col),
                composition=self._get_str_value(row, composition_col),
                row_number=int(idx) + 2,  # +2 т.к. Excel начинается с 1 + заголовок
            )
            items.append(item)

        if not items:
            raise ValueError("В Excel файле не найдено валидных баркодов")

        return ExcelBarcodeData(
            items=items,
            count=len(items),
            filename=filename,
            has_articles=article_col is not None,
            has_sizes=size_col is not None,
        )

    def _get_engine(self, filename: str) -> str:
        """Определение движка pandas по расширению файла."""
        filename_lower = filename.lower()

        if filename_lower.endswith(".xlsx"):
            return "openpyxl"
        elif filename_lower.endswith(".xls"):
            return "xlrd"
        else:
            # По умолчанию пробуем openpyxl
            return "openpyxl"

    def _find_column(
        self,
        columns: pd.Index,
        candidates: list[str],
    ) -> str | None:
        """Поиск колонки по списку возможных названий."""
        columns_list = list(columns)

        for candidate in candidates:
            # Точное совпадение
            if candidate in columns_list:
                return candidate

            # Частичное совпадение (колонка содержит искомое слово)
            for col in columns_list:
                if candidate in col:
                    return col

        return None

    def _clean_barcode(self, value: str) -> str:
        """
        Очистка баркода от лишних символов.

        Обрабатывает:
        - Float из Excel (4.601234567890e+12 -> 4601234567890)
        - Пробелы и тире
        - Текстовые префиксы
        """
        import contextlib

        value = value.strip()

        # Если это float в научной нотации (например, из Excel)
        if "e+" in value.lower() or "e-" in value.lower():
            with contextlib.suppress(ValueError):
                # Конвертируем в целое число
                value = str(int(float(value)))

        # Если это float без научной нотации (например, "4601234567890.0")
        if "." in value:
            with contextlib.suppress(ValueError):
                # Пробуем убрать десятичную часть
                float_val = float(value)
                if float_val == int(float_val):
                    value = str(int(float_val))

        # Убираем лишние символы
        value = value.replace(" ", "").replace("-", "").replace("\n", "")

        # Оставляем только цифры
        return "".join(c for c in value if c.isdigit())

    def _get_str_value(self, row: pd.Series, column: str | None) -> str | None:
        """Получение строкового значения из ячейки."""
        if column is None:
            return None

        value = row.get(column)
        if pd.isna(value) or not str(value).strip():
            return None

        return str(value).strip()
