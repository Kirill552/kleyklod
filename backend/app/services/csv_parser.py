"""
Парсер CSV/Excel файлов с кодами Честного Знака.

Извлекает коды DataMatrix из различных форматов.
"""

import csv
import io
import logging
import re
from dataclasses import dataclass

import chardet

logger = logging.getLogger(__name__)

# Кириллические символы, визуально похожие на латинские
# Пользователи часто копируют коды с русскими буквами вместо английских
CYRILLIC_TO_LATIN = {
    "А": "A",
    "В": "B",
    "С": "C",
    "Е": "E",
    "Н": "H",
    "К": "K",
    "М": "M",
    "О": "O",
    "Р": "P",
    "Т": "T",
    "У": "Y",
    "Х": "X",
    # строчные
    "а": "a",
    "в": "b",
    "с": "c",
    "е": "e",
    "н": "h",
    "к": "k",
    "м": "m",
    "о": "o",
    "р": "p",
    "т": "t",
    "у": "y",
    "х": "x",
}


@dataclass
class ParsedCodes:
    """Результат парсинга кодов."""

    codes: list[str]
    count: int
    duplicates_removed: int
    invalid_removed: int
    headers_skipped: int = 0  # Количество пропущенных заголовков


class CSVParser:
    """
    Парсер CSV/Excel файлов с кодами маркировки.

    Поддерживает:
    - CSV с разными разделителями (;, ,, табуляция)
    - Автоопределение колонки с кодами
    - Удаление дубликатов
    - Валидация формата кодов
    """

    # Regex для валидации кода DataMatrix ЧЗ
    # Формат: 01 + GTIN (14 цифр) + 21 + серийный номер + разделитель + крипто
    DATAMATRIX_PATTERN = re.compile(
        r"^01\d{14}21[\w\W]{6,}$"  # Минимальный паттерн
    )

    # Альтернативный паттерн для кодов с GS1 разделителями
    GS1_PATTERN = re.compile(r"^\(01\)\d{14}\(21\)[\w\W]+$")

    def parse(
        self,
        file_bytes: bytes,
        filename: str = "codes.csv",
        remove_duplicates: bool = True,
    ) -> ParsedCodes:
        """
        Парсинг файла с кодами.

        Args:
            file_bytes: Содержимое файла
            filename: Имя файла (для определения формата)
            remove_duplicates: Удалять дубликаты

        Returns:
            ParsedCodes со списком кодов

        Raises:
            ValueError: Если файл не содержит валидных кодов
        """
        # Определяем формат по расширению
        extension = filename.lower().split(".")[-1] if "." in filename else "csv"

        if extension in ["xlsx", "xls"]:
            raw_codes, headers_skipped = self._parse_excel(file_bytes)
        else:
            raw_codes, headers_skipped = self._parse_csv(file_bytes)

        if not raw_codes:
            raise ValueError("Файл не содержит данных")

        # Валидация и очистка кодов
        valid_codes: list[str] = []
        invalid_count = 0

        for code in raw_codes:
            cleaned = self._clean_code(code)
            if cleaned and self._validate_code(cleaned):
                valid_codes.append(cleaned)
            elif cleaned:  # Код есть, но невалидный
                invalid_count += 1

        if not valid_codes:
            raise ValueError(
                "Не найдено валидных кодов DataMatrix. "
                "Убедитесь, что файл содержит коды Честного Знака."
            )

        # Удаление дубликатов
        duplicates_count = 0
        if remove_duplicates:
            unique_codes = list(dict.fromkeys(valid_codes))  # Сохраняем порядок
            duplicates_count = len(valid_codes) - len(unique_codes)
            valid_codes = unique_codes

        return ParsedCodes(
            codes=valid_codes,
            count=len(valid_codes),
            duplicates_removed=duplicates_count,
            invalid_removed=invalid_count,
            headers_skipped=headers_skipped,
        )

    def _parse_csv(self, file_bytes: bytes) -> tuple[list[str], int]:
        """
        Парсинг CSV файла.

        Returns:
            Tuple[list[str], int] — список кодов и количество пропущенных заголовков
        """
        # Автоопределение кодировки через chardet
        detected = chardet.detect(file_bytes)
        encoding = detected.get("encoding") or "utf-8"
        confidence = detected.get("confidence", 0)

        logger.info(f"Обнаружена кодировка: {encoding} (уверенность: {confidence:.0%})")

        try:
            content = file_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Fallback на cp1251 (частая кодировка экспортов из 1С)
            logger.warning(f"Не удалось декодировать как {encoding}, пробую cp1251")
            try:
                content = file_bytes.decode("cp1251")
            except UnicodeDecodeError:
                raise ValueError("Не удалось определить кодировку файла")

        # Определяем разделитель
        delimiter = self._detect_delimiter(content)

        # Парсим CSV
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return [], 0

        # Определяем колонку с кодами
        code_column = self._detect_code_column(rows)

        # Извлекаем коды, пропуская заголовки
        codes: list[str] = []
        headers_skipped = 0

        for row_idx, row in enumerate(rows):
            # Проверяем, является ли строка заголовком
            if self._is_header_row(row, row_idx):
                header_text = row[0][:50] if row else "(пустая)"
                logger.info(f"Пропущена строка {row_idx + 1} (заголовок): {header_text}...")
                headers_skipped += 1
                continue

            if len(row) > code_column:
                codes.append(row[code_column])

        return codes, headers_skipped

    def _parse_excel(self, file_bytes: bytes) -> tuple[list[str], int]:
        """
        Парсинг Excel файла.

        Использует openpyxl для xlsx или xlrd для xls.

        Returns:
            Tuple[list[str], int] — список кодов и количество пропущенных заголовков
        """
        try:
            import openpyxl

            workbook = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
            sheet = workbook.active

            if sheet is None:
                raise ValueError("Excel файл не содержит листов")

            # Собираем все значения из первого столбца или ищем колонку с кодами
            rows = list(sheet.iter_rows(values_only=True))
            workbook.close()

            if not rows:
                return [], 0

            # Определяем колонку с кодами
            code_column = self._detect_code_column_from_values(rows)

            # Извлекаем коды, пропуская заголовки
            codes: list[str] = []
            headers_skipped = 0

            for row_idx, row in enumerate(rows):
                # Проверяем, является ли строка заголовком
                if self._is_header_row_from_values(row, row_idx):
                    header_text = str(row[0])[:50] if row and row[0] else "(пустая)"
                    logger.info(f"Пропущена строка {row_idx + 1} (заголовок): {header_text}...")
                    headers_skipped += 1
                    continue

                if len(row) > code_column and row[code_column]:
                    codes.append(str(row[code_column]))

            return codes, headers_skipped

        except ImportError:
            raise ValueError(
                "Для обработки Excel файлов требуется установить openpyxl: pip install openpyxl"
            )
        except Exception as e:
            raise ValueError(f"Ошибка при чтении Excel файла: {str(e)}")

    def _detect_delimiter(self, content: str) -> str:
        """Автоопределение разделителя CSV."""
        # Берём первые несколько строк для анализа
        sample = content[:2000]

        # Считаем встречаемость потенциальных разделителей
        delimiters = {
            ";": sample.count(";"),
            ",": sample.count(","),
            "\t": sample.count("\t"),
        }

        # Выбираем самый частый
        return max(delimiters, key=delimiters.get)

    def _detect_code_column(self, rows: list[list[str]]) -> int:
        """Определение колонки с кодами DataMatrix."""
        if not rows:
            return 0

        # Проверяем каждую колонку на наличие кодов
        max_codes = 0
        best_column = 0

        # Анализируем первые 10 строк
        sample_rows = rows[:10]

        for col_idx in range(len(rows[0]) if rows else 0):
            code_count = 0
            for row in sample_rows:
                if len(row) > col_idx:
                    cleaned = self._clean_code(row[col_idx])
                    if cleaned and self._validate_code(cleaned):
                        code_count += 1

            if code_count > max_codes:
                max_codes = code_count
                best_column = col_idx

        return best_column

    def _detect_code_column_from_values(self, rows: list[tuple]) -> int:
        """Определение колонки с кодами для Excel."""
        if not rows:
            return 0

        max_codes = 0
        best_column = 0

        sample_rows = rows[:10]

        for col_idx in range(len(rows[0]) if rows else 0):
            code_count = 0
            for row in sample_rows:
                if len(row) > col_idx and row[col_idx]:
                    cleaned = self._clean_code(str(row[col_idx]))
                    if cleaned and self._validate_code(cleaned):
                        code_count += 1

            if code_count > max_codes:
                max_codes = code_count
                best_column = col_idx

        return best_column

    def _clean_code(self, code: str) -> str:
        """Очистка кода от лишних символов и замена кириллицы на латиницу."""
        if not code:
            return ""

        # Убираем пробелы по краям
        cleaned = code.strip()

        # Убираем кавычки
        cleaned = cleaned.strip("\"'")

        # Убираем BOM и невидимые символы
        cleaned = cleaned.replace("\ufeff", "").replace("\u200b", "")

        # Заменяем кириллические символы на латинские
        # (частая ошибка при копировании кодов)
        for cyr, lat in CYRILLIC_TO_LATIN.items():
            cleaned = cleaned.replace(cyr, lat)

        return cleaned

    def _validate_code(self, code: str) -> bool:
        """Проверка валидности кода DataMatrix ЧЗ."""
        if not code or len(code) < 20:
            return False

        # Проверяем основной паттерн
        if self.DATAMATRIX_PATTERN.match(code):
            return True

        # Проверяем GS1 паттерн
        if self.GS1_PATTERN.match(code):
            return True

        # Проверяем, начинается ли с 01 (GTIN)
        return bool(code.startswith("01") and len(code) >= 31)

    def _is_header_row(self, row: list[str], row_index: int) -> bool:
        """
        Определяет, является ли строка заголовком.

        Эвристики:
        1. Первые 3 строки с ключевыми словами заголовков — пропускаем
        2. Строка не содержит цифр (коды ЧЗ всегда содержат цифры)
        3. Первая ячейка слишком короткая для кода ЧЗ (< 20 символов)
        4. Первая ячейка не начинается с "01" (GTIN prefix)
        """
        if not row:
            return True  # Пустая строка — пропускаем

        # Объединяем все ячейки в текст для анализа
        text = " ".join(str(cell).lower().strip() for cell in row if cell)

        # Первая ячейка — основной кандидат на код
        first_cell = str(row[0]).strip() if row else ""

        # Ключевые слова, характерные для заголовков
        header_keywords = [
            "код",
            "маркировк",
            "баркод",
            "штрихкод",
            "артикул",
            "наименование",
            "название",
            "товар",
            "честн",
            "знак",
            "crpt",
            "datamatrix",
            "серийный",
            "номер",
            "gtin",
            "column",
            "поле",
        ]

        # 1. Первые 3 строки с ключевыми словами — скорее всего заголовок
        if row_index < 3 and any(kw in text for kw in header_keywords):
            return True

        # 2. Строка без цифр — не может быть кодом ЧЗ
        if not any(char.isdigit() for char in text):
            return True

        # 3. Первая ячейка слишком короткая для кода ЧЗ (минимум 20 символов)
        if len(first_cell) < 20:
            return True

        # 4. Код ЧЗ должен начинаться с "01" (GTIN Application Identifier)
        # Если первая ячейка не начинается с 01 — это не код
        return not first_cell.startswith("01")

    def _is_header_row_from_values(self, row: tuple, row_index: int) -> bool:
        """Версия _is_header_row для Excel (tuple вместо list)."""
        if not row:
            return True

        # Преобразуем tuple в list[str]
        str_row = [str(cell) if cell is not None else "" for cell in row]
        return self._is_header_row(str_row, row_index)
