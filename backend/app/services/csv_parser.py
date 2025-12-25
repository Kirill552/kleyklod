"""
Парсер CSV/Excel файлов с кодами Честного Знака.

Извлекает коды DataMatrix из различных форматов.
"""

import csv
import io
import re
from dataclasses import dataclass


@dataclass
class ParsedCodes:
    """Результат парсинга кодов."""

    codes: list[str]
    count: int
    duplicates_removed: int
    invalid_removed: int


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
    GS1_PATTERN = re.compile(
        r"^\(01\)\d{14}\(21\)[\w\W]+$"
    )

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
            raw_codes = self._parse_excel(file_bytes)
        else:
            raw_codes = self._parse_csv(file_bytes)

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
        )

    def _parse_csv(self, file_bytes: bytes) -> list[str]:
        """Парсинг CSV файла."""
        # Пробуем декодировать с разными кодировками
        content = None
        for encoding in ["utf-8", "cp1251", "latin-1"]:
            try:
                content = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError("Не удалось определить кодировку файла")

        # Определяем разделитель
        delimiter = self._detect_delimiter(content)

        # Парсим CSV
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return []

        # Определяем колонку с кодами
        code_column = self._detect_code_column(rows)

        # Извлекаем коды
        codes: list[str] = []
        for row in rows:
            if len(row) > code_column:
                codes.append(row[code_column])

        return codes

    def _parse_excel(self, file_bytes: bytes) -> list[str]:
        """
        Парсинг Excel файла.

        Использует openpyxl для xlsx или xlrd для xls.
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
                return []

            # Определяем колонку с кодами
            code_column = self._detect_code_column_from_values(rows)

            codes: list[str] = []
            for row in rows:
                if len(row) > code_column and row[code_column]:
                    codes.append(str(row[code_column]))

            return codes

        except ImportError:
            raise ValueError(
                "Для обработки Excel файлов требуется установить openpyxl: "
                "pip install openpyxl"
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
        """Очистка кода от лишних символов."""
        if not code:
            return ""

        # Убираем пробелы по краям
        cleaned = code.strip()

        # Убираем кавычки
        cleaned = cleaned.strip('"\'')

        # Убираем BOM и невидимые символы
        cleaned = cleaned.replace("\ufeff", "").replace("\u200b", "")

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
        if code.startswith("01") and len(code) >= 31:
            return True

        return False
