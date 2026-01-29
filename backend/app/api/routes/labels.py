"""
API эндпоинты для работы с этикетками.

Основной функционал: объединение WB + ЧЗ.
"""

import hashlib
import io
import logging
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user  # noqa: F401 — используется в других endpoints
from app.config import LABEL, get_settings
from app.db.database import get_db, get_redis  # noqa: F401
from app.db.models import ProductCard, User, UserPlan
from app.models.schemas import (
    ErrorResponse,
    ExcelItemInfo,
    ExcelParseResponse,
    ExcelSampleItem,
    FileDetectionResponse,
    FileType,
    GenerationError,
    GtinInfo,
    GtinMatchingStatus,
    GtinPreflightResponse,
    LabelFormat,
    LabelMergeResponse,
    LabelTemplate,
    LayoutPreflightError,
    LayoutPreflightRequest,
    LayoutPreflightResponse,
    PreflightResponse,
    PreflightResult,
    PreflightStatus,
    TemplatesResponse,
)
from app.repositories import GenerationRepository, UsageRepository, UserRepository
from app.repositories.product_repo import ProductRepository
from app.services.auth import decode_access_token
from app.services.code_history import CodeHistoryService
from app.services.csv_parser import ChzCsvParser
from app.services.file_storage import get_file_storage
from app.services.label_balance import LabelBalanceService
from app.services.layout_preflight import (
    LayoutPreflightChecker,
    filter_fields_by_priority,
)
from app.services.preflight import PreflightChecker

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# Безопасная работа с файлами — защита от Path Traversal
ALLOWED_DIR = Path("data/generations").resolve()

# Допустимые MIME-типы для файлов с кодами ЧЗ
ALLOWED_CODES_TYPES = [
    "application/pdf",
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

# Минимальная длина полного кода ЧЗ с криптохвостом
# Структура: 01+GTIN(14)+21+serial(13)+91+key(4)+92+crypto(~44) = ~83 символа
MIN_CODE_LENGTH_WITH_CRYPTO = 80


def _is_codes_file(filename: str, _content_type: str | None) -> bool:
    """Определяет, является ли файл с кодами ЧЗ (PDF, CSV, Excel)."""
    if not filename:
        return False
    ext = filename.lower().split(".")[-1]
    return ext in ("pdf", "csv", "xlsx", "xls")


def _validate_codes_have_crypto(codes: list[str]) -> tuple[bool, list[str]]:
    """
    Проверяет наличие криптохвоста в кодах.

    Returns:
        (all_valid, short_codes) — все ли коды валидны и список коротких кодов
    """
    short_codes = []
    for code in codes:
        if len(code) < MIN_CODE_LENGTH_WITH_CRYPTO:
            short_codes.append(code[:30] + "..." if len(code) > 30 else code)
    return len(short_codes) == 0, short_codes[:5]  # Первые 5 для примера


def _normalize_chz_code(code: str) -> str | None:
    """
    Нормализует код ЧЗ — добавляет AI "01" если отсутствует.

    ЛК Честного Знака может выдавать коды без AI префикса "01":
    - С "01": 010467004977480221... (полный GS1)
    - Без "01": 0467004977480221... (только GTIN + данные)

    Возвращает нормализованный код или None если это не код ЧЗ.
    """
    code = code.strip()

    # Код уже с AI "01" — возвращаем как есть
    if code.startswith("01") and len(code) >= 16:
        return code

    # Код начинается с "04" (GTIN товаров) — добавляем "01"
    # GTIN для РФ начинается с 046, 047, 048, 049
    if code.startswith("04") and len(code) >= 14:
        return "01" + code

    return None


def _parse_codes_from_csv(file_bytes: bytes) -> list[str]:
    """Парсит коды DataMatrix из CSV файла."""
    import csv
    import io

    codes = []
    # Пробуем разные кодировки
    for encoding in ["utf-8", "cp1251", "latin-1"]:
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Не удалось определить кодировку CSV файла")

    reader = csv.reader(io.StringIO(text))
    for row in reader:
        for cell in row:
            normalized = _normalize_chz_code(cell)
            if normalized:
                codes.append(normalized)

    return codes


def _parse_codes_from_excel(file_bytes: bytes, _filename: str) -> list[str]:
    """Парсит коды DataMatrix из Excel файла."""
    import io

    import openpyxl

    codes = []
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)

    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            for cell in row:
                if cell is None:
                    continue
                normalized = _normalize_chz_code(str(cell))
                if normalized:
                    codes.append(normalized)

    wb.close()
    return codes


def parse_codes_from_file(file_bytes: bytes, filename: str) -> list[str]:
    """
    Парсер кодов ЧЗ из PDF, CSV или Excel файла.

    Args:
        file_bytes: Содержимое файла
        filename: Имя файла (для определения формата)

    Returns:
        Список кодов DataMatrix

    Raises:
        ValueError: Если не удалось извлечь коды или коды без криптохвоста
    """
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    codes: list[str] = []

    if ext == "pdf":
        from app.services.pdf_parser import PDFParser

        pdf_parser = PDFParser()
        page_count = pdf_parser.get_page_count(file_bytes)

        # Параллельный парсинг для больших PDF (>3 страниц = ~4x ускорение)
        if page_count > 3:
            result = pdf_parser.extract_codes_parallel(file_bytes)
        else:
            result = pdf_parser.extract_codes(file_bytes)

        codes = result.codes

    elif ext == "csv":
        codes = _parse_codes_from_csv(file_bytes)

    elif ext in ("xlsx", "xls"):
        codes = _parse_codes_from_excel(file_bytes, filename)

    else:
        raise ValueError(
            f"Неподдерживаемый формат файла: .{ext}. " "Используйте PDF, CSV или Excel (.xlsx)."
        )

    if not codes:
        raise ValueError(
            "Не найдено кодов маркировки в файле. "
            "Убедитесь что файл содержит коды DataMatrix из Честного Знака."
        )

    # Валидация криптохвоста (только для CSV/Excel — PDF всегда полный)
    if ext != "pdf":
        all_valid, short_codes = _validate_codes_have_crypto(codes)
        if not all_valid:
            examples = ", ".join(short_codes)
            raise ValueError(
                f"Коды без криптохвоста! Найдено {len(short_codes)} коротких кодов. "
                f"Примеры: {examples}. "
                "CSV/Excel из ЧЗ часто без криптоподписи — используйте PDF."
            )

    return codes


async def parse_codes_from_file_cached(
    file_bytes: bytes,
    filename: str,
    redis: "Redis | None" = None,
) -> list[str]:
    """
    Парсер кодов ЧЗ из PDF с кэшированием результатов.

    При повторном запросе того же PDF возвращает результат из Redis кэша.

    Args:
        file_bytes: Содержимое PDF файла
        filename: Имя файла
        redis: Redis клиент для кэширования (опционально)

    Returns:
        Список кодов DataMatrix
    """
    from app.services.parse_cache import ParseCache

    # Если Redis доступен — проверяем кэш
    if redis:
        cache = ParseCache(redis)
        file_hash = cache.compute_hash(file_bytes)

        # Проверяем кэш
        cached_codes = await cache.get(file_hash)
        if cached_codes is not None:
            return cached_codes

    # Парсим файл (синхронная операция)
    codes = parse_codes_from_file(file_bytes, filename)

    # Сохраняем в кэш
    if redis:
        await cache.set(file_hash, codes)

    return codes


# Временное in-memory хранилище для fallback
# Импортируем из users.py для единого источника данных
from app.api.routes.users import _usage_db, _users_db  # noqa: E402


async def _get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency для получения UserRepository."""
    return UserRepository(db)


async def _get_usage_repo(db: AsyncSession = Depends(get_db)) -> UsageRepository:
    """Dependency для получения UsageRepository."""
    return UsageRepository(db)


async def _get_gen_repo(db: AsyncSession = Depends(get_db)) -> GenerationRepository:
    """Dependency для получения GenerationRepository."""
    return GenerationRepository(db)


async def _get_code_history(db: AsyncSession = Depends(get_db)) -> CodeHistoryService:
    """Dependency для получения CodeHistoryService."""
    return CodeHistoryService(db)


async def _get_product_repo(db: AsyncSession = Depends(get_db)) -> ProductRepository:
    """Dependency для получения ProductRepository."""
    return ProductRepository(db)


async def _get_label_balance_service(db: AsyncSession = Depends(get_db)) -> LabelBalanceService:
    """Dependency для получения LabelBalanceService."""
    return LabelBalanceService(db)


# OAuth2 схема для опциональной JWT авторизации
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/telegram", auto_error=False)


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Опциональная JWT авторизация.

    Возвращает пользователя если токен валиден, иначе None.
    Используется для эндпоинтов которые работают и с JWT и с telegram_id.
    """
    if not token:
        return None

    user_id_str = decode_access_token(token)
    if not user_id_str:
        return None

    try:
        from uuid import UUID

        user_id = UUID(user_id_str)
    except ValueError:
        return None

    user_repo = UserRepository(db)
    return await user_repo.get_by_id(user_id)


