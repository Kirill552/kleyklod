"""
API эндпоинты для работы с этикетками.

Основной функционал: объединение WB + ЧЗ.
"""

import hashlib
import io
import json
import logging
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import LABEL, get_settings
from app.db.database import get_db
from app.db.models import User
from app.models.schemas import (
    CountMismatchInfo,
    ErrorResponse,
    ExcelParseResponse,
    ExcelSampleItem,
    FileDetectionResponse,
    FileType,
    LabelFormat,
    LabelMergeResponse,
    LabelTemplate,
    PreflightResponse,
    PreflightResult,
    PreflightStatus,
    TemplatesResponse,
)
from app.repositories import GenerationRepository, UsageRepository, UserRepository
from app.services.auth import decode_access_token
from app.services.code_history import CodeHistoryService
from app.services.file_storage import file_storage
from app.services.merger import LabelMerger
from app.services.preflight import PreflightChecker

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# Безопасная работа с файлами — защита от Path Traversal
ALLOWED_DIR = Path("data/generations").resolve()

# Допустимые MIME-типы для файлов с кодами ЧЗ
ALLOWED_CODES_TYPES = [
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "application/pdf",  # Теперь поддерживаем PDF с DataMatrix
]


def _is_pdf_codes_file(filename: str, content_type: str | None) -> bool:
    """Определяет, является ли файл PDF с кодами."""
    return content_type == "application/pdf" or (filename and filename.lower().endswith(".pdf"))


def parse_codes_from_file(file_bytes: bytes, filename: str) -> list[str]:
    """
    Универсальный парсер кодов ЧЗ из файла.

    Поддерживает: CSV, Excel (.xlsx, .xls), PDF с DataMatrix.

    Args:
        file_bytes: Содержимое файла
        filename: Имя файла (для определения формата)

    Returns:
        Список кодов DataMatrix

    Raises:
        ValueError: Если не удалось извлечь коды
    """
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext == "pdf":
        # PDF — извлекаем DataMatrix коды
        from app.services.pdf_parser import PDFParser

        pdf_parser = PDFParser()
        result = pdf_parser.extract_codes(file_bytes)
        return result.codes
    else:
        # CSV/Excel — используем CSVParser
        from app.services.csv_parser import CSVParser

        csv_parser = CSVParser()
        result = csv_parser.parse(file_bytes, filename)
        return result.codes


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
        pro_limit=500,
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
    summary="Автодетект типа файла (PDF или Excel)",
    description="""
**Определяет тип загруженного файла и возвращает информацию о нём.**

Используется для автоматического определения workflow:
- **PDF** → старый режим (WB PDF + коды ЧЗ)
- **Excel** → новый режим (Excel с баркодами + коды ЧЗ)

**Возвращает:**
- Для PDF: количество страниц
- Для Excel: колонки, количество строк, примеры данных
- Для неизвестного формата: сообщение об ошибке

**Поддерживаемые форматы:**
- PDF (.pdf)
- Excel (.xlsx, .xls)
""",
)
async def detect_file_type(
    file: Annotated[UploadFile, File(description="Файл для определения типа (PDF или Excel)")],
) -> FileDetectionResponse:
    """
    Автодетект типа файла.

    Позволяет фронтенду определить какой workflow использовать:
    - PDF → merge_labels (старый режим)
    - Excel → generate_from_excel (новый режим)
    """
    from app.services.excel_parser import ExcelBarcodeParser
    from app.services.pdf_parser import PDFParser

    # Валидация размера файла
    if file.size and file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    content = await file.read()
    filename = file.filename or "unknown"
    size_bytes = len(content)

    # Проверяем PDF
    if filename.lower().endswith(".pdf") or content[:4] == b"%PDF":
        try:
            pdf_parser = PDFParser()
            pages_count = pdf_parser.get_page_count(content)
            return FileDetectionResponse(
                file_type=FileType.PDF,
                filename=filename,
                size_bytes=size_bytes,
                pages_count=pages_count,
            )
        except Exception as e:
            return FileDetectionResponse(
                file_type=FileType.UNKNOWN,
                filename=filename,
                size_bytes=size_bytes,
                error=f"Не удалось прочитать PDF: {str(e)}",
            )

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
        error="Поддерживаются только PDF и Excel (.xlsx, .xls) файлы",
    )


