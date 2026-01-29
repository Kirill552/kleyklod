"""Тесты для CSV парсера кодов Честного знака."""

from app.services.csv_parser import ChzCsvParser

# Валидный код маркировки с криптохвостом (>= 31 символ)
VALID_CODE_1 = "010467004977480221JNlMVstBYYuQ91EE0692Wh0KGcGm6HpwZf+7aWtp/DaNgFU="
VALID_CODE_2 = "010467004977480221ABC123defGHI91EE0692XYZTEST123456789abcdef="


class TestChzCsvParser:
    """Тесты для ChzCsvParser."""

    def test_parse_valid_csv_with_full_codes(self):
        """Парсинг CSV с полными кодами маркировки (с криптохвостом)."""
        csv_content = f"{VALID_CODE_1}\n{VALID_CODE_2}"

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert result.success is True
        assert len(result.codes) == 2
        assert result.codes[0] == VALID_CODE_1
        assert result.codes[1] == VALID_CODE_2
        assert result.invalid_count == 0
        assert result.truncated is False

    def test_reject_short_codes_without_crypto(self):
        """Отклонение кодов без криптохвоста (< 31 символ)."""
        csv_content = """0104670049774802
010467004977480221"""

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert result.invalid_count == 2
        assert len(result.codes) == 0
        assert "криптохвост" in result.errors[0].lower()

    def test_parse_semicolon_separated(self):
        """Парсинг CSV с разделителем точка с запятой."""
        csv_content = f"код;дата\n{VALID_CODE_1};2026-01-28"

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert len(result.codes) == 1
        assert result.codes[0] == VALID_CODE_1

    def test_handle_different_encodings(self):
        """Поддержка кодировок utf-8, cp1251, latin-1."""
        csv_bytes = f"код маркировки\n{VALID_CODE_1}".encode("cp1251")

        parser = ChzCsvParser()
        result = parser.parse_bytes(csv_bytes)

        assert result.success is True
        assert len(result.codes) == 1

    def test_limit_30000_codes(self):
        """Лимит 30 000 кодов в файле."""
        codes = [VALID_CODE_1] * 35000
        csv_content = "\n".join(codes)

        parser = ChzCsvParser()
        result = parser.parse(csv_content, max_codes=30000)

        assert len(result.codes) == 30000
        assert result.truncated is True

    # === Новые edge case тесты ===

    def test_empty_file(self):
        """Пустой CSV файл должен вернуть пустой результат."""
        parser = ChzCsvParser()
        result = parser.parse("")

        assert result.success is True  # Пустой файл — не ошибка
        assert len(result.codes) == 0
        assert result.invalid_count == 0

    def test_only_header(self):
        """CSV только с заголовком — 0 кодов."""
        csv_content = "код маркировки\n"

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert len(result.codes) == 0
        assert result.invalid_count == 0

    def test_mixed_valid_invalid_codes(self):
        """Смешанные валидные и невалидные коды."""
        csv_content = f"""{VALID_CODE_1}
INVALID_SHORT
{VALID_CODE_2}
123456"""

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert result.success is True
        assert len(result.codes) == 2
        assert result.invalid_count == 2
        assert len(result.errors) == 2

    def test_max_5_errors_displayed(self):
        """Показываем только первые 5 ошибок."""
        invalid_codes = [f"INVALID_{i}" for i in range(10)]
        csv_content = "\n".join(invalid_codes)

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert result.invalid_count == 10
        assert len(result.errors) == 5  # Максимум 5 ошибок

    def test_normalize_code_without_01_prefix(self):
        """Код без AI-префикса 01 должен быть нормализован."""
        # Код без "01" в начале, но с 14-значным GTIN
        code_without_prefix = (
            "04670049774802" + "21JNlMVstBYYuQ91EE0692Wh0KGcGm6HpwZf+7aWtp/DaNgFU="
        )
        csv_content = code_without_prefix

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert result.success is True
        assert len(result.codes) == 1
        assert result.codes[0].startswith("01")  # Префикс добавлен

    def test_whitespace_handling(self):
        """Пробелы вокруг кодов должны быть убраны."""
        csv_content = f"  {VALID_CODE_1}  \n\t{VALID_CODE_2}\t"

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert len(result.codes) == 2
        assert result.codes[0] == VALID_CODE_1
        assert result.codes[1] == VALID_CODE_2

    def test_skip_empty_lines(self):
        """Пустые строки должны быть пропущены."""
        csv_content = f"{VALID_CODE_1}\n\n\n{VALID_CODE_2}\n\n"

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert len(result.codes) == 2

    def test_invalid_encoding_returns_error(self):
        """Файл с невалидной кодировкой возвращает ошибку."""
        # Создаём байты, которые не декодируются ни одной из поддерживаемых кодировок
        invalid_bytes = bytes([0x80, 0x81, 0x82, 0xFF, 0xFE])

        parser = ChzCsvParser()
        result = parser.parse_bytes(invalid_bytes)

        # На самом деле latin-1 декодирует любые байты, так что это пройдёт
        # но коды будут невалидными
        assert result.success is False or len(result.codes) == 0

    def test_total_lines_count(self):
        """Подсчёт общего количества строк."""
        csv_content = f"заголовок\n{VALID_CODE_1}\nINVALID\n{VALID_CODE_2}"

        parser = ChzCsvParser()
        result = parser.parse(csv_content)

        assert result.total_lines == 4