async def check_user_limit_db(
    telegram_id: int | None,
    labels_count: int,
    user_repo: UserRepository,
    usage_repo: UsageRepository,
) -> tuple[bool, str, int]:
    """
    Проверить лимит пользователя через БД.

    Args:
        telegram_id: ID пользователя Telegram (None = анонимный)
        labels_count: Количество этикеток для генерации
        user_repo: Репозиторий пользователей
        usage_repo: Репозиторий использования

    Returns:
        (allowed, message, remaining)
    """
    if telegram_id is None:
        return (
            labels_count <= settings.free_tier_daily_limit,
            "Для доступа к лимитам авторизуйтесь через бота",
            settings.free_tier_daily_limit,
        )

    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        return (
            labels_count <= settings.free_tier_daily_limit,
            "Пользователь не найден, применён Free лимит",
            settings.free_tier_daily_limit,
        )

    result = await usage_repo.check_limit(
        user=user,
        labels_count=labels_count,
        free_limit=settings.free_tier_daily_limit,
    )

    if not result["allowed"]:
        message = (
            f"Превышен лимит: использовано {result['used_today']}/{result['daily_limit']} сегодня"
        )
    else:
        message = "OK"

    return (result["allowed"], message, result["remaining"])


async def record_user_usage_db(
    telegram_id: int | None,
    labels_count: int,
    preflight_ok: bool,
    user_repo: UserRepository,
    usage_repo: UsageRepository,
) -> None:
    """
    Записать использование через БД.
    """
    if telegram_id is None:
        return

    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        return

    preflight_status = "ok" if preflight_ok else "error"
    await usage_repo.record_usage(
        user_id=user.id,
        labels_count=labels_count,
        preflight_status=preflight_status,
    )


def check_user_limit_fallback(telegram_id: int | None, labels_count: int) -> tuple[bool, str, int]:
    """
    Fallback проверка лимита без БД.
    """
    if telegram_id is None:
        return (
            labels_count <= settings.free_tier_daily_limit,
            "Для доступа к лимитам авторизуйтесь через бота",
            settings.free_tier_daily_limit,
        )

    user = _users_db.get(telegram_id)
    if not user:
        return (
            labels_count <= settings.free_tier_daily_limit,
            "Пользователь не найден, применён Free лимит",
            settings.free_tier_daily_limit,
        )

    plan = user.get("plan", "free")
    usage = _usage_db.get(telegram_id, {})

    today = date.today().isoformat()
    used_today = usage.get("daily_usage", {}).get(today, 0)

    if plan == "free":
        daily_limit = settings.free_tier_daily_limit
    elif plan == "pro":
        daily_limit = 500
    else:
        daily_limit = 999999

    remaining = daily_limit - used_today
    allowed = remaining >= labels_count

    if not allowed:
        message = f"Превышен лимит: использовано {used_today}/{daily_limit} сегодня"
    else:
        message = "OK"

    return (allowed, message, remaining)


def record_user_usage_fallback(
    telegram_id: int | None, labels_count: int, preflight_ok: bool = True
):
    """
    Fallback запись использования без БД.
    """
    if telegram_id is None:
        return

    if telegram_id not in _usage_db:
        _usage_db[telegram_id] = {
            "total_generated": 0,
            "success_count": 0,
            "preflight_errors": 0,
            "daily_usage": {},
        }

    usage = _usage_db[telegram_id]
    today = date.today().isoformat()

    usage["total_generated"] += labels_count
    if preflight_ok:
        usage["success_count"] += 1
    else:
        usage["preflight_errors"] += 1

    if "daily_usage" not in usage:
        usage["daily_usage"] = {}
    usage["daily_usage"][today] = usage["daily_usage"].get(today, 0) + labels_count


@router.post(
    "/labels/detect-file",
    response_model=FileDetectionResponse,
    responses={
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
    },
    summary="Анализ Excel файла с баркодами",
    description="""
**Анализирует загруженный Excel файл и возвращает информацию о нём.**

**Возвращает:**
- Колонки файла
- Количество строк с данными
- Автоопределённая колонка с баркодами
- Примеры данных (первые строки)

**Поддерживаемые форматы:**
- Excel (.xlsx, .xls)
""",
)
async def detect_file_type(
    file: Annotated[UploadFile, File(description="Excel файл с баркодами")],
) -> FileDetectionResponse:
    """
    Анализ Excel файла с баркодами.

    Возвращает информацию о структуре файла для предварительного просмотра.
    """
    from app.services.excel_parser import ExcelBarcodeParser

    # Валидация размера файла
    if file.size and file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    content = await file.read()
    filename = file.filename or "unknown"
    size_bytes = len(content)

    # Проверяем Excel
    if filename.lower().endswith((".xlsx", ".xls")):
        try:
            excel_parser = ExcelBarcodeParser()
            columns_info = excel_parser.get_columns_info(content, filename)
            return FileDetectionResponse(
                file_type=FileType.EXCEL,
                filename=filename,
                size_bytes=size_bytes,
                rows_count=columns_info["total_rows"],
                columns=columns_info["all_columns"],
                detected_barcode_column=columns_info["detected_column"],
                sample_items=[ExcelSampleItem(**item) for item in columns_info["sample_items"]],
            )
        except Exception as e:
            return FileDetectionResponse(
                file_type=FileType.UNKNOWN,
                filename=filename,
                size_bytes=size_bytes,
                error=f"Не удалось прочитать Excel: {str(e)}",
            )

    # Неизвестный формат
    return FileDetectionResponse(
        file_type=FileType.UNKNOWN,
        filename=filename,
        size_bytes=size_bytes,
        error="Поддерживаются только Excel файлы (.xlsx, .xls)",
    )


@router.post(
    "/labels/preflight",
    response_model=PreflightResponse,
    summary="Проверка качества",
    description="""
Проверка качества этикеток БЕЗ генерации результата.

Проверяется:
- Размер DataMatrix (минимум 22x22мм)
- Контрастность (минимум 80%)
- Наличие quiet zone (3мм)
- Читаемость DataMatrix
    """,
)
async def preflight_check(
    wb_pdf: Annotated[UploadFile, File(description="PDF с этикетками Wildberries")],
    codes_file: Annotated[UploadFile, File(description="PDF с кодами Честного Знака")],
) -> PreflightResponse:
    """
    Проверка качества без генерации результата.

    Полезно для валидации файлов перед массовой генерацией.
    """
    wb_pdf_bytes = await wb_pdf.read()
    codes_bytes = await codes_file.read()

    checker = PreflightChecker()

    try:
        result = await checker.check(
            wb_pdf_bytes=wb_pdf_bytes,
            codes_bytes=codes_bytes,
            codes_filename=codes_file.filename or "codes.pdf",
        )

        return PreflightResponse(result=result)

    except ValueError:
        # Возвращаем ошибку как результат preflight
        return PreflightResponse(
            result=PreflightResult(
                overall_status=PreflightStatus.ERROR,
                checks=[],
                can_proceed=False,
            )
        )


@router.post(
    "/labels/preflight-layout",
    response_model=LayoutPreflightResponse,
    summary="Проверка данных этикетки ПЕРЕД генерацией",
    description="""
**Проверка данных ПЕРЕД генерацией** — экономит лимит пользователя.

Проверяется:
- Количество активных полей vs лимит шаблона
- Ширина текста — поместится ли при минимальном шрифте
- Совместимость layout и размера этикетки

**Лимиты полей по шаблонам:**
| Template | Layout | Max полей |
|----------|--------|-----------|
| Basic 58x30 | basic | 2 |
| Basic 58x40 | basic | 4 |
| Basic 58x60 | basic | 4 |
| Extended 58x40 | extended | 12 |
| Extended 58x60 | extended | 12 |
| Professional 58x40 | professional | 10 |

**Пример запроса:**
```json
{
  "template": "58x40",
  "layout": "basic",
  "fields": [
    {"id": "article", "key": "Артикул", "value": "WB-12345-VERY-LONG"},
    {"id": "size", "key": "Размер", "value": "42-44"},
    {"id": "color", "key": "Цвет", "value": "белый"}
  ],
  "organization": "ООО Рога и Копыта",
  "inn": "1234567890"
}
```
    """,
)
async def preflight_layout(
    request: LayoutPreflightRequest,
) -> LayoutPreflightResponse:
    """
    Проверка данных этикетки ПЕРЕД генерацией.

    Позволяет выявить проблемы до того, как лимит будет потрачен:
    - Слишком много полей для выбранного шаблона
    - Текст не помещается при минимальном шрифте
    - Несовместимость layout и размера
    """
    checker = LayoutPreflightChecker()

    # Преобразуем fields в список словарей
    fields_dicts = [{"id": f.id, "key": f.key, "value": f.value} for f in request.fields]

    result = checker.check(
        template=request.template,
        layout=request.layout,
        fields=fields_dicts,
        organization=request.organization,
        inn=request.inn,
    )

    # Преобразуем dataclass в Pydantic модели
    errors = [
        LayoutPreflightError(
            field_id=e.field_id,
            message=e.message,
            suggestion=e.suggestion,
        )
        for e in result.errors
    ]

    return LayoutPreflightResponse(
        success=result.success,
        errors=errors,
        suggestions=result.suggestions,
    )


