"""
API эндпоинты для работы с этикетками.

Основной функционал: объединение WB + ЧЗ.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import LABEL, get_settings
from app.db.database import get_db
from app.models.schemas import (
    ErrorResponse,
    LabelMergeResponse,
    LabelTemplate,
    PreflightResponse,
    PreflightResult,
    PreflightStatus,
    TemplatesResponse,
)
from app.repositories import UsageRepository, UserRepository
from app.services.merger import LabelMerger
from app.services.preflight import PreflightChecker

router = APIRouter()
settings = get_settings()

# Временное in-memory хранилище для fallback
# Импортируем из users.py для единого источника данных
from app.api.routes.users import _usage_db, _users_db  # noqa: E402


async def _get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency для получения UserRepository."""
    return UserRepository(db)


async def _get_usage_repo(db: AsyncSession = Depends(get_db)) -> UsageRepository:
    """Dependency для получения UsageRepository."""
    return UsageRepository(db)


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
- `run_preflight` — Выполнять Pre-flight проверку (по умолчанию: да)
- `telegram_id` — ID пользователя Telegram (для учёта лимитов)

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
    codes_file: Annotated[UploadFile, File(description="CSV/Excel с кодами Честного Знака")],
    template: Annotated[str, Form(description="Шаблон этикетки")] = "58x40",
    run_preflight: Annotated[bool, Form(description="Выполнять Pre-flight")] = True,
    telegram_id: Annotated[int | None, Form(description="Telegram ID пользователя")] = None,
    user_repo: UserRepository = Depends(_get_user_repo),
    usage_repo: UsageRepository = Depends(_get_usage_repo),
) -> LabelMergeResponse:
    """
    Объединение этикеток WB и кодов ЧЗ в один PDF.

    Основной workflow:
    1. Проверка лимитов пользователя
    2. Парсинг PDF от Wildberries (извлечение изображений этикеток)
    3. Парсинг CSV/Excel с кодами DataMatrix
    4. Генерация DataMatrix для каждого кода
    5. Pre-flight проверка (размер, контраст, quiet zone)
    6. Объединение WB штрихкода и DataMatrix на одной этикетке
    7. Генерация итогового PDF
    8. Запись использования

    Args:
        wb_pdf: PDF файл с этикетками WB
        codes_file: CSV/Excel файл с кодами ЧЗ
        template: Шаблон этикетки
        run_preflight: Выполнять ли Pre-flight проверку
        telegram_id: ID пользователя Telegram для учёта лимитов

    Returns:
        LabelMergeResponse с результатом и ссылкой на скачивание
    """
    # Валидация размера файлов
    if wb_pdf.size and wb_pdf.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF файл слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    if codes_file.size and codes_file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл кодов слишком большой. Максимум: {settings.max_upload_size_mb}MB",
        )

    # Валидация типов файлов
    if wb_pdf.content_type not in ["application/pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл WB должен быть в формате PDF",
        )

    allowed_codes_types = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
    ]
    if codes_file.content_type not in allowed_codes_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл кодов должен быть в формате CSV или Excel",
        )

    # Читаем файлы
    wb_pdf_bytes = await wb_pdf.read()
    codes_bytes = await codes_file.read()

    # Создаём сервис объединения
    merger = LabelMerger()

    try:
        # Сначала получаем количество этикеток для проверки лимита
        # (парсим PDF для подсчёта страниц)
        from app.services.pdf_parser import PDFParser

        pdf_parser = PDFParser()
        labels_count = pdf_parser.get_page_count(wb_pdf_bytes)

        # Проверяем лимит пользователя
        try:
            allowed, limit_message, remaining = await check_user_limit_db(
                telegram_id, labels_count, user_repo, usage_repo
            )
        except Exception:
            # Fallback на in-memory при ошибке БД
            allowed, limit_message, remaining = check_user_limit_fallback(telegram_id, labels_count)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Превышен дневной лимит. {limit_message}. "
                f"Оформите Pro подписку для увеличения лимита.",
            )

        # Выполняем объединение
        result = await merger.merge(
            wb_pdf_bytes=wb_pdf_bytes,
            codes_bytes=codes_bytes,
            codes_filename=codes_file.filename or "codes.csv",
            template=template,
            run_preflight=run_preflight,
        )

        # Записываем использование после успешной генерации
        preflight_ok = True
        if result.preflight:
            preflight_ok = result.preflight.overall_status.value != "error"

        try:
            await record_user_usage_db(
                telegram_id, labels_count, preflight_ok, user_repo, usage_repo
            )
        except Exception:
            # Fallback на in-memory
            record_user_usage_fallback(telegram_id, labels_count, preflight_ok)

        return result

    except HTTPException:
        # Пробрасываем HTTP исключения как есть
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
    summary="Pre-flight проверка",
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
    Pre-flight проверка без генерации результата.

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


@router.get(
    "/labels/download/{file_id}",
    response_class=StreamingResponse,
    summary="Скачать сгенерированный PDF",
)
async def download_pdf(file_id: str) -> StreamingResponse:  # noqa: ARG001
    """
    Скачать сгенерированный PDF по ID.

    Args:
        file_id: Идентификатор файла из ответа merge

    Returns:
        PDF файл для скачивания
    """
    # TODO: Реализовать получение файла из хранилища
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Файл не найден или срок хранения истёк",
    )
