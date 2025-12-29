"""
Дружелюбные сообщения об ошибках.

Вместо технических сообщений пользователь видит понятные подсказки.
"""


class FriendlyError:
    """Человекопонятная ошибка с подсказкой."""

    def __init__(self, message: str, hint: str | None = None, details: str | None = None):
        self.message = message
        self.hint = hint
        self.details = details  # Техническая инфа для поддержки

    def to_dict(self) -> dict:
        result = {"message": self.message}
        if self.hint:
            result["hint"] = self.hint
        if self.details:
            result["details"] = self.details
        return result


# === Ошибки формата файлов ===

INVALID_FILE_FORMAT = FriendlyError(
    message="Упс! Нужен PDF или Excel файл",
    hint="Проверьте, что скачали файл из WB, а не скриншот. Формат: .pdf, .xlsx, .xls",
)

EMPTY_FILE = FriendlyError(
    message="Файл пустой",
    hint="Попробуйте скачать заново из личного кабинета Wildberries",
)

CORRUPTED_FILE = FriendlyError(
    message="Файл повреждён или имеет неверный формат",
    hint="Попробуйте скачать файл заново. Если проблема повторяется, обратитесь в поддержку",
)


# === Ошибки кодов ЧЗ ===

NO_VALID_CODES = FriendlyError(
    message="Не найдено валидных кодов Честного Знака",
    hint="Убедитесь, что файл содержит коды маркировки из crpt.ru. Коды начинаются с 01 и содержат 31+ символ",
)

INVALID_CODE = FriendlyError(
    message="Код «{code}» не похож на код Честного Знака",
    hint="Коды ЧЗ начинаются с 01, затем идут 14 цифр GTIN, потом 21 и серийный номер",
)


# === Ошибки соответствия количества ===


def count_mismatch_error(wb_count: int, code_count: int) -> FriendlyError:
    """Ошибка несоответствия количества."""
    return FriendlyError(
        message=f"Количество не сходится: {wb_count} штрихкодов и {code_count} кодов ЧЗ",
        hint="Проверьте, все ли коды маркировки на месте. Количество должно совпадать",
        details=f"wb_count={wb_count}, code_count={code_count}",
    )


# === Ошибки штрихкодов ===

BARCODE_NOT_FOUND = FriendlyError(
    message="Не найдены штрихкоды в Excel",
    hint="Убедитесь, что в файле есть колонка с баркодами (13 цифр EAN-13)",
)

INVALID_BARCODE = FriendlyError(
    message="Штрихкод «{barcode}» имеет неверный формат",
    hint="Штрихкоды WB обычно содержат 12-13 цифр (EAN-13)",
)


# === Ошибки лимитов ===

DAILY_LIMIT_REACHED = FriendlyError(
    message="Дневной лимит исчерпан",
    hint="Подождите до завтра или оформите подписку для увеличения лимита",
)

TRIAL_EXPIRED = FriendlyError(
    message="Пробный период закончился",
    hint="Оформите подписку PRO или ENTERPRISE для продолжения работы",
)


# === Ошибки авторизации ===

UNAUTHORIZED = FriendlyError(
    message="Необходимо войти в систему",
    hint="Авторизуйтесь через Telegram для доступа к сервису",
)

FORBIDDEN = FriendlyError(
    message="Нет доступа к этой функции",
    hint="Эта функция доступна только для подписчиков PRO или ENTERPRISE",
)


# === Серверные ошибки ===

INTERNAL_ERROR = FriendlyError(
    message="Что-то пошло не так",
    hint="Попробуйте ещё раз. Если ошибка повторяется, обратитесь в поддержку",
)


# === Утилиты ===


def get_friendly_error(error_key: str, **kwargs) -> FriendlyError:
    """
    Получить дружелюбную ошибку по ключу.

    Args:
        error_key: Ключ ошибки (например, "invalid_file_format")
        **kwargs: Параметры для форматирования (например, code="ABC123")

    Returns:
        FriendlyError с заполненными параметрами
    """
    errors = {
        "invalid_file_format": INVALID_FILE_FORMAT,
        "empty_file": EMPTY_FILE,
        "corrupted_file": CORRUPTED_FILE,
        "no_valid_codes": NO_VALID_CODES,
        "barcode_not_found": BARCODE_NOT_FOUND,
        "daily_limit_reached": DAILY_LIMIT_REACHED,
        "trial_expired": TRIAL_EXPIRED,
        "unauthorized": UNAUTHORIZED,
        "forbidden": FORBIDDEN,
        "internal_error": INTERNAL_ERROR,
    }

    error = errors.get(error_key, INTERNAL_ERROR)

    # Форматируем сообщение с параметрами
    if kwargs:
        message = error.message.format(**kwargs) if "{" in error.message else error.message
        hint = error.hint.format(**kwargs) if error.hint and "{" in error.hint else error.hint
        return FriendlyError(message=message, hint=hint, details=error.details)

    return error