@router.get(
    "/labels/templates",
    response_model=TemplatesResponse,
    summary="Доступные шаблоны этикеток",
)
async def get_templates() -> TemplatesResponse:
    """
    Получить список доступных шаблонов этикеток.

    Returns:
        Список шаблонов с размерами
    """
    templates = [
        LabelTemplate(
            width_mm=w,
            height_mm=h,
            name=f"{int(w)}x{int(h)}",
        )
        for w, h in LABEL.SUPPORTED_TEMPLATES
    ]

    return TemplatesResponse(templates=templates)


@router.post(
    "/labels/parse-excel",
    response_model=ExcelParseResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные входные данные"},
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
    },
    summary="Анализ Excel с баркодами (preview)",
    description="""
**Анализирует Excel файл и возвращает preview для подтверждения пользователем.**

Используется для human-in-the-loop workflow:
1. Пользователь загружает Excel с баркодами
2. Система определяет колонку с баркодами и возвращает preview
3. Пользователь подтверждает или выбирает другую колонку
4. После подтверждения вызывается /labels/generate-full с параметром barcode_column

**Возвращает:**
- detected_column: Автоопределённая колонка с баркодами
- all_columns: Все колонки в файле
- barcode_candidates: Колонки, похожие на баркоды
- total_rows: Количество строк с данными
- sample_items: Примеры данных (первые 5 строк)
""",
)
async def parse_excel(
    barcodes_excel: Annotated[UploadFile, File(description="Excel файл с баркодами Wildberries")],
    _current_user: User | None = Depends(get_current_user_optional),
) -> ExcelParseResponse:
    """
    Анализирует Excel файл и возвращает preview для подтверждения.

    Пользователь должен подтвердить:
    1. Правильная ли колонка выбрана
    2. Корректны ли примеры данных

    После подтверждения вызвать /labels/generate-full с barcode_column.
    """
    from app.services.excel_parser import ExcelBarcodeParser

    # Валидация размера файла
    if barcodes_excel.size and barcodes_excel.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Excel файл слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    # Валидация типа файла
    allowed_excel_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]
    if barcodes_excel.content_type not in allowed_excel_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть в формате Excel (.xlsx или .xls)",
        )

    # Читаем файл
    excel_bytes = await barcodes_excel.read()
    filename = barcodes_excel.filename or "barcodes.xlsx"

    # Анализируем Excel
    excel_parser = ExcelBarcodeParser()
    try:
        columns_info = excel_parser.get_columns_info(
            excel_bytes=excel_bytes,
            filename=filename,
        )
    except ValueError as e:
        return ExcelParseResponse(
            success=False,
            message=f"Ошибка парсинга Excel: {str(e)}",
        )

    # Проверяем что нашлись данные
    if columns_info["total_rows"] == 0:
        return ExcelParseResponse(
            success=False,
            all_columns=columns_info["all_columns"],
            message="В Excel файле не найдено валидных данных",
        )

    # Если колонка с баркодами не найдена автоматически
    if not columns_info["detected_column"]:
        return ExcelParseResponse(
            success=True,
            detected_column=None,
            all_columns=columns_info["all_columns"],
            barcode_candidates=columns_info["barcode_candidates"],
            total_rows=columns_info["total_rows"],
            sample_items=[ExcelSampleItem(**item) for item in columns_info["sample_items"]],
            message="Колонка с баркодами не определена автоматически. "
            "Пожалуйста, выберите колонку вручную.",
        )

    # Успешный парсинг
    return ExcelParseResponse(
        success=True,
        detected_column=columns_info["detected_column"],
        all_columns=columns_info["all_columns"],
        barcode_candidates=columns_info["barcode_candidates"],
        total_rows=columns_info["total_rows"],
        sample_items=[ExcelSampleItem(**item) for item in columns_info["sample_items"]],
        message=f"Найдено {columns_info['total_rows']} строк. "
        f"Колонка с баркодами: {columns_info['detected_column']}",
    )


@router.post(
    "/labels/preflight-matching",
    response_model=GtinPreflightResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные входные данные"},
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
    },
    summary="Проверка матчинга GTIN ДО генерации",
    description="""
**Проверяет совместимость Excel и PDF ДО генерации этикеток.**

Вызывается после загрузки обоих файлов для показа блока матчинга.

**Возвращает:**
- status: auto_matched | auto_fallback | manual_required | error
- gtins: список GTIN из кодов ЧЗ с количеством
- excel_items: список товаров из Excel
- auto_mapping: автоматический маппинг GTIN → товар (если возможен)

**Статусы:**
- auto_matched: баркоды Excel совпадают с GTIN — всё ок
- auto_fallback: 1 товар + 1 GTIN с разными баркодами — авто-сопоставление
- manual_required: нужен ручной матчинг через UI
- error: ошибка парсинга файлов
""",
)
async def preflight_matching(
    barcodes_excel: Annotated[UploadFile, File(description="Excel файл с баркодами WB")],
    codes_pdf: Annotated[UploadFile, File(description="PDF файл с кодами ЧЗ")],
    barcode_column: Annotated[str | None, Form(description="Колонка с баркодами")] = None,
    _current_user: User | None = Depends(get_current_user_optional),
) -> GtinPreflightResponse:
    """
    Проверяет матчинг GTIN с товарами ДО генерации.

    Позволяет показать пользователю блок матчинга сразу после загрузки файлов,
    а не после ошибки генерации.
    """
    from app.services.excel_parser import ExcelBarcodeParser

    # Валидация размеров файлов
    for file, name in [(barcodes_excel, "Excel"), (codes_pdf, "PDF")]:
        if file.size and file.size > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"{name} файл слишком большой. Максимум: {settings.max_upload_size_mb}MB",
            )

    # Валидация типов файлов
    allowed_excel_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]
    if barcodes_excel.content_type not in allowed_excel_types:
        return GtinPreflightResponse(
            success=False,
            status=GtinMatchingStatus.ERROR,
            message="Excel файл должен быть в формате .xlsx или .xls",
        )

    if not _is_codes_file(codes_pdf.filename or "", codes_pdf.content_type):
        return GtinPreflightResponse(
            success=False,
            status=GtinMatchingStatus.ERROR,
            message="Файл кодов ЧЗ должен быть в формате PDF, CSV или Excel",
        )

    # Читаем файлы
    excel_bytes = await barcodes_excel.read()
    codes_bytes = await codes_pdf.read()
    excel_filename = barcodes_excel.filename or "barcodes.xlsx"
    codes_filename = codes_pdf.filename or "codes.pdf"

    # Парсим Excel
    excel_parser = ExcelBarcodeParser()
    try:
        excel_data = excel_parser.parse(
            excel_bytes=excel_bytes,
            filename=excel_filename,
            column_name=barcode_column,
        )
    except ValueError as e:
        return GtinPreflightResponse(
            success=False,
            status=GtinMatchingStatus.ERROR,
            message=f"Ошибка парсинга Excel: {str(e)}",
        )

    if not excel_data.items:
        return GtinPreflightResponse(
            success=False,
            status=GtinMatchingStatus.ERROR,
            message="В Excel файле не найдено товаров с баркодами",
        )

    # Парсим файл с кодами ЧЗ (PDF, CSV, Excel)
    try:
        codes = parse_codes_from_file(codes_bytes, codes_filename)
    except ValueError as e:
        error_msg = str(e)
        # Проверяем на ошибку криптохвоста — даём понятное объяснение
        if "криптохвост" in error_msg.lower() or "коротких кодов" in error_msg.lower():
            return GtinPreflightResponse(
                success=False,
                status=GtinMatchingStatus.ERROR,
                message="❌ Коды без криптоподписи — DataMatrix не будет сканироваться! "
                "CSV/Excel из ЧЗ часто экспортируются без криптохвоста. "
                "Скачайте PDF из личного кабинета Честного Знака.",
            )
        return GtinPreflightResponse(
            success=False,
            status=GtinMatchingStatus.ERROR,
            message=f"Ошибка парсинга файла с кодами: {error_msg}",
        )

    if not codes:
        return GtinPreflightResponse(
            success=False,
            status=GtinMatchingStatus.ERROR,
            message="В файле не найдено кодов маркировки",
        )

    # Извлекаем GTIN из кодов
    def extract_gtin(code: str) -> str | None:
        if code.startswith("01") and len(code) >= 16:
            return code[2:16]
        return None

    # Собираем уникальные GTIN с количеством
    gtin_counts: dict[str, int] = {}
    for code in codes:
        gtin = extract_gtin(code)
        if gtin:
            barcode_from_gtin = gtin.lstrip("0")
            gtin_counts[barcode_from_gtin] = gtin_counts.get(barcode_from_gtin, 0) + 1

    gtins = [GtinInfo(gtin=gtin, codes_count=count) for gtin, count in sorted(gtin_counts.items())]
    total_codes = sum(gtin_counts.values())

    # Конвертируем items в ExcelItemInfo
    excel_items = [
        ExcelItemInfo(
            barcode=item.barcode or "",
            name=item.name,
            size=item.size,
            color=item.color,
            article=item.article,
        )
        for item in excel_data.items
    ]

    # Индекс товаров по баркоду для матчинга
    items_by_barcode: dict[str, int] = {}
    for idx, item in enumerate(excel_items):
        if item.barcode:
            normalized = item.barcode.strip().lstrip("0")
            items_by_barcode[normalized] = idx
            items_by_barcode[item.barcode.strip()] = idx

    # Проверяем матчинг
    auto_mapping: dict[str, int] = {}
    missing_gtins: list[str] = []

    for gtin_info in gtins:
        gtin = gtin_info.gtin
        # Пробуем найти товар по баркоду
        item_idx = items_by_barcode.get(gtin)
        if item_idx is not None:
            auto_mapping[gtin] = item_idx
        else:
            missing_gtins.append(gtin)

    # Определяем статус
    if not missing_gtins:
        # Все GTIN сматчились — auto_matched
        return GtinPreflightResponse(
            success=True,
            status=GtinMatchingStatus.AUTO_MATCHED,
            message=f"Все товары сопоставлены: {len(gtins)} GTIN → {total_codes} кодов",
            gtins=gtins,
            excel_items=excel_items,
            total_codes=total_codes,
            auto_mapping=auto_mapping,
        )

    # Есть несматченные GTIN — проверяем auto_fallback
    unique_gtins = set(gtin_counts.keys())

    if len(excel_items) == 1 and len(unique_gtins) == 1:
        # Auto-fallback: 1 товар + 1 GTIN с разными баркодами
        single_gtin = next(iter(unique_gtins))
        return GtinPreflightResponse(
            success=True,
            status=GtinMatchingStatus.AUTO_FALLBACK,
            message=f"Баркод WB ({excel_items[0].barcode}) отличается от GTIN ({single_gtin}). "
            f"Будет применено авто-сопоставление для {total_codes} кодов.",
            gtins=gtins,
            excel_items=excel_items,
            total_codes=total_codes,
            auto_mapping={single_gtin: 0},  # Единственный товар = индекс 0
        )

    # Нужен ручной матчинг
    return GtinPreflightResponse(
        success=True,
        status=GtinMatchingStatus.MANUAL_REQUIRED,
        message=f"Баркоды в Excel не совпадают с GTIN в кодах ЧЗ. "
        f"Укажите соответствие для {len(missing_gtins)} GTIN.",
        gtins=gtins,
        excel_items=excel_items,
        total_codes=total_codes,
        auto_mapping=auto_mapping,  # Частичный маппинг, если есть
    )