@router.post(
    "/labels/merge",
    response_model=LabelMergeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные входные данные"},
        403: {"model": ErrorResponse, "description": "Превышен лимит"},
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
        422: {"model": ErrorResponse, "description": "Ошибка валидации"},
    },
    summary="Объединить этикетки WB и ЧЗ",
    description="""
Основной эндпоинт для объединения этикеток Wildberries и кодов маркировки Честного Знака.

**Входные данные:**
- `wb_pdf` — PDF файл с этикетками от Wildberries
- `codes_file` — CSV/Excel файл с кодами DataMatrix от Честного Знака
- `template` — Шаблон этикетки (58x40, 58x30, 58x60)
- `run_preflight` — Выполнять проверку качества (по умолчанию: да)
- `label_format` — Формат этикеток: combined (на одной) или separate (раздельные)
- `range_start` — Начало диапазона печати (1-based, включительно)
- `range_end` — Конец диапазона печати (1-based, включительно)
- `telegram_id` — ID пользователя Telegram (для учёта лимитов)

**Форматы этикеток:**
- `combined` (по умолчанию) — WB + DataMatrix на одной этикетке 58x40мм
- `separate` — WB и DataMatrix на отдельных этикетках (чередование: WB1, DM1, WB2, DM2...)

**Диапазон печати ("Ножницы"):**
Если указаны range_start и range_end, будут сгенерированы только этикетки в этом диапазоне.
Например: range_start=10, range_end=20 → этикетки с 10 по 20 (11 штук).

**Лимиты:**
- Free: 50 этикеток/день
- Pro: 500 этикеток/день
- Enterprise: безлимит

**Результат:**
- PDF файл с объединёнными этикетками размером 58x40мм
- Готов к печати на термопринтере с разрешением 203 DPI
    """,
)
async def merge_labels(
    wb_pdf: Annotated[UploadFile, File(description="PDF с этикетками Wildberries")],
    codes_file: Annotated[UploadFile | None, File(description="CSV/Excel с кодами ЧЗ")] = None,
    codes: Annotated[str | None, Form(description="JSON массив кодов")] = None,
    template: Annotated[str, Form(description="Шаблон этикетки")] = "58x40",
    run_preflight: Annotated[bool, Form(description="Выполнять проверку качества")] = True,
    label_format: Annotated[str, Form(description="Формат: combined или separate")] = "combined",
    range_start: Annotated[int | None, Form(description="Начало диапазона (1-based)")] = None,
    range_end: Annotated[int | None, Form(description="Конец диапазона (1-based)")] = None,
    telegram_id: Annotated[int | None, Form(description="Telegram ID (для бота)")] = None,
    skip_duplicate_check: Annotated[
        bool, Form(description="Пропустить проверку дубликатов")
    ] = False,
    current_user: User | None = Depends(get_current_user_optional),
    user_repo: UserRepository = Depends(_get_user_repo),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
    code_history: CodeHistoryService = Depends(_get_code_history),
) -> LabelMergeResponse:
    """
    Объединение этикеток WB и кодов ЧЗ в один PDF.

    Основной workflow:
    1. Проверка лимитов пользователя
    2. Парсинг PDF от Wildberries (извлечение изображений этикеток)
    3. Парсинг CSV/Excel с кодами DataMatrix
    4. Генерация DataMatrix для каждого кода
    5. Проверка качества (размер, контраст, quiet zone)
    6. Объединение WB штрихкода и DataMatrix на одной этикетке
    7. Генерация итогового PDF
    8. Запись использования

    Args:
        wb_pdf: PDF файл с этикетками WB
        codes_file: CSV/Excel файл с кодами ЧЗ
        template: Шаблон этикетки
        run_preflight: Выполнять ли проверку качества
        telegram_id: ID пользователя Telegram для учёта лимитов

    Returns:
        LabelMergeResponse с результатом и ссылкой на скачивание
    """
    # Определяем пользователя: JWT приоритетнее telegram_id
    user = current_user
    user_telegram_id = telegram_id

    if user:
        user_telegram_id = int(user.telegram_id) if user.telegram_id else None

    # Валидация размера PDF
    if wb_pdf.size and wb_pdf.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF файл слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    # Валидация типа PDF
    if wb_pdf.content_type not in ["application/pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл WB должен быть в формате PDF",
        )

    # Определяем источник кодов: JSON или файл
    codes_list: list[str] = []
    codes_bytes: bytes | None = None
    codes_filename: str = "codes.json"

    if codes:
        # Парсим JSON массив кодов
        try:
            codes_list = json.loads(codes)
            if not isinstance(codes_list, list):
                raise ValueError("codes должен быть массивом")
            codes_list = [str(c).strip() for c in codes_list if c]
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невалидный JSON в параметре codes",
            )
    elif codes_file:
        # Валидация файла с кодами
        if codes_file.size and codes_file.size > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файл кодов слишком большой. Максимум: {settings.max_upload_size_mb}MB",
            )

        if codes_file.content_type not in ALLOWED_CODES_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл кодов должен быть в формате CSV, Excel или PDF",
            )

        codes_bytes = await codes_file.read()
        codes_filename = codes_file.filename or "codes.csv"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите codes (JSON) или codes_file (файл)",
        )

    # Читаем PDF
    wb_pdf_bytes = await wb_pdf.read()

    # Создаём сервис объединения
    merger = LabelMerger()

    try:
        # Получаем количество этикеток для проверки лимита
        from app.services.pdf_parser import PDFParser

        pdf_parser = PDFParser()
        labels_count = pdf_parser.get_page_count(wb_pdf_bytes)

        # Проверяем лимит пользователя
        if user:
            # Проверка через User объект
            limit_result = await usage_repo.check_limit(
                user=user,
                labels_count=labels_count,
                free_limit=settings.free_tier_daily_limit,
                pro_limit=500,
            )
            allowed = limit_result["allowed"]
            limit_message = (
                f"использовано {limit_result['used_today']}/{limit_result['daily_limit']}"
                if not allowed
                else "OK"
            )
        else:
            # Fallback на telegram_id
            try:
                allowed, limit_message, _ = await check_user_limit_db(
                    user_telegram_id, labels_count, user_repo, usage_repo
                )
            except Exception:
                allowed, limit_message, _ = check_user_limit_fallback(
                    user_telegram_id, labels_count
                )

        if not allowed:
            # Проверяем, истёк ли trial период
            trial_expired = limit_result.get("trial_expired", False) if user else False
            if trial_expired:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Trial период закончился. Оформите подписку PRO или ENTERPRISE для продолжения работы.",
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Превышен дневной лимит: {limit_message}. "
                f"Оформите Pro подписку для увеличения лимита.",
            )

        # Выполняем объединение
        if codes_list:
            # Коды из JSON — передаём как строку CSV
            codes_bytes = "\n".join(codes_list).encode("utf-8")
            codes_filename = "codes.csv"
        else:
            # Парсим коды из файла (CSV, Excel или PDF)
            try:
                codes_list = parse_codes_from_file(codes_bytes, codes_filename)
            except ValueError:
                codes_list = []

        # Определяем пользователя для проверки дубликатов
        check_user = user
        if not check_user and user_telegram_id:
            check_user = await user_repo.get_by_telegram_id(user_telegram_id)

        # Проверка дубликатов кодов (только для авторизованных пользователей)
        duplicate_warning: str | None = None
        duplicate_count = 0

        if check_user and codes_list and not skip_duplicate_check:
            dup_result = await code_history.check_duplicates(check_user.id, codes_list)
            if dup_result.has_duplicates:
                duplicate_warning = dup_result.warning_message
                duplicate_count = dup_result.duplicate_count

        result = await merger.merge(
            wb_pdf_bytes=wb_pdf_bytes,
            codes_bytes=codes_bytes,
            codes_filename=codes_filename,
            template=template,
            run_preflight=run_preflight,
            label_format=label_format,
            range_start=range_start,
            range_end=range_end,
        )

        # Определяем результат preflight
        preflight_ok = True
        if result.preflight:
            preflight_ok = result.preflight.overall_status.value != "error"

        # Если нет JWT пользователя, но есть telegram_id — находим пользователя по нему
        generation_user = user
        if not generation_user and user_telegram_id:
            generation_user = await user_repo.get_by_telegram_id(user_telegram_id)

        # Сохраняем файл и запись в БД если есть пользователь (JWT или telegram_id)
        if generation_user and result.success and result.file_id:
            # Получаем PDF bytes из временного хранилища
            stored_file = file_storage.get(result.file_id)
            if stored_file:
                pdf_bytes = stored_file.data

                # Создаём директорию для файлов пользователя
                user_dir = Path("data/generations") / str(generation_user.id)
                user_dir.mkdir(parents=True, exist_ok=True)

                # Генерируем имя файла
                from uuid import uuid4

                gen_file_id = uuid4()
                file_path = user_dir / f"{gen_file_id}.pdf"

                # Сохраняем файл
                file_path.write_bytes(pdf_bytes)

                # Вычисляем хеш
                file_hash = hashlib.sha256(pdf_bytes).hexdigest()

                # Определяем срок хранения по тарифу
                # Free: не сохраняем, Pro: 7 дней, Enterprise: 30 дней
                from app.db.models import UserPlan

                if generation_user.plan == UserPlan.ENTERPRISE:
                    expires_days = 30
                elif generation_user.plan == UserPlan.PRO:
                    expires_days = 7
                else:
                    expires_days = None  # Free — не сохраняем

                # Создаём запись в БД только для платных тарифов
                if expires_days is not None:
                    generation = await gen_repo.create(
                        user_id=generation_user.id,
                        labels_count=labels_count,
                        preflight_passed=preflight_ok,
                        file_path=str(file_path),
                        file_hash=file_hash,
                        file_size_bytes=len(pdf_bytes),
                        expires_days=expires_days,
                    )
                    # Обновляем file_id в ответе для скачивания из истории
                    result.file_id = str(generation.id)

        # Записываем использование
        if generation_user:
            await usage_repo.record_usage(
                user_id=generation_user.id,
                labels_count=labels_count,
                preflight_status="ok" if preflight_ok else "error",
            )

            # Сохраняем использованные коды для проверки дубликатов
            if codes_list and result.success:
                await code_history.save_usage(
                    user_id=generation_user.id,
                    codes=codes_list,
                    generation_id=None,  # TODO: передать generation.id если создали
                )

            # Получаем актуальную информацию о лимитах после записи
            updated_limit = await usage_repo.check_limit(
                user=generation_user,
                labels_count=0,  # Просто получаем текущее состояние
                free_limit=settings.free_tier_daily_limit,
                pro_limit=500,
            )
            result.daily_limit = updated_limit["daily_limit"]
            result.used_today = updated_limit["used_today"]
        else:
            # Fallback для анонимных пользователей
            try:
                await record_user_usage_db(
                    user_telegram_id, labels_count, preflight_ok, user_repo, usage_repo
                )
            except Exception:
                record_user_usage_fallback(user_telegram_id, labels_count, preflight_ok)

            # Для анонимных пользователей — стандартный лимит
            result.daily_limit = settings.free_tier_daily_limit
            result.used_today = labels_count

        # Добавляем информацию о дубликатах
        result.duplicate_warning = duplicate_warning
        result.duplicate_count = duplicate_count

        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при объединении этикеток: {str(e)}",
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
    codes_file: Annotated[UploadFile, File(description="CSV/Excel с кодами Честного Знака")],
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
            codes_filename=codes_file.filename or "codes.csv",
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
    "/labels/generate-full",
    response_model=LabelMergeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные входные данные"},
        403: {"model": ErrorResponse, "description": "Превышен лимит"},
        413: {"model": ErrorResponse, "description": "Файл слишком большой"},
        422: {"model": ErrorResponse, "description": "Ошибка валидации"},
    },
    summary="Полная генерация: Excel с баркодами -> PDF с ЧЗ",
    description="""
**Полная генерация этикеток из Excel файла с баркодами Wildberries.**

Рекомендуемый workflow (human-in-the-loop):
1. Сначала вызвать `/labels/parse-excel` для анализа Excel файла
2. Показать пользователю preview и дать выбрать колонку с баркодами
3. После подтверждения вызвать этот endpoint с параметром `barcode_column`

**Входные данные:**
- `barcodes_excel` — Excel файл с баркодами WB
- `codes_file` — CSV/Excel с кодами DataMatrix от Честного Знака
- `barcode_column` — Название колонки с баркодами (опционально, если не указано — автоопределение)
- `template` — Шаблон этикетки (58x40, 58x30, 58x60)
- `run_preflight` — Выполнять проверку качества (по умолчанию: да)
- `label_format` — Формат этикеток: combined или separate

**Автоопределение колонки с баркодами:**
Если `barcode_column` не указан, парсер ищет колонку по названию:
- "Баркод", "Barcode", "Штрихкод", "ШК", "EAN", "EAN13"

Дополнительные колонки (опционально): Артикул, Размер, Цвет

**Пример Excel:**
| Баркод | Артикул | Размер |
|--------|---------|--------|
| 4601234567890 | ABC-001 | S |
| 4601234567891 | ABC-001 | M |

**Лимиты:**
- Free: 50 этикеток/день
- Pro: 500 этикеток/день
- Enterprise: безлимит

**Результат:**
- PDF файл с объединёнными этикетками размером 58x40мм
- Штрихкоды WB (EAN-13/Code128) + DataMatrix ЧЗ на одной этикетке
""",
)
async def generate_full(
    barcodes_excel: Annotated[UploadFile, File(description="Excel файл с баркодами Wildberries")],
    codes_file: Annotated[UploadFile, File(description="CSV/Excel с кодами Честного Знака")],
    barcode_column: Annotated[
        str | None, Form(description="Колонка с баркодами (если указана — использовать её)")
    ] = None,
    template: Annotated[str, Form(description="Шаблон этикетки")] = "58x40",
    run_preflight: Annotated[bool, Form(description="Выполнять проверку качества")] = True,
    label_format: Annotated[str, Form(description="Формат: combined или separate")] = "combined",
    range_start: Annotated[int | None, Form(description="Начало диапазона (1-based)")] = None,
    range_end: Annotated[int | None, Form(description="Конец диапазона (1-based)")] = None,
    force_generate: Annotated[
        bool, Form(description="Игнорировать несовпадение количества строк Excel и кодов ЧЗ")
    ] = False,
    telegram_id: Annotated[int | None, Form(description="Telegram ID (для бота)")] = None,
    current_user: User | None = Depends(get_current_user_optional),
    user_repo: UserRepository = Depends(_get_user_repo),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
) -> LabelMergeResponse:
    """
    Полная генерация этикеток: Excel с баркодами WB -> PDF с ЧЗ.

    Workflow:
    1. Парсинг Excel с баркодами WB (с учётом выбранной колонки)
    2. Генерация штрихкодов (EAN-13/Code128) для каждого баркода
    3. Парсинг CSV/Excel с кодами ЧЗ
    4. Генерация DataMatrix для каждого кода
    5. Объединение WB штрихкода и DataMatrix на одной этикетке
    6. Генерация итогового PDF

    Args:
        barcodes_excel: Excel файл с баркодами от WB
        codes_file: CSV/Excel файл с кодами ЧЗ
        barcode_column: Название колонки с баркодами (если указано — использовать её,
                       иначе автоопределение)
        template: Шаблон этикетки (58x40, 58x30, 58x60)
        run_preflight: Выполнять ли проверку качества
        label_format: Формат этикеток (combined/separate)
        telegram_id: ID пользователя Telegram для учёта лимитов

    Returns:
        LabelMergeResponse с результатом и ссылкой на скачивание
    """
    from uuid import uuid4

    from app.services.barcode_generator import BarcodeGenerator
    from app.services.excel_parser import ExcelBarcodeParser
    from app.services.pdf_parser import images_to_pdf

    # Определяем пользователя: JWT приоритетнее telegram_id
    user = current_user
    user_telegram_id = telegram_id

    if user:
        user_telegram_id = int(user.telegram_id) if user.telegram_id else None

    # Нормализуем label_format
    format_enum = LabelFormat.SEPARATE if label_format == "separate" else LabelFormat.COMBINED

    # Валидация размера файлов
    if barcodes_excel.size and barcodes_excel.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Excel файл слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    if codes_file.size and codes_file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл кодов слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    # Валидация типов файлов
    allowed_excel_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]
    if barcodes_excel.content_type not in allowed_excel_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл баркодов должен быть в формате Excel (.xlsx или .xls)",
        )

    if codes_file.content_type not in ALLOWED_CODES_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл кодов должен быть в формате CSV, Excel или PDF",
        )

    # Читаем файлы
    excel_bytes = await barcodes_excel.read()
    codes_bytes = await codes_file.read()

    # Парсим Excel с баркодами
    excel_parser = ExcelBarcodeParser()
    try:
        excel_data = excel_parser.parse(
            excel_bytes=excel_bytes,
            filename=barcodes_excel.filename or "barcodes.xlsx",
            column_name=barcode_column,  # Передаём выбранную колонку (или None для автоопределения)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка парсинга Excel с баркодами: {str(e)}",
        )

    labels_count = excel_data.count

    # Проверяем лимит пользователя
    if user:
        limit_result = await usage_repo.check_limit(
            user=user,
            labels_count=labels_count,
            free_limit=settings.free_tier_daily_limit,
            pro_limit=500,
        )
        allowed = limit_result["allowed"]
        limit_message = (
            f"использовано {limit_result['used_today']}/{limit_result['daily_limit']}"
            if not allowed
            else "OK"
        )
    else:
        try:
            allowed, limit_message, _ = await check_user_limit_db(
                user_telegram_id, labels_count, user_repo, usage_repo
            )
        except Exception:
            allowed, limit_message, _ = check_user_limit_fallback(user_telegram_id, labels_count)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Превышен дневной лимит: {limit_message}. "
            f"Оформите Pro подписку для увеличения лимита.",
        )

    # Проверяем лимит batch size
    if labels_count > settings.max_batch_size:
        return LabelMergeResponse(
            success=False,
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            message=f"Превышен лимит: {labels_count} этикеток. Максимум: {settings.max_batch_size}",
        )

    # Генерируем штрихкоды для каждого баркода
    barcode_generator = BarcodeGenerator()
    barcode_images: list[Image.Image] = []

    for item in excel_data.items:
        try:
            generated = barcode_generator.generate(
                digits=item.barcode,
                width_mm=40.0,
                height_mm=15.0,
            )
            barcode_images.append(generated.image)
        except ValueError:
            # Невалидный баркод — создаём placeholder
            placeholder = Image.new(
                "RGB", (LABEL.mm_to_pixels(40), LABEL.mm_to_pixels(15)), "white"
            )
            barcode_images.append(placeholder)

    # Парсим коды ЧЗ (поддерживаются CSV, Excel, PDF)
    try:
        codes_list = parse_codes_from_file(codes_bytes, codes_file.filename or "codes.csv")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка парсинга кодов ЧЗ: {str(e)}",
        )

    # HITL: проверяем совпадение количества строк Excel и кодов ЧЗ
    excel_rows_count = len(barcode_images)
    codes_count = len(codes_list)

    if excel_rows_count != codes_count and not force_generate:
        # Количество не совпадает — требуется подтверждение пользователя
        will_generate = min(excel_rows_count, codes_count)
        return LabelMergeResponse(
            success=False,
            needs_confirmation=True,
            count_mismatch=CountMismatchInfo(
                excel_rows=excel_rows_count,
                codes_count=codes_count,
                will_generate=will_generate,
            ),
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            message=f"Количество строк Excel ({excel_rows_count}) не совпадает с количеством кодов ЧЗ ({codes_count}). Будет создано {will_generate} этикеток.",
        )

    # Определяем количество этикеток (минимум из баркодов и кодов)
    total_count = min(excel_rows_count, codes_count)

    if total_count == 0:
        return LabelMergeResponse(
            success=False,
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            message="Нет данных для генерации этикеток",
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
    barcode_images = barcode_images[start_idx:end_idx]
    codes_list = codes_list[start_idx:end_idx]
    actual_labels_count = len(barcode_images)

    # Создаём сервис объединения для доступа к вспомогательным методам
    merger = LabelMerger()

    # Pre-flight проверка для кодов ЧЗ
    preflight_result: PreflightResult | None = None
    if run_preflight:
        preflight_result = await merger.preflight_checker.check_codes_only(
            codes=codes_list[:actual_labels_count]
        )

        if preflight_result and not preflight_result.can_proceed:
            return LabelMergeResponse(
                success=False,
                labels_count=0,
                pages_count=0,
                label_format=format_enum,
                preflight=preflight_result,
                message="Pre-flight проверка не пройдена. Исправьте ошибки.",
            )

    # Получаем размеры шаблона
    template_width, template_height = merger._get_template_size(template)

    # Объединяем этикетки
    if format_enum == LabelFormat.SEPARATE:
        merged_images = await _merge_batch_separate_from_barcodes(
            barcode_images=barcode_images[:actual_labels_count],
            codes=codes_list[:actual_labels_count],
            template_width=template_width,
            template_height=template_height,
            dm_generator=merger.dm_generator,
        )
        pages_count = actual_labels_count * 2
    else:
        merged_images = await _merge_batch_from_barcodes(
            barcode_images=barcode_images[:actual_labels_count],
            codes=codes_list[:actual_labels_count],
            template_width=template_width,
            template_height=template_height,
            dm_generator=merger.dm_generator,
        )
        pages_count = actual_labels_count

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
    file_id = str(uuid4())

    file_storage.save(
        file_id=file_id,
        data=_pdf_bytes,
        filename="labels.pdf",
        content_type="application/pdf",
        ttl_seconds=3600,
    )

    # Определяем результат preflight
    preflight_ok = True
    if preflight_result:
        preflight_ok = preflight_result.overall_status.value != "error"

    # Сохраняем в историю если есть пользователь
    generation_user = user
    if not generation_user and user_telegram_id:
        generation_user = await user_repo.get_by_telegram_id(user_telegram_id)

    if generation_user:
        # Создаём директорию для файлов пользователя
        user_dir = Path("data/generations") / str(generation_user.id)
        user_dir.mkdir(parents=True, exist_ok=True)

        gen_file_id = uuid4()
        file_path = user_dir / f"{gen_file_id}.pdf"
        file_path.write_bytes(_pdf_bytes)

        file_hash = hashlib.sha256(_pdf_bytes).hexdigest()

        # Определяем срок хранения по тарифу
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
                labels_count=actual_labels_count,
                preflight_passed=preflight_ok,
                file_path=str(file_path),
                file_hash=file_hash,
                file_size_bytes=len(_pdf_bytes),
                expires_days=expires_days,
            )
            file_id = str(generation.id)

        # Записываем использование
        await usage_repo.record_usage(
            user_id=generation_user.id,
            labels_count=actual_labels_count,
            preflight_status="ok" if preflight_ok else "error",
        )
    else:
        try:
            await record_user_usage_db(
                user_telegram_id, actual_labels_count, preflight_ok, user_repo, usage_repo
            )
        except Exception:
            record_user_usage_fallback(user_telegram_id, actual_labels_count, preflight_ok)

    format_text = "раздельном" if format_enum == LabelFormat.SEPARATE else "объединённом"
    return LabelMergeResponse(
        success=True,
        labels_count=actual_labels_count,
        pages_count=pages_count,
        label_format=format_enum,
        preflight=preflight_result,
        file_id=file_id,
        download_url=f"/api/v1/labels/download/{file_id}",
        message=f"Успешно сгенерировано {actual_labels_count} этикеток ({pages_count} стр.) "
        f"в {format_text} формате из Excel",
    )


