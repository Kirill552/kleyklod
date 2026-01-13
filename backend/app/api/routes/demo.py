"""
Demo эндпоинт для генерации этикеток БЕЗ регистрации.

Ограничения:
- 3 генерации в час на IP
- Максимум 5 баркодов
- Максимум 5 кодов ЧЗ
- Максимум 2MB файлы
- Водяной знак на результате
"""

import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis

from app.db.database import get_redis
from app.models.schemas import LabelMergeResponse
from app.services.rate_limiter import RateLimiter

router = APIRouter(prefix="/api/v1/demo", tags=["Demo"])

# Ограничения для demo
DEMO_MAX_CODES = 5
DEMO_MAX_FILE_SIZE_MB = 2
DEMO_MAX_FILE_SIZE_BYTES = DEMO_MAX_FILE_SIZE_MB * 1024 * 1024
DEMO_RATE_LIMIT = 3  # генераций в час
DEMO_RATE_WINDOW = 3600  # 1 час в секундах


def _get_client_ip(request: Request) -> str:
    """
    Получить реальный IP клиента.

    ВАЖНО: X-Real-IP устанавливается nginx и не может быть подделан.
    X-Forwarded-For можно подделать, поэтому не используем.
    """
    # X-Real-IP — надёжный заголовок от nginx
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback на client.host (без nginx)
    return request.client.host if request.client else "unknown"


@router.post(
    "/generate-full",
    response_model=LabelMergeResponse,
    summary="Demo генерация из Excel (полный флоу)",
    description="""
Demo генерация этикеток из Excel файла с баркодами WB — БЕЗ регистрации.

Это рекомендуемый способ: загрузите Excel с баркодами из ЛК Wildberries
и PDF с кодами Честного Знака.

**Ограничения:**
- 3 генерации в час на IP
- Максимум 5 баркодов
- Максимум 5 кодов ЧЗ
- Максимум 2MB файлы
- Водяной знак "DEMO" на результате

**Для снятия ограничений:**
Зарегистрируйтесь через Telegram бот и получите 7 дней полного доступа бесплатно.
    """,
)
async def demo_generate_full(
    request: Request,
    barcodes_excel: Annotated[UploadFile, File(description="Excel с баркодами из ЛК Wildberries")],
    codes_file: Annotated[UploadFile, File(description="PDF с кодами ЧЗ")],
    template: Annotated[str, Form(description="Шаблон этикетки")] = "58x40",
    redis: Redis = Depends(get_redis),
) -> LabelMergeResponse:
    """
    Demo генерация из Excel — полный флоу БЕЗ регистрации.

    Workflow (ReportLab — векторный PDF):
    1. Парсинг Excel с баркодами WB
    2. Парсинг кодов ЧЗ
    3. Векторная генерация PDF через ReportLab
    4. Водяной знак "DEMO"
    """
    import uuid

    from app.models.schemas import LabelFormat
    from app.services.excel_parser import ExcelBarcodeParser
    from app.services.file_storage import get_file_storage
    from app.services.label_generator import LabelGenerator, LabelItem
    from app.services.pdf_parser import PDFParser

    # Получаем IP клиента
    client_ip = _get_client_ip(request)

    # Проверяем rate limit
    rate_limiter = RateLimiter(redis)
    allowed, remaining, reset_ts = await rate_limiter.check_rate_limit(
        key=f"demo:{client_ip}",
        limit=DEMO_RATE_LIMIT,
        window_seconds=DEMO_RATE_WINDOW,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "DEMO_LIMIT_EXCEEDED",
                "message": "Лимит демо исчерпан. Зарегистрируйтесь для 7 дней бесплатного доступа.",
                "reset_at": reset_ts,
            },
        )

    # Проверяем размеры файлов
    if barcodes_excel.size and barcodes_excel.size > DEMO_MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Excel слишком большой для demo. Максимум: {DEMO_MAX_FILE_SIZE_MB}MB.",
        )

    if codes_file.size and codes_file.size > DEMO_MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл кодов слишком большой для demo. Максимум: {DEMO_MAX_FILE_SIZE_MB}MB.",
        )

    # Проверяем типы файлов
    allowed_excel_types = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    if barcodes_excel.content_type not in allowed_excel_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл баркодов должен быть в формате Excel (.xlsx, .xls)",
        )

    # Проверяем что файл кодов — PDF
    allowed_codes_types = ["application/pdf"]
    is_pdf = codes_file.content_type in allowed_codes_types or (
        codes_file.filename and codes_file.filename.lower().endswith(".pdf")
    )
    if not is_pdf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл кодов должен быть в формате PDF. CSV и Excel не содержат криптоподпись.",
        )

    # Читаем файлы
    excel_bytes = await barcodes_excel.read()
    codes_bytes = await codes_file.read()

    # Парсим Excel с баркодами
    excel_parser = ExcelBarcodeParser()
    try:
        barcodes_data = excel_parser.parse(excel_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка чтения Excel: {str(e)}",
        )

    if barcodes_data.count > DEMO_MAX_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Demo режим: максимум {DEMO_MAX_CODES} баркодов. "
            f"Ваш файл содержит {barcodes_data.count}. Зарегистрируйтесь для снятия ограничения.",
        )

    # Парсим коды ЧЗ из PDF
    pdf_parser = PDFParser()
    try:
        codes_result = pdf_parser.extract_codes(codes_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка чтения кодов ЧЗ из PDF: {str(e)}",
        )

    if codes_result.count > DEMO_MAX_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Demo режим: максимум {DEMO_MAX_CODES} кодов ЧЗ. "
            f"Ваш файл содержит {codes_result.count}. Зарегистрируйтесь для снятия ограничения.",
        )

    # Конвертируем ExcelBarcodeItem → LabelItem
    items = [
        LabelItem(
            barcode=item.barcode,
            article=item.article,
            size=item.size,
            color=item.color,
            name=item.name,
        )
        for item in barcodes_data.items
    ]

    # Генерируем PDF через ReportLab (векторный)
    label_gen = LabelGenerator()
    try:
        pdf_bytes = label_gen.generate(
            items=items,
            codes=codes_result.codes,
            size=template,
            organization=None,  # Demo не требует организации
            layout="basic",
            label_format="combined",
            show_article=True,
            show_size=True,
            show_color=True,
            show_name=True,
            demo_mode=True,  # Водяной знак DEMO
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации: {str(e)}",
        )

    # Количество этикеток = количество кодов ЧЗ (GTIN matching)
    labels_count = len(codes_result.codes)

    # Сохраняем в file_storage (Redis)
    file_id = str(uuid.uuid4())
    await get_file_storage(redis).save(
        file_id=file_id,
        data=pdf_bytes,
        filename="demo_labels.pdf",
        content_type="application/pdf",
        ttl_seconds=3600,  # 1 час для demo
    )

    return LabelMergeResponse(
        success=True,
        labels_count=labels_count,
        pages_count=labels_count,
        label_format=LabelFormat.COMBINED,
        preflight=None,  # Demo не делает preflight
        file_id=file_id,
        message=f"Готово! {labels_count} этикеток (векторный PDF). "
        f"Demo: осталось {remaining - 1} генераций в этом часе.",
    )