# === АВТОСОХРАНЕНИЕ КАРТОЧЕК: helper-функции ===


def _should_autosave_products(user: User | None) -> bool:
    """
    Проверить можно ли автосохранять карточки для пользователя.

    Автосохранение доступно только для PRO и ENTERPRISE тарифов.
    """
    if not user:
        return False
    from app.db.models import UserPlan

    return user.plan in (UserPlan.PRO, UserPlan.ENTERPRISE)


def _extract_unique_products_for_save(label_items: list) -> list[dict]:
    """
    Извлечь уникальные товары для сохранения в базу карточек.

    Дедупликация по barcode — если один товар встречается несколько раз
    (несколько кодов ЧЗ для одного баркода), сохраняем только один раз.

    Returns:
        Список словарей с полями для ProductCard
    """
    seen_barcodes: set[str] = set()
    products: list[dict] = []

    for item in label_items:
        if not item.barcode or item.barcode in seen_barcodes:
            continue

        seen_barcodes.add(item.barcode)
        products.append(
            {
                "barcode": item.barcode,
                "name": item.name,
                "article": item.article,
                "size": item.size,
                "color": item.color,
                "composition": item.composition,
                "country": item.country,
                "brand": item.brand,
                "manufacturer": item.manufacturer,
                "production_date": item.production_date,
                "importer": item.importer,
                "certificate_number": item.certificate_number,
                "address": item.address,
            }
        )

    return products


async def _autosave_products(
    user,
    label_items: list,
    product_repo,
) -> dict | None:
    """
    Автосохранение карточек товаров после успешной генерации.

    Args:
        user: Пользователь (PRO/ENTERPRISE)
        label_items: Список товаров из генерации
        product_repo: Репозиторий карточек

    Returns:
        Статистика {"created": N, "updated": M} или None при ошибке
    """
    if not _should_autosave_products(user):
        return None

    products = _extract_unique_products_for_save(label_items)
    if not products:
        return None

    try:
        result = await product_repo.bulk_upsert(user.id, products)
        logger.info(
            f"[autosave] Сохранено карточек для user {user.id}: "
            f"created={result['created']}, updated={result['updated']}"
        )
        return result
    except Exception as e:
        logger.warning(f"[autosave] Ошибка сохранения карточек: {e}")
        return None