async def _merge_batch_from_barcodes(
    barcode_images: list[Image.Image],
    codes: list[str],
    template_width: int,
    template_height: int,
    dm_generator,
) -> list[Image.Image]:
    """
    Объединение штрихкодов WB (из Excel) с DataMatrix ЧЗ.

    Компоновка: штрихкод WB слева, DataMatrix справа.
    """
    from concurrent.futures import ThreadPoolExecutor

    from PIL import ImageDraw, ImageFont

    # Генерируем все DataMatrix заранее
    dm_images: list[Image.Image] = []
    for code in codes:
        try:
            dm = dm_generator.generate(code, with_quiet_zone=False)
            dm_images.append(dm.image)
        except Exception:
            placeholder = Image.new(
                "RGB", (LABEL.DATAMATRIX_PIXELS, LABEL.DATAMATRIX_PIXELS), "white"
            )
            dm_images.append(placeholder)

    def merge_single(index: int) -> Image.Image:
        """Объединение одной этикетки."""
        label = Image.new("RGB", (template_width, template_height), "white")
        draw = ImageDraw.Draw(label)

        # Размеры текста под DataMatrix
        text_height = LABEL.mm_to_pixels(5)

        # DataMatrix = 22мм
        dm_size = LABEL.mm_to_pixels(22)
        dm_margin = LABEL.mm_to_pixels(1)

        # Область для DataMatrix справа
        dm_area_width = dm_size + 2 * dm_margin

        # Область для WB слева
        wb_area_width = template_width - dm_area_width
        small_margin = LABEL.mm_to_pixels(1)

        # Масштабируем штрихкод WB
        wb_img = barcode_images[index]
        wb_aspect = wb_img.width / wb_img.height
        max_wb_width = wb_area_width - small_margin
        max_wb_height = template_height - 2 * small_margin

        if wb_aspect > (max_wb_width / max_wb_height):
            new_width = max_wb_width
            new_height = int(new_width / wb_aspect)
        else:
            new_height = max_wb_height
            new_width = int(new_height * wb_aspect)

        wb_resized = wb_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Позиция WB: по центру вертикально, слева
        wb_x = small_margin
        wb_y = (template_height - new_height) // 2
        label.paste(wb_resized, (wb_x, wb_y))

        # Масштабируем DataMatrix
        dm_resized = dm_images[index].resize((dm_size, dm_size), Image.Resampling.NEAREST)

        # Позиция DataMatrix: справа, по центру вертикально
        dm_x = template_width - dm_size - dm_margin
        dm_y = (template_height - dm_size - text_height) // 2
        label.paste(dm_resized, (dm_x, dm_y))

        # Добавляем текст под DataMatrix
        try:
            import os

            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(current_dir, "..", "..", "assets", "fonts", "arial.ttf")

            font_size = LABEL.mm_to_pixels(2)
            small_font = ImageFont.truetype(font_path, font_size - 2)
        except OSError:
            try:
                small_font = ImageFont.truetype("arial.ttf", LABEL.mm_to_pixels(2) - 2)
            except OSError:
                small_font = ImageFont.load_default()

        text_y = dm_y + dm_size + 2
        text_center_x = dm_x + dm_size // 2

        # "ЧЕСТНЫЙ ЗНАК"
        label_text = "ЧЕСТНЫЙ ЗНАК"
        bbox = draw.textbbox((0, 0), label_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (text_center_x - text_width // 2, text_y), label_text, fill="black", font=small_font
        )

        # GTIN
        code = codes[index]
        if code and len(code) >= 16:
            gtin = code[2:16]
            text_y += LABEL.mm_to_pixels(2) - 2
            bbox = draw.textbbox((0, 0), gtin, font=small_font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (text_center_x - text_width // 2, text_y), gtin, fill="black", font=small_font
            )

        return label

    # Параллельная обработка
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(merge_single, range(len(barcode_images))))

    return results


async def _merge_batch_separate_from_barcodes(
    barcode_images: list[Image.Image],
    codes: list[str],
    template_width: int,
    template_height: int,
    dm_generator,
) -> list[Image.Image]:
    """
    Генерация раздельных этикеток из штрихкодов WB.

    Результат чередуется: WB1, DM1, WB2, DM2, ...
    """
    from PIL import ImageDraw, ImageFont

    # Генерируем все DataMatrix заранее
    dm_images: list[Image.Image] = []
    for code in codes:
        try:
            dm = dm_generator.generate(code, with_quiet_zone=True)
            dm_images.append(dm.image)
        except Exception:
            placeholder = Image.new(
                "RGB", (LABEL.DATAMATRIX_PIXELS, LABEL.DATAMATRIX_PIXELS), "white"
            )
            dm_images.append(placeholder)

    results: list[Image.Image] = []
    total = len(barcode_images)

    for i in range(total):
        # 1. Страница с WB штрихкодом
        wb_page = Image.new("RGB", (template_width, template_height), "white")
        wb_img = barcode_images[i]

        # Масштабируем с сохранением пропорций
        wb_aspect = wb_img.width / wb_img.height
        max_width = template_width - 2 * LABEL.QUIET_ZONE_PIXELS
        max_height = template_height - 2 * LABEL.QUIET_ZONE_PIXELS

        if wb_aspect > (max_width / max_height):
            new_width = max_width
            new_height = int(max_width / wb_aspect)
        else:
            new_height = max_height
            new_width = int(max_height * wb_aspect)

        wb_resized = wb_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Центрируем
        x = (template_width - new_width) // 2
        y = (template_height - new_height) // 2
        wb_page.paste(wb_resized, (x, y))
        results.append(wb_page)

        # 2. Страница с DataMatrix
        dm_page = Image.new("RGB", (template_width, template_height), "white")
        draw = ImageDraw.Draw(dm_page)

        text_height = LABEL.mm_to_pixels(8)
        dm_size = min(
            template_width - 2 * LABEL.QUIET_ZONE_PIXELS,
            template_height - 2 * LABEL.QUIET_ZONE_PIXELS - text_height,
            LABEL.DATAMATRIX_PIXELS + 2 * LABEL.QUIET_ZONE_PIXELS,
        )

        dm_resized = dm_images[i].resize((dm_size, dm_size), Image.Resampling.NEAREST)

        x = (template_width - dm_size) // 2
        y = (template_height - dm_size - text_height) // 2
        dm_page.paste(dm_resized, (x, y))

        # Шрифт
        try:
            import os

            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(current_dir, "..", "..", "assets", "fonts", "arial.ttf")

            font_size = LABEL.mm_to_pixels(2)
            small_font = ImageFont.truetype(font_path, font_size - 2)
        except OSError:
            try:
                small_font = ImageFont.truetype("arial.ttf", LABEL.mm_to_pixels(2) - 2)
            except OSError:
                small_font = ImageFont.load_default()

        text_center_x = template_width // 2
        text_y = y + dm_size + 4

        # "ЧЕСТНЫЙ ЗНАК"
        label_text = "ЧЕСТНЫЙ ЗНАК"
        bbox = draw.textbbox((0, 0), label_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (text_center_x - text_width // 2, text_y), label_text, fill="black", font=small_font
        )

        # GTIN
        code = codes[i]
        if code and len(code) >= 16:
            gtin = code[2:16]
            text_y += LABEL.mm_to_pixels(2)
            bbox = draw.textbbox((0, 0), gtin, font=small_font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (text_center_x - text_width // 2, text_y), gtin, fill="black", font=small_font
            )

        # Нумерация
        number_text = f"{i + 1} из {total}"
        text_y += LABEL.mm_to_pixels(2)
        bbox = draw.textbbox((0, 0), number_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (text_center_x - text_width // 2, text_y), number_text, fill="black", font=small_font
        )

        results.append(dm_page)

    return results


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
- `codes_file` — CSV/Excel с кодами ЧЗ
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
    codes_file: Annotated[UploadFile | None, File(description="CSV/Excel с кодами ЧЗ")] = None,
    codes: Annotated[str | None, Form(description="JSON массив кодов ЧЗ")] = None,
    organization_name: Annotated[str | None, Form(description="Название организации")] = None,
    inn: Annotated[str | None, Form(description="ИНН организации")] = None,
    layout: Annotated[str, Form(description="Шаблон: basic, professional")] = "basic",
    label_size: Annotated[str, Form(description="Размер: 58x40, 58x30, 58x60")] = "58x40",
    label_format: Annotated[str, Form(description="Формат: combined или separate")] = "combined",
    # Флаги отображения полей
    show_article: Annotated[bool, Form(description="Показывать артикул")] = True,
    show_size_color: Annotated[bool, Form(description="Показывать размер/цвет")] = True,
    show_name: Annotated[bool, Form(description="Показывать название")] = True,
    show_organization: Annotated[bool, Form(description="Показывать организацию")] = True,
    show_inn: Annotated[bool, Form(description="Показывать ИНН")] = False,
    show_country: Annotated[bool, Form(description="Показывать страну")] = False,
    show_composition: Annotated[bool, Form(description="Показывать состав")] = False,
    show_chz_code_text: Annotated[bool, Form(description="Показывать код ЧЗ текстом")] = True,
    show_serial_number: Annotated[bool, Form(description="Показывать серийный номер")] = False,
    show_brand: Annotated[bool, Form(description="Показывать бренд")] = False,
    # Поля для professional шаблона
    show_importer: Annotated[bool, Form(description="Показывать импортер")] = False,
    show_manufacturer: Annotated[bool, Form(description="Показывать производитель")] = False,
    show_address: Annotated[bool, Form(description="Показывать адрес")] = False,
    show_production_date: Annotated[bool, Form(description="Показывать дату производства")] = False,
    show_certificate: Annotated[bool, Form(description="Показывать сертификат")] = False,
    # Реквизиты для professional шаблона
    organization_address: Annotated[str | None, Form(description="Адрес производства")] = None,
    importer: Annotated[str | None, Form(description="Импортер")] = None,
    manufacturer: Annotated[str | None, Form(description="Производитель")] = None,
    production_date: Annotated[str | None, Form(description="Дата производства")] = None,
    certificate_number: Annotated[str | None, Form(description="Номер сертификата")] = None,
    # Диапазон печати ("Ножницы")
    range_start: Annotated[int | None, Form(description="Начало диапазона (1-based)")] = None,
    range_end: Annotated[int | None, Form(description="Конец диапазона (1-based)")] = None,
    # HITL: игнорировать несовпадение количества
    force_generate: Annotated[
        bool, Form(description="Игнорировать несовпадение количества строк Excel и кодов ЧЗ")
    ] = False,
    # Fallback значения
    fallback_size: Annotated[str | None, Form(description="Размер по умолчанию")] = None,
    fallback_color: Annotated[str | None, Form(description="Цвет по умолчанию")] = None,
    barcode_column: Annotated[str | None, Form(description="Колонка с баркодами")] = None,
    telegram_id: Annotated[int | None, Form(description="Telegram ID")] = None,
    current_user: User | None = Depends(get_current_user_optional),
    user_repo: UserRepository = Depends(_get_user_repo),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
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

    # Диагностика: логируем параметры ИНН
    logger.info(
        f"[generate_from_excel] Параметры ИНН: inn={inn!r}, show_inn={show_inn!r} (type={type(show_inn).__name__}), "
        f"organization_name={organization_name!r}, show_organization={show_organization!r}"
    )

    from app.models.label_types import LabelLayout, LabelSize
    from app.services.excel_parser import ExcelBarcodeParser
    from app.services.label_generator import LabelGenerator, LabelItem

    # Определяем пользователя
    user = current_user
    user_telegram_id = telegram_id
    if user:
        user_telegram_id = int(user.telegram_id) if user.telegram_id else None

    # Нормализуем параметры
    format_enum = LabelFormat.SEPARATE if label_format == "separate" else LabelFormat.COMBINED

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
    import json

    codes_list: list[str] = []
    if codes_file:
        codes_bytes = await codes_file.read()
        codes_list = parse_codes_from_file(codes_bytes, codes_file.filename or "codes.csv")
    elif codes:
        try:
            codes_list = json.loads(codes)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат JSON в параметре codes",
            )

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

    # Преобразуем в LabelItem для нового генератора
    label_items: list[LabelItem] = []
    for item in excel_data.items:
        label_items.append(
            LabelItem(
                barcode=item.barcode,
                article=item.article,
                size=item.size or fallback_size,
                color=item.color or fallback_color,
                name=item.name,
                brand=getattr(item, "brand", None),  # Бренд из Excel если есть
                country=item.country,
                composition=item.composition,
            )
        )

    labels_count = len(label_items)

    # Проверяем лимит
    if user:
        limit_result = await usage_repo.check_limit(
            user=user,
            labels_count=labels_count,
            free_limit=settings.free_tier_daily_limit,
            pro_limit=500,
        )
        allowed = limit_result["allowed"]
    else:
        try:
            allowed, _, _ = await check_user_limit_db(
                user_telegram_id, labels_count, user_repo, usage_repo
            )
        except Exception:
            allowed, _, _ = check_user_limit_fallback(user_telegram_id, labels_count)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Превышен дневной лимит. Оформите Pro подписку.",
        )

    # HITL: проверяем совпадение количества строк Excel и кодов ЧЗ
    excel_rows_count = len(label_items)
    codes_count_total = len(codes_list)

    if excel_rows_count != codes_count_total and not force_generate:
        # Количество не совпадает — требуется подтверждение пользователя
        will_generate = min(excel_rows_count, codes_count_total)
        return LabelMergeResponse(
            success=False,
            needs_confirmation=True,
            count_mismatch=CountMismatchInfo(
                excel_rows=excel_rows_count,
                codes_count=codes_count_total,
                will_generate=will_generate,
            ),
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            message=f"Количество строк Excel ({excel_rows_count}) не совпадает с количеством кодов ЧЗ ({codes_count_total}). Будет создано {will_generate} этикеток.",
        )

    # Определяем количество этикеток
    total_count = min(excel_rows_count, codes_count_total)
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
    label_items = label_items[start_idx:end_idx]
    codes_list = codes_list[start_idx:end_idx]
    actual_count = len(label_items)

    # Pre-flight проверка кодов ЧЗ
    preflight_checker = PreflightChecker()
    preflight_result = await preflight_checker.check_codes_only(codes=codes_list[:actual_count])

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

    # Диагностика: логируем параметры перед вызовом генератора
    logger.info(
        f"[generate_from_excel] Вызов генератора: show_inn={show_inn}, inn={inn!r}, "
        f"show_organization={show_organization}, organization={organization_name!r}"
    )

    try:
        pdf_bytes = label_generator.generate(
            items=label_items[:actual_count],
            codes=codes_list[:actual_count],
            size=size_enum.value,
            organization=organization_name,
            inn=inn,
            layout=layout_enum.value,
            label_format=label_format,
            show_article=show_article,
            show_size_color=show_size_color,
            show_name=show_name,
            show_organization=show_organization,
            show_inn=show_inn,
            show_country=show_country,
            show_composition=show_composition,
            show_chz_code_text=show_chz_code_text,
            show_serial_number=show_serial_number,
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
        )
    except Exception as e:
        return LabelMergeResponse(
            success=False,
            labels_count=0,
            pages_count=0,
            label_format=format_enum,
            message=f"Ошибка генерации PDF: {str(e)}",
        )

    # Количество страниц зависит от формата
    pages_count = actual_count * 2 if format_enum == LabelFormat.SEPARATE else actual_count

    # Сохраняем файл
    file_id = str(uuid4())
    file_storage.save(
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
    else:
        try:
            await record_user_usage_db(
                user_telegram_id, actual_count, preflight_ok, user_repo, usage_repo
            )
        except Exception:
            record_user_usage_fallback(user_telegram_id, actual_count, preflight_ok)

    layout_name = {"basic": "Базовый", "professional": "Профессиональный"}.get(layout, layout)
    return LabelMergeResponse(
        success=True,
        labels_count=actual_count,
        pages_count=pages_count,
        label_format=format_enum,
        preflight=preflight_result,
        file_id=file_id,
        download_url=f"/api/v1/labels/download/{file_id}",
        message=f"Сгенерировано {actual_count} этикеток (layout: {layout_name})",
    )


@router.get(
    "/labels/download/{file_id}",
    response_class=StreamingResponse,
    summary="Скачать сгенерированный PDF",
)
async def download_pdf(
    file_id: str,
    gen_repo: GenerationRepository = Depends(_get_gen_repo),
) -> StreamingResponse:
    """
    Скачать сгенерированный PDF по ID.

    Args:
        file_id: Идентификатор файла из ответа merge (UUID или временный ID)

    Returns:
        PDF файл для скачивания
    """
    # Сначала проверяем временное хранилище
    stored = file_storage.get(file_id)
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
            # Проверяем что файл внутри разрешённой директории (Path Traversal защита)
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
