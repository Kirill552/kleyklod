"""Парсер CSV файлов с кодами маркировки Честного знака."""

import csv
import io
import re
from dataclasses import dataclass, field

# Минимальная длина кода с криптохвостом (AI + GTIN + Serial + Crypto)
MIN_CODE_LENGTH = 31

# Паттерн кода маркировки: начинается с 01 (AI для GTIN) и содержит буквы/цифры/спецсимволы
CODE_PATTERN = re.compile(r"^01\d{14}[\w\d+/=]+$")


@dataclass
class ChzParseResult:
    """Результат парсинга CSV."""

    success: bool
    codes: list[str] = field(default_factory=list)
    invalid_count: int = 0
    errors: list[str] = field(default_factory=list)
    truncated: bool = False
    total_lines: int = 0


class ChzCsvParser:
    """Парсер CSV с кодами маркировки ЧЗ."""

    ENCODINGS = ["utf-8", "cp1251", "latin-1"]

    def parse(self, content: str, max_codes: int = 30000) -> ChzParseResult:
        """Парсинг строки CSV."""
        return self._parse_content(content, max_codes)

    def parse_bytes(self, data: bytes, max_codes: int = 30000) -> ChzParseResult:
        """Парсинг байтов с автоопределением кодировки."""
        content = None
        for encoding in self.ENCODINGS:
            try:
                content = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            return ChzParseResult(success=False, errors=["Не удалось определить кодировку файла"])

        return self._parse_content(content, max_codes)

    def _parse_content(self, content: str, max_codes: int) -> ChzParseResult:
        """Основная логика парсинга."""
        codes: list[str] = []
        errors: list[str] = []
        invalid_count = 0
        total_lines = 0

        # Определяем разделитель
        delimiter = ";" if ";" in content.split("\n")[0] else ","

        reader = csv.reader(io.StringIO(content), delimiter=delimiter)

        for row_num, row in enumerate(reader, 1):
            total_lines += 1

            # Пропускаем заголовок если похож на заголовок
            if row_num == 1 and any(
                h.lower() in ["код", "code", "маркировка", "код маркировки"] for h in row
            ):
                continue

            for cell in row:
                cell = cell.strip()
                if not cell:
                    continue

                # Проверка валидности кода
                if len(cell) < MIN_CODE_LENGTH:
                    invalid_count += 1
                    if len(errors) < 5:
                        errors.append(
                            f"Строка {row_num}: код '{cell[:20]}...' слишком короткий (нет криптохвоста)"
                        )
                    continue

                # Нормализация: добавляем 01 если отсутствует
                normalized = self._normalize_code(cell)

                if not CODE_PATTERN.match(normalized):
                    invalid_count += 1
                    if len(errors) < 5:
                        errors.append(f"Строка {row_num}: неверный формат кода")
                    continue

                codes.append(normalized)

                if len(codes) >= max_codes:
                    return ChzParseResult(
                        success=True,
                        codes=codes,
                        invalid_count=invalid_count,
                        errors=errors,
                        truncated=True,
                        total_lines=total_lines,
                    )

        return ChzParseResult(
            success=len(codes) > 0 or invalid_count == 0,
            codes=codes,
            invalid_count=invalid_count,
            errors=errors,
            truncated=False,
            total_lines=total_lines,
        )

    def _normalize_code(self, code: str) -> str:
        """Добавляет AI префикс 01 если отсутствует."""
        # Проверяем, похож ли на GTIN (14 цифр в начале) без AI префикса
        if not code.startswith("01") and len(code) >= 14 and code[:14].isdigit():
            return "01" + code
        return code