@router.post(
    "/labels/generate-from-excel",
    response_model=LabelMergeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные входные данные"},
        403: {"model": ErrorResponse, "description": "Превышен лимит"},
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
    },
    summary="Генерация этикеток из Excel с выбором layout",
    description="""
**Генерация полных этикеток из Excel файла с поддержкой layouts.**

Новый режим генерации (ReportLab) с возможностью кастомизации внешнего вида этикеток:
- **basic** — вертикальный шаблон: DataMatrix слева, штрихкод справа внизу
- **professional** — двухколоночный: реквизиты, импортер, производитель (только 58x40, 58x60)

**Входные данные:**
- `barcodes_excel` — Excel с баркодами WB (с метаданными: артикул, размер, цвет, название)
- `codes_file` — PDF с кодами ЧЗ (только PDF содержит криптоподпись)
- `organization_name` — Название организации для этикетки
- `layout` — Шаблон этикетки (basic, professional)
- `label_size` — Размер этикетки (58x40, 58x30, 58x60)
- `show_article`, `show_size_color`, `show_name` — Какие поля показывать
- Для professional: `organization_address`, `importer`, `manufacturer`, `production_date`, `certificate_number`

**Результат:**
- Векторный PDF с этикетками: WB штрихкод + текст + DataMatrix ЧЗ
""",
)
async def generate_from_excel(
    barcodes_excel: Annotated[UploadFile, File(description="Excel с баркодами WB")],
    codes_file: Annotated[UploadFile | None, File(description="PDF с кодами ЧЗ")] = None,
    codes: Annotated[str | None, Form(description="JSON массив кодов ЧЗ")] = None,
    organization_name: Annotated[str | None, Form(description="Название организации")] = None,
    inn: Annotated[str | None, Form(description="ИНН организации")] = None,
    layout: Annotated[str, Form(description="Шаблон: basic, professional, extended")] = "basic",
    label_size: Annotated[str, Form(description="Размер: 58x40, 58x30, 58x60")] = "58x40",
    label_format: Annotated[str, Form(description="Формат: combined или separate")] = "combined",
    # Флаги отображения полей
    show_article: Annotated[bool, Form(description="Показывать артикул")] = True,
    show_size: Annotated[bool, Form(description="Показывать размер")] = True,
    show_color: Annotated[bool, Form(description="Показывать цвет")] = True,
    # Deprecated: для обратной совместимости
    show_size_color: Annotated[
        bool | None, Form(description="[Deprecated] Используйте show_size и show_color")
    ] = None,
    show_name: Annotated[bool, Form(description="Показывать название")] = True,
    show_organization: Annotated[bool, Form(description="Показывать организацию")] = True,
    show_inn: Annotated[bool, Form(description="Показывать ИНН")] = False,
    show_country: Annotated[bool, Form(description="Показывать страну")] = False,
    show_composition: Annotated[bool, Form(description="Показывать состав")] = False,
    show_chz_code_text: Annotated[bool, Form(description="Показывать код ЧЗ текстом")] = True,
    show_brand: Annotated[bool, Form(description="Показывать бренд")] = False,
    # Поля для professional шаблона
    show_importer: Annotated[bool, Form(description="Показывать импортер")] = False,
    show_manufacturer: Annotated[bool, Form(description="Показывать производитель")] = False,
    show_address: Annotated[bool, Form(description="Показывать адрес")] = False,
    show_production_date: Annotated[bool, Form(description="Показывать дату производства")] = False,
    show_certificate: Annotated[bool, Form(description="Показывать сертификат")] = False,
    # Режим нумерации этикеток
    numbering_mode: Annotated[
        Literal["none", "sequential", "per_product", "continue"],
        Form(description="Режим нумерации: none, sequential, per_product, continue"),
    ] = "none",
    start_number: Annotated[
        int | None, Form(description="Стартовый номер (для режима continue)")
    ] = None,
    # Реквизиты для professional шаблона
    organization_address: Annotated[str | None, Form(description="Адрес производства")] = None,
    importer: Annotated[str | None, Form(description="Импортер")] = None,
    manufacturer: Annotated[str | None, Form(description="Производитель")] = None,
    production_date: Annotated[str | None, Form(description="Дата производства")] = None,
    certificate_number: Annotated[str | None, Form(description="Номер сертификата")] = None,
    # Кастомные строки для extended шаблона
    custom_lines: Annotated[
        str | None, Form(description="JSON массив кастомных строк для extended")
    ] = None,
    # Диапазон печати ("Ножницы")
    range_start: Annotated[int | None, Form(description="Начало диапазона (1-based)")] = None,
    range_end: Annotated[int | None, Form(description="Конец диапазона (1-based)")] = None,
    # Preflight: остановить генерацию при ошибке (не списывать лимит)
    skip_on_preflight_error: Annotated[
        bool,
        Form(
            description="При ошибке preflight: True = вернуть ошибку и НЕ генерировать (default), "
            "False = генерировать с PREFLIGHT ERROR на этикетке (legacy)"
        ),
    ] = True,
    # Fallback значения
    fallback_size: Annotated[str | None, Form(description="Размер по умолчанию")] = None,
    fallback_color: Annotated[str | None, Form(description="Цвет по умолчанию")] = None,
    barcode_column: Annotated[str | None, Form(description="Колонка с баркодами")] = None,
    # Ручной маппинг GTIN → индекс товара (JSON: {"gtin": index})
    manual_gtin_mapping: Annotated[
        str | None, Form(description="JSON маппинг GTIN → индекс товара")
    ] = None,
    telegram_id: Annotated[int | None, Form(description="Telegram ID")] = None,
    current_user: User | None = Depends(get_current_user_optional),
    user_repo: UserRepository = Depends(_get_user_repo),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
    product_repo: ProductRepository = Depends(_get_product_repo),
    label_balance_service: LabelBalanceService = Depends(_get_label_balance_service),
    redis: Redis = Depends(get_redis),
) -> LabelMergeResponse:
    """
    Генерация этикеток из Excel с использованием LabelGenerator (ReportLab).

    Создаёт полные векторные этикетки с:
    - Штрихкодом WB (EAN-13/Code128)
    - Названием товара
    - Артикулом
    - Размером/цветом
    - Организацией
    - DataMatrix ЧЗ
    """
    from uuid import uuid4

    # Диагностика: логируем параметры (ПДн маскированы для 152-ФЗ)
    inn_masked = (inn[:3] + "***" + inn[-2:]) if inn and len(inn) > 5 else "***" if inn else None
    org_masked = (
        (organization_name[:10] + "...")
        if organization_name and len(organization_name) > 10
        else organization_name
    )
    logger.info(
        f"[generate_from_excel] Параметры: inn={inn_masked}, show_inn={show_inn}, "
        f"organization={org_masked}, show_organization={show_organization}"
    )

    from app.models.label_types import LabelLayout, LabelSize
    from app.services.excel_parser import ExcelBarcodeParser
    from app.services.label_generator import GtinMatchingException, LabelGenerator, LabelItem

    # Определяем пользователя: JWT авторизация или Bot Secret + telegram_id
    user = current_user
    user_telegram_id = telegram_id
    if user:
        user_telegram_id = int(user.telegram_id) if user.telegram_id else None
    elif telegram_id:
        # Бот передаёт telegram_id — получаем пользователя по нему
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        user_telegram_id = telegram_id
    else:
        # Ни JWT, ни telegram_id — доступ запрещён
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Используется только объединённый формат
    format_enum = LabelFormat.COMBINED

    try:
        layout_enum = LabelLayout(layout)
    except ValueError:
        layout_enum = LabelLayout.BASIC

    try:
        size_enum = LabelSize(label_size)
    except ValueError:
        size_enum = LabelSize.SIZE_58x40

    # Валидация размера файлов
    if barcodes_excel.size and barcodes_excel.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Excel файл слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    if codes_file and codes_file.size and codes_file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл кодов слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    # Проверяем что коды переданы хотя бы одним способом
    if not codes_file and not codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо передать коды ЧЗ (codes_file или codes)",
        )

    # Читаем Excel файл
    excel_bytes = await barcodes_excel.read()

    # Получаем коды ЧЗ из файла или JSON
    import json as json_module

    codes_list: list[str] = []
    if codes_file:
        codes_bytes = await codes_file.read()
        codes_list = parse_codes_from_file(codes_bytes, codes_file.filename or "codes.pdf")
    elif codes:
        try:
            raw_codes = json_module.loads(codes)
            # Нормализуем коды (добавляем "01" если отсутствует)
            codes_list = []
            for code in raw_codes:
                normalized = _normalize_chz_code(str(code))
                if normalized:
                    codes_list.append(normalized)
            # Проверка криптохвоста (как для CSV/Excel)
            all_valid, short_codes = _validate_codes_have_crypto(codes_list)
            if not all_valid:
                examples = ", ".join(short_codes)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Коды без криптохвоста! Примеры: {examples}. "
                    "DataMatrix не будет сканироваться. Используйте PDF из ЛК Честного Знака.",
                )
        except json_module.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат JSON в параметре codes",
            )

    # === PREFLIGHT ПРОВЕРКА (первый и последний код) ===
    # Выполняем ДО async decision чтобы передать результат в Celery
    preflight_checker = PreflightChecker()
    preflight_result = await preflight_checker.check_codes_only(codes=codes_list)
    preflight_ok = True
    if preflight_result:
        preflight_ok = preflight_result.overall_status.value != "error"

    # === ПРОВЕРКА ЛИМИТА (перед ASYNC decision!) ===
    labels_count_for_limit = len(codes_list)
    limit_result = None
    if user:
        limit_result = await usage_repo.check_limit(
            user=user,
            labels_count=labels_count_for_limit,
            free_limit=settings.free_tier_daily_limit,
        )
        allowed = limit_result["allowed"]
    else:
        try:
            allowed, _, _ = await check_user_limit_db(
                user_telegram_id, labels_count_for_limit, user_repo, usage_repo
            )
        except Exception:
            allowed, _, _ = check_user_limit_fallback(user_telegram_id, labels_count_for_limit)

    if not allowed:
        used_today = limit_result.get("used_today", 0) if limit_result else 0
        daily_limit = (
            limit_result.get("daily_limit", settings.free_tier_daily_limit)
            if limit_result
            else settings.free_tier_daily_limit
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Превышен дневной лимит. Оформите Pro подписку.",
                "used_today": used_today,
                "daily_limit": daily_limit,
                "requested": labels_count_for_limit,
            },
        )

    # === ASYNC DECISION: Celery для больших файлов (>60 кодов) ===
    from app.tasks.generate_labels import ASYNC_THRESHOLD_CODES

    codes_count_for_threshold = len(codes_list)
    should_use_async = codes_count_for_threshold > ASYNC_THRESHOLD_CODES and user is not None

    if should_use_async:
        import base64

        from app.repositories.task_repository import TaskRepository
        from app.tasks.generate_labels import generate_from_excel_async

        logger.info(
            f"[generate_from_excel] ASYNC режим: {codes_count_for_threshold} кодов > {ASYNC_THRESHOLD_CODES}"
        )

        # Создаём задачу в БД (используем сессию из product_repo)
        task_repo = TaskRepository(product_repo.session)
        task = await task_repo.create(
            user_id=user.id,
            total_pages=codes_count_for_threshold,
        )

        # Подготавливаем параметры для Celery
        excel_bytes_b64 = base64.b64encode(excel_bytes).decode("utf-8")

        # Парсим кастомные строки
        custom_lines_parsed = None
        if custom_lines:
            import contextlib

            with contextlib.suppress(json_module.JSONDecodeError, TypeError):
                custom_lines_parsed = json_module.loads(custom_lines)

        params = {
            "excel_filename": barcodes_excel.filename or "barcodes.xlsx",
            "barcode_column": barcode_column,
            "layout": layout,
            "label_size": label_size,
            "label_format": label_format,
            "organization_name": organization_name,
            "inn": inn,
            "show_article": show_article,
            "show_size": show_size if show_size_color is None else show_size_color,
            "show_color": show_color if show_size_color is None else show_size_color,
            "show_name": show_name,
            "show_organization": show_organization,
            "show_inn": show_inn,
            "show_country": show_country,
            "show_composition": show_composition,
            "show_chz_code_text": show_chz_code_text,
            "show_brand": show_brand,
            "show_importer": show_importer,
            "show_manufacturer": show_manufacturer,
            "show_address": show_address,
            "show_production_date": show_production_date,
            "show_certificate": show_certificate,
            "numbering_mode": numbering_mode,
            "start_number": start_number,
            "organization_address": organization_address,
            "importer_text": importer,
            "manufacturer_text": manufacturer,
            "production_date_text": production_date,
            "certificate_number_text": certificate_number,
            "custom_lines": custom_lines_parsed,
            "fallback_size": fallback_size,
            "fallback_color": fallback_color,
            "preflight_ok": preflight_ok,
        }

        # Запускаем Celery задачу
        generate_from_excel_async.delay(
            task_id=str(task.id),
            excel_bytes_b64=excel_bytes_b64,
            codes_list=codes_list,
            params=params,
        )

        # Списываем баланс для PRO
        if user and user.plan == "pro":
            try:
                await label_balance_service.debit_labels(
                    user_id=user.id,
                    amount=codes_count_for_threshold,
                    reason="generation",
                    reference_id=task.id,
                    description=f"Генерация {codes_count_for_threshold} этикеток (фоновая)",
                )
            except Exception as e:
                logger.error(f"[generate_from_excel] Ошибка списания баланса (async): {e}")

        # Оценка времени: ~0.1 сек/этикетку на проде
        estimated_seconds = int(codes_count_for_threshold * 0.1)

        logger.info(
            f"[generate_from_excel] Задача {task.id} отправлена в Celery ({codes_count_for_threshold} кодов)"
        )

        return LabelMergeResponse(
            success=True,
            labels_count=0,  # Пока не известно
            pages_count=0,
            label_format=format_enum,
            message=f"Задача отправлена на обработку ({codes_count_for_threshold} этикеток)",
            is_async=True,
            task_id=str(task.id),
            estimated_seconds=estimated_seconds,
            codes_count=codes_count_for_threshold,
            preflight=preflight_result,
        )

    # === SYNC MODE: Для небольших файлов продолжаем синхронную обработку ===

    # Парсим Excel
    excel_parser = ExcelBarcodeParser()
    try:
        excel_data = excel_parser.parse(
            excel_bytes=excel_bytes,
            filename=barcodes_excel.filename or "barcodes.xlsx",
            column_name=barcode_column,
        )
    except ValueError as e:
        return LabelMergeResponse(
            success=False,
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            message=f"Ошибка чтения Excel: {str(e)}",
        )

    # === ФАЗА 3.7: Автоподтягивание данных из базы карточек ===
    # Получаем все баркоды из Excel для поиска в базе
    excel_barcodes = [item.barcode for item in excel_data.items if item.barcode]

    # Определяем пользователя для работы с карточками
    product_user = user
    if not product_user and user_telegram_id:
        product_user = await user_repo.get_by_telegram_id(user_telegram_id)

    # Словарь существующих карточек: barcode -> ProductCard
    products_map: dict[str, ProductCard] = {}
    if product_user and excel_barcodes:
        from app.db.models import UserPlan

        # Проверяем доступ к базе карточек (только PRO и ENTERPRISE)
        if product_user.plan in (UserPlan.PRO, UserPlan.ENTERPRISE):
            existing_products = await product_repo.get_by_barcodes(product_user.id, excel_barcodes)
            products_map = {p.barcode: p for p in existing_products}
            if products_map:
                logger.info(f"[generate_from_excel] Найдено {len(products_map)} карточек в базе")

    # Преобразуем в LabelItem для нового генератора
    # Обогащаем данными из базы карточек если есть
    label_items: list[LabelItem] = []
    for item in excel_data.items:
        # Ищем карточку в базе
        saved_product = products_map.get(item.barcode)

        # Данные из Excel имеют приоритет, но если пусто — берём из базы
        label_items.append(
            LabelItem(
                barcode=item.barcode,
                article=item.article or (saved_product.article if saved_product else None),
                size=item.size or (saved_product.size if saved_product else None) or fallback_size,
                color=item.color
                or (saved_product.color if saved_product else None)
                or fallback_color,
                name=item.name or (saved_product.name if saved_product else None),
                brand=getattr(item, "brand", None)
                or (saved_product.brand if saved_product else None),
                country=item.country or (saved_product.country if saved_product else None),
                composition=item.composition
                or (saved_product.composition if saved_product else None),
                # Дополнительные поля для professional шаблона
                manufacturer=getattr(item, "manufacturer", None)
                or (saved_product.manufacturer if saved_product else None),
                production_date=getattr(item, "production_date", None)
                or (saved_product.production_date if saved_product else None),
                importer=getattr(item, "importer", None)
                or (saved_product.importer if saved_product else None),
                certificate_number=getattr(item, "certificate_number", None)
                or (saved_product.certificate_number if saved_product else None),
                address=getattr(item, "address", None)
                or (saved_product.address if saved_product else None),
            )
        )

    # === НУМЕРАЦИЯ: подготовка start_number для режима "continue" ===
    # Валидация: start_number должен быть >= 1
    if start_number is not None and start_number < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_number должен быть >= 1",
        )
    effective_start_number = start_number or 1
    if numbering_mode == "continue" and start_number is None and products_map:
        # Находим максимальный last_serial_number из карточек товаров
        max_serial = max(
            (p.last_serial_number for p in products_map.values() if p.last_serial_number),
            default=0,
        )
        effective_start_number = max_serial + 1
    elif numbering_mode == "continue" and start_number is None:
        effective_start_number = 1

    logger.info(
        f"[generate_from_excel] Нумерация: mode={numbering_mode}, start_number={effective_start_number}"
    )

    # GTIN matching: количество этикеток = количество кодов ЧЗ
    # Матчинг товаров и ЧЗ по GTIN происходит в label_generator._match_items_with_codes()
    # 1 товар в Excel + 5 ЧЗ с этим GTIN = 5 этикеток
    codes_count_total = len(codes_list)
    total_count = codes_count_total
    if total_count == 0:
        return LabelMergeResponse(
            success=False,
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            message="Нет данных для генерации",
        )

    # Применяем диапазон ("Ножницы")
    start_idx = 0
    end_idx = total_count
    if range_start is not None and range_end is not None:
        # Валидация диапазона
        if range_start < 1:
            range_start = 1
        if range_end > total_count:
            range_end = total_count
        if range_start > range_end:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                pages_count=0,
                label_format=format_enum,
                message=f"Неверный диапазон: {range_start}-{range_end}",
            )
        start_idx = range_start - 1  # 1-based → 0-based
        end_idx = range_end

    # Slice данных по диапазону
    # При GTIN matching: 1 товар в Excel может соответствовать N кодам ЧЗ
    # Количество этикеток определяется по кодам ЧЗ (не по Excel строкам)
    # label_items НЕ slice'им — все товары нужны для матчинга по GTIN
    codes_list = codes_list[start_idx:end_idx]
    actual_count = len(codes_list)  # Количество этикеток = количество кодов ЧЗ

    # Pre-flight проверка уже выполнена перед async decision (первый и последний код)
    # preflight_result доступен из проверки выше

    if preflight_result and not preflight_result.can_proceed:
        return LabelMergeResponse(
            success=False,
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            preflight=preflight_result,
            message="Pre-flight проверка не пройдена",
        )

    # Генерируем этикетки через новый ReportLab генератор
    label_generator = LabelGenerator()

    # Парсим кастомные строки для extended шаблона
    custom_lines_list: list[str] | None = None
    if custom_lines:
        try:
            custom_lines_list = json_module.loads(custom_lines)
            if not isinstance(custom_lines_list, list):
                custom_lines_list = None
        except (json_module.JSONDecodeError, TypeError):
            custom_lines_list = None

    # Парсим ручной маппинг GTIN → индекс товара
    gtin_mapping_dict: dict[str, int] | None = None
    if manual_gtin_mapping:
        try:
            gtin_mapping_dict = json_module.loads(manual_gtin_mapping)
            if not isinstance(gtin_mapping_dict, dict):
                gtin_mapping_dict = None
            else:
                logger.info(f"[generate_from_excel] Ручной маппинг GTIN: {gtin_mapping_dict}")
        except (json_module.JSONDecodeError, TypeError):
            gtin_mapping_dict = None

    # === Обратная совместимость: show_size_color → show_size + show_color ===
    # Если передан deprecated show_size_color, применяем его к обоим полям
    effective_show_size = show_size
    effective_show_color = show_color
    if show_size_color is not None:
        effective_show_size = show_size_color
        effective_show_color = show_size_color
        logger.info(
            f"[generate_from_excel] Deprecated show_size_color={show_size_color} → "
            f"show_size={effective_show_size}, show_color={effective_show_color}"
        )

    # Диагностика: логируем параметры перед вызовом генератора
    logger.info(
        f"[generate_from_excel] Вызов генератора: layout={layout_enum.value}, show_inn={show_inn}, inn={inn!r}, "
        f"show_organization={show_organization}, organization={organization_name!r}, custom_lines={custom_lines_list}, "
        f"show_size={effective_show_size}, show_color={effective_show_color}"
    )

    # === ПРИОРИТЕТ ПОЛЕЙ: Автообрезка до лимита шаблона ===
    # Вместо ошибки при превышении лимита — автоматически обрезаем поля по приоритету
    # Собираем информацию о заполненных полях из первого товара
    effective_show_fields = {
        "name": show_name,
        "article": show_article,
        "size": effective_show_size,
        "color": effective_show_color,
        "brand": show_brand,
        "composition": show_composition,
        "country": show_country,
        "manufacturer": show_manufacturer,
        "importer": show_importer,
        "production_date": show_production_date,
        "certificate": show_certificate,
    }

    if label_items:
        first_item = label_items[0]
        # Какие поля реально заполнены в Excel
        filled_fields_dict = {
            "name": bool(first_item.name),
            "article": bool(first_item.article),
            "size": bool(first_item.size),
            "color": bool(first_item.color),
            "brand": bool(first_item.brand),
            "composition": bool(first_item.composition),
            "country": bool(first_item.country),
            "manufacturer": bool(first_item.manufacturer),
            "importer": bool(first_item.importer),
            "production_date": bool(first_item.production_date),
            "certificate": bool(first_item.certificate_number),
        }

        # Получаем приоритет полей из настроек пользователя (PRO/ENT) или дефолтный
        user_field_priority = None
        if user and user.field_priority:
            user_field_priority = user.field_priority

        # Фильтруем поля по приоритету до лимита шаблона
        filtered_fields = filter_fields_by_priority(
            layout=layout_enum.value,
            template=size_enum.value,
            filled_fields=filled_fields_dict,
            field_priority=user_field_priority,
        )

        # Обновляем show_* флаги на основе фильтрации
        # Поле показываем только если: оно заполнено И прошло фильтр по приоритету
        effective_show_fields = {
            field: filtered_fields.get(field, False) for field in effective_show_fields
        }

        logger.info(
            f"[generate_from_excel] Field priority filter: "
            f"filled={sum(filled_fields_dict.values())}, "
            f"after_filter={sum(effective_show_fields.values())}, "
            f"layout={layout_enum.value}, size={size_enum.value}"
        )

    # Распаковываем отфильтрованные флаги
    show_name = effective_show_fields["name"]
    show_article = effective_show_fields["article"]
    effective_show_size = effective_show_fields["size"]
    effective_show_color = effective_show_fields["color"]
    show_brand = effective_show_fields["brand"]
    show_composition = effective_show_fields["composition"]
    show_country = effective_show_fields["country"]
    show_manufacturer = effective_show_fields["manufacturer"]
    show_importer = effective_show_fields["importer"]
    show_production_date = effective_show_fields["production_date"]
    show_certificate = effective_show_fields["certificate"]

    # === PREFLIGHT ПРОВЕРКА (skip_on_preflight_error) ===
    # Если skip_on_preflight_error=True — проверяем данные ПЕРЕД генерацией
    # и возвращаем ошибку без списания лимита
    if skip_on_preflight_error:
        preflight_layout_errors = label_generator.preflight_check(
            items=label_items,  # Все товары для проверки
            size=size_enum.value,
            organization=organization_name,
            layout=layout_enum.value,
            show_article=show_article,
            show_size=effective_show_size,
            show_color=effective_show_color,
            show_name=show_name,
            show_brand=show_brand,
            show_composition=show_composition,
            show_country=show_country,
            show_importer=show_importer,
            show_manufacturer=show_manufacturer,
            show_address=show_address,
            show_production_date=show_production_date,
            show_certificate=show_certificate,
            organization_address=organization_address,
            importer=importer,
            manufacturer=manufacturer,
            production_date=production_date,
            certificate_number=certificate_number,
            custom_lines=custom_lines_list,
        )

        if preflight_layout_errors:
            # Преобразуем в GenerationError для ответа
            generation_errors = [
                GenerationError(
                    field_id=err.field_id,
                    message=err.message,
                    suggestion=err.suggestion,
                )
                for err in preflight_layout_errors
            ]

            logger.warning(
                f"[generate_from_excel] Preflight errors: {len(preflight_layout_errors)} ошибок, "
                f"skip_on_preflight_error=True → НЕ генерируем"
            )

            return LabelMergeResponse(
                success=False,
                labels_count=0,
                pages_count=0,
                label_format=format_enum,
                message="Данные не прошли проверку. Исправьте ошибки и попробуйте снова.",
                generation_errors=generation_errors,
            )

    try:
        pdf_bytes = label_generator.generate(
            items=label_items,  # Все товары — матчинг по GTIN внутри _match_items_with_codes
            codes=codes_list,  # Уже slice'нут по диапазону
            size=size_enum.value,
            organization=organization_name,
            inn=inn,
            layout=layout_enum.value,
            label_format=label_format,
            show_article=show_article,
            show_size=effective_show_size,
            show_color=effective_show_color,
            show_name=show_name,
            show_organization=show_organization,
            show_inn=show_inn,
            show_country=show_country,
            show_composition=show_composition,
            show_chz_code_text=show_chz_code_text,
            numbering_mode=numbering_mode,
            start_number=effective_start_number,
            show_brand=show_brand,
            # Поля для professional шаблона
            show_importer=show_importer,
            show_manufacturer=show_manufacturer,
            show_address=show_address,
            show_production_date=show_production_date,
            show_certificate=show_certificate,
            # Реквизиты для professional шаблона
            organization_address=organization_address,
            importer=importer,
            manufacturer=manufacturer,
            production_date=production_date,
            certificate_number=certificate_number,
            # Кастомные строки для extended шаблона
            custom_lines=custom_lines_list,
            # Ручной маппинг GTIN → товар
            manual_gtin_mapping=gtin_mapping_dict,
        )
    except GtinMatchingException as e:
        # Ошибка матчинга GTIN — возвращаем детальную информацию для ручного матчинга
        return JSONResponse(
            status_code=422,
            content={
                "detail": str(e),
                "gtin_matching_error": {
                    "message": str(e),
                    "extracted_gtins": e.extracted_gtins,
                    "excel_items": e.excel_items,
                    "can_manual_match": e.can_manual_match,
                },
            },
        )
    except Exception as e:
        return LabelMergeResponse(
            success=False,
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            message=f"Ошибка генерации PDF: {str(e)}",
        )

    # Количество страниц = количеству этикеток (объединённый формат)
    pages_count = actual_count

    # Сохраняем файл во временное хранилище (Redis)
    file_id = str(uuid4())
    await get_file_storage(redis).save(
        file_id=file_id,
        data=pdf_bytes,
        filename="labels.pdf",
        content_type="application/pdf",
        ttl_seconds=3600,
    )

    # Определяем результат preflight
    preflight_ok = True
    if preflight_result:
        preflight_ok = preflight_result.overall_status.value != "error"

    # Сохраняем в историю
    generation_user = user
    if not generation_user and user_telegram_id:
        generation_user = await user_repo.get_by_telegram_id(user_telegram_id)

    if generation_user:
        user_dir = Path("data/generations") / str(generation_user.id)
        user_dir.mkdir(parents=True, exist_ok=True)

        gen_file_id = uuid4()
        file_path = user_dir / f"{gen_file_id}.pdf"
        file_path.write_bytes(pdf_bytes)

        file_hash = hashlib.sha256(pdf_bytes).hexdigest()

        from app.db.models import UserPlan

        if generation_user.plan == UserPlan.ENTERPRISE:
            expires_days = 30
        elif generation_user.plan == UserPlan.PRO:
            expires_days = 7
        else:
            expires_days = None

        if expires_days is not None:
            generation = await gen_repo.create(
                user_id=generation_user.id,
                labels_count=actual_count,
                preflight_passed=preflight_ok,
                file_path=str(file_path),
                file_hash=file_hash,
                file_size_bytes=len(pdf_bytes),
                expires_days=expires_days,
            )
            file_id = str(generation.id)

        await usage_repo.record_usage(
            user_id=generation_user.id,
            labels_count=actual_count,
            preflight_status="ok" if preflight_ok else "error",
        )

        # Списываем баланс для PRO
        if generation_user.plan == UserPlan.PRO:
            try:
                await label_balance_service.debit_labels(
                    user_id=generation_user.id,
                    amount=actual_count,
                    reason="generation",
                    reference_id=gen_file_id,
                    description=f"Генерация {actual_count} этикеток",
                )
            except Exception as e:
                logger.error(f"[generate_from_excel] Ошибка списания баланса (sync): {e}")

        # === АВТОСОХРАНЕНИЕ КАРТОЧЕК ===

        # Сохраняем товары в базу карточек (только PRO/ENTERPRISE)
        # Логирование результата внутри _autosave_products
        await _autosave_products(
            user=generation_user,
            label_items=label_items,
            product_repo=product_repo,
        )

        # === СОХРАНЕНИЕ last_serial_number ===
        # Обновляем last_serial_number в карточках товаров (кроме режима "none")
        # ИЗВЕСТНЫЕ ОГРАНИЧЕНИЯ:
        # - Race condition: параллельные запросы в режиме "continue" могут получить
        #   одинаковый max_serial. Для единственного пользователя это маловероятно.
        # - Sequential mode сохраняет позицию последнего вхождения баркода,
        #   а не общий счётчик. Для продолжения нумерации используйте mode="continue".
        # Сохраняем last_serial_number только для режимов "per_product" и "continue"
        # Режим "sequential" — разовая нумерация 1-N, продолжение не предусмотрено
        if (
            numbering_mode in ("per_product", "continue")
            and products_map
            and generation_user.plan in (UserPlan.PRO, UserPlan.ENTERPRISE)
        ):
            # Считаем финальные номера для каждого баркода
            # При GTIN matching: извлекаем barcode из codes_list по GTIN
            final_serials: dict[str, int] = {}

            # Helper: извлечь barcode из кода ЧЗ по GTIN
            def extract_barcode_from_code(code: str) -> str | None:
                """GTIN (01 + 14 цифр) → EAN-13 barcode (без ведущего 0)."""
                if code.startswith("01") and len(code) >= 16:
                    gtin = code[2:16]
                    barcode = gtin.lstrip("0")
                    # Проверяем наличие в products_map
                    if barcode in products_map:
                        return barcode
                    if gtin in products_map:
                        return gtin
                return None

            if numbering_mode == "per_product":
                # По товару: считаем количество каждого баркода по GTIN из кодов
                barcode_counts: Counter[str] = Counter()
                for code in codes_list:
                    barcode = extract_barcode_from_code(code)
                    if barcode:
                        barcode_counts[barcode] += 1
                final_serials = dict(barcode_counts)

            elif numbering_mode == "continue":
                # Продолжение: для каждого баркода сохраняем его финальный номер
                barcode_last_positions: dict[str, int] = {}
                for idx, code in enumerate(codes_list):
                    barcode = extract_barcode_from_code(code)
                    if barcode:
                        barcode_last_positions[barcode] = idx

                # Финальный номер = start_number + позиция последнего появления
                for barcode, last_idx in barcode_last_positions.items():
                    final_serials[barcode] = effective_start_number + last_idx

            # Обновляем карточки в БД
            for barcode, last_serial in final_serials.items():
                try:
                    await product_repo.update_serial(generation_user.id, barcode, last_serial)
                    logger.info(
                        f"[generate_from_excel] Обновлён last_serial_number: {barcode} -> {last_serial}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[generate_from_excel] Не удалось обновить serial: {barcode}, {e}"
                    )
    else:
        try:
            await record_user_usage_db(
                user_telegram_id, actual_count, preflight_ok, user_repo, usage_repo
            )
        except Exception:
            record_user_usage_fallback(user_telegram_id, actual_count, preflight_ok)

    layout_name = {"basic": "Базовый", "professional": "Профессиональный"}.get(layout, layout)

    # Получаем актуальные лимиты для ответа (после списания)
    limit_info = await usage_repo.check_limit(
        user=generation_user or user,  # type: ignore
        labels_count=0,
    )
    response_daily_limit = limit_info.get("limit", 50)
    response_used_today = limit_info.get("used_period", 0)

    # Информация о матчинге

    unique_products_count = len(set(excel_barcodes))
    codes_total_count = len(codes_list)

    return LabelMergeResponse(
        success=True,
        labels_count=actual_count,
        pages_count=pages_count,
        label_format=format_enum,
        preflight=preflight_result,
        file_id=file_id,
        download_url=f"/api/v1/labels/download/{file_id}",
        message=f"Сгенерировано {actual_count} этикеток (layout: {layout_name})",
        daily_limit=response_daily_limit,
        used_today=response_used_today,
        unique_products=unique_products_count,
        codes_count=codes_total_count,
    )