@router.get(
    "/limits",
    summary="Проверить лимиты demo",
    description="Проверить оставшееся количество demo генераций для текущего IP.",
)
async def check_demo_limits(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> dict:
    """
    Проверить оставшееся количество demo генераций.
    """
    client_ip = _get_client_ip(request)

    rate_limiter = RateLimiter(redis)
    remaining, reset_ts = await rate_limiter.get_remaining(
        key=f"demo:{client_ip}",
        limit=DEMO_RATE_LIMIT,
        window_seconds=DEMO_RATE_WINDOW,
    )

    return {
        "remaining": remaining,
        "limit": DEMO_RATE_LIMIT,
        "reset_at": reset_ts,
        "max_barcodes": DEMO_MAX_CODES,
        "max_codes": DEMO_MAX_CODES,
        "max_file_size_mb": DEMO_MAX_FILE_SIZE_MB,
        "message": "Зарегистрируйтесь для 7 дней полного доступа бесплатно",
    }


@router.get(
    "/download/{file_id}",
    response_class=StreamingResponse,
    summary="Скачать demo PDF",
    description="Скачать сгенерированный demo PDF файл по ID.",
)
async def download_demo_pdf(
    file_id: str,
    redis: Redis = Depends(get_redis),
) -> StreamingResponse:
    """
    Скачать demo PDF по ID.

    Args:
        file_id: Идентификатор файла из ответа generate-full

    Returns:
        PDF файл для скачивания
    """
    from app.services.file_storage import get_file_storage

    stored = await get_file_storage(redis).get(file_id)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден или срок хранения истёк (1 час для demo)",
        )

    return StreamingResponse(
        io.BytesIO(stored.data),
        media_type=stored.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{stored.filename}"',
        },
    )