@router.get(
    "/labels/download/{file_id}",
    response_class=StreamingResponse,
    summary="Скачать сгенерированный PDF",
)
async def download_pdf(
    file_id: str,
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
    redis: Redis = Depends(get_redis),
) -> StreamingResponse:
    """
    Скачать сгенерированный PDF по ID.

    Args:
        file_id: Идентификатор файла из ответа merge (UUID или временный ID)

    Returns:
        PDF файл для скачивания
    """
    # Сначала проверяем временное хранилище (Redis)
    stored = await get_file_storage(redis).get(file_id)
    if stored is not None:
        return StreamingResponse(
            io.BytesIO(stored.data),
            media_type=stored.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{stored.filename}"',
            },
        )

    # Пробуем найти в БД по generation ID
    try:
        from uuid import UUID

        gen_id = UUID(file_id)
        generation = await gen_repo.get_by_id(gen_id)
        if generation and generation.file_path:
            # Path Traversal защита: null bytes, traversal sequences, абсолютные пути
            raw_path = generation.file_path
            if (
                "\x00" in raw_path  # Null byte injection
                or ".." in raw_path  # Directory traversal
                or raw_path.startswith("/")  # Unix absolute path
                or raw_path.startswith("\\")  # Windows UNC path (\\server\share)
                or (len(raw_path) > 1 and raw_path[1] == ":")  # Windows absolute path (C:\)
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недопустимый путь к файлу",
                )
            # Проверяем что файл внутри разрешённой директории
            file_path = Path(generation.file_path).resolve()
            if not file_path.is_relative_to(ALLOWED_DIR):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Доступ запрещён",
                )
            if file_path.exists():
                pdf_bytes = file_path.read_bytes()
                return StreamingResponse(
                    io.BytesIO(pdf_bytes),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="labels_{file_id}.pdf"',
                    },
                )
    except (ValueError, TypeError):
        pass  # Невалидный UUID, файл не в БД

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Файл не найден или срок хранения истёк",
    )


# === Новые endpoint'ы для режимов "Только ЧЗ" и "Только WB" ===


@router.post("/labels/generate-chz", response_model=LabelMergeResponse)
async def generate_chz_labels(
    csv_file: UploadFile = File(..., description="CSV файл с кодами ЧЗ"),
    label_size: str = Form("58x40", description="Размер этикетки: 58x40"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Генерация этикеток только с кодами Честного знака.

    Бесплатно для всех тарифов, без списания баланса.
    """
    # Парсинг CSV
    content = await csv_file.read()
    parser = ChzCsvParser()
    result = parser.parse_bytes(content)

    if not result.success or len(result.codes) == 0:
        error_msg = result.errors[0] if result.errors else "Не найдено валидных кодов маркировки"
        raise HTTPException(status_code=400, detail=error_msg)

    # Лимит на количество кодов по тарифу
    max_codes_by_plan = {
        UserPlan.FREE: 5000,
        UserPlan.PRO: 30000,
        UserPlan.ENTERPRISE: 100000,
    }
    max_codes = max_codes_by_plan.get(current_user.plan, 5000)

    if len(result.codes) > max_codes:
        raise HTTPException(
            status_code=400,
            detail=f"Превышен лимит: {len(result.codes)} кодов, максимум {max_codes} для тарифа {current_user.plan.value}",
        )

    # Генерация PDF
    from uuid import uuid4

    from app.services.label_generator import LabelGenerator

    generator = LabelGenerator()
    pdf_bytes = generator.generate_chz_only(
        codes=result.codes,
        label_size=label_size,
    )

    # Сохранение файла в Redis
    file_id = str(uuid4())
    await redis.setex(
        f"label_file:{file_id}",
        3600,  # 1 час
        pdf_bytes,
    )

    # Запись статистики (без списания баланса)
    gen_repo = GenerationRepository(db)
    await gen_repo.create(
        user_id=current_user.id,
        labels_count=len(result.codes),
        file_path=f"redis://{file_id}",
    )

    return LabelMergeResponse(
        success=True,
        labels_count=len(result.codes),
        pages_count=len(result.codes),
        download_url=f"/api/v1/labels/download/{file_id}",
        file_id=file_id,
    )


@router.post("/labels/generate-wb", response_model=LabelMergeResponse)
async def generate_wb_labels(
    request_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Генерация этикеток только для Wildberries.

    Бесплатно для всех тарифов, без списания баланса.
    """
    items = request_data.get("items", [])
    label_size = request_data.get("label_size", "58x40")
    show_fields = request_data.get("show_fields", {"barcode": True})

    if not items:
        raise HTTPException(status_code=400, detail="Нет товаров для генерации")

    # Лимит на количество товаров по тарифу
    max_items_by_plan = {
        UserPlan.FREE: 1000,
        UserPlan.PRO: 10000,
        UserPlan.ENTERPRISE: 100000,
    }
    max_items = max_items_by_plan.get(current_user.plan, 1000)

    if len(items) > max_items:
        raise HTTPException(
            status_code=400, detail=f"Превышен лимит: {len(items)} товаров, максимум {max_items}"
        )

    # Подсчёт общего количества этикеток
    total_labels = sum(item.get("quantity", 1) or 1 for item in items)

    # Генерация PDF
    from uuid import uuid4

    from app.services.label_generator import LabelGenerator

    generator = LabelGenerator()
    pdf_bytes = generator.generate_wb_only(
        items=items,
        label_size=label_size,
        show_fields=show_fields,
    )

    # Сохранение файла в Redis
    file_id = str(uuid4())
    await redis.setex(
        f"label_file:{file_id}",
        3600,  # 1 час
        pdf_bytes,
    )

    # Запись статистики (без списания баланса)
    gen_repo = GenerationRepository(db)
    await gen_repo.create(
        user_id=current_user.id,
        labels_count=total_labels,
        file_path=f"redis://{file_id}",
    )

    return LabelMergeResponse(
        success=True,
        labels_count=total_labels,
        pages_count=total_labels,
        download_url=f"/api/v1/labels/download/{file_id}",
        file_id=file_id,
    )
