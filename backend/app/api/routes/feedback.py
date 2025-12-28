"""
API эндпоинты для сбора обратной связи.

Минималистичный опрос после 3-й генерации.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import FeedbackResponse, User
from app.models.schemas import FeedbackSubmitRequest, FeedbackSubmitResponse

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])
logger = logging.getLogger(__name__)


@router.post("", response_model=FeedbackSubmitResponse)
async def submit_feedback(
    request: FeedbackSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackSubmitResponse:
    """
    Сохранить ответ пользователя на опрос.

    Показываем опрос один раз после 3-й генерации.
    После отправки помечаем user.feedback_asked = True.
    """
    # Проверяем, не отправлял ли уже
    if user.feedback_asked:
        return FeedbackSubmitResponse(success=False, message="Вы уже отправляли отзыв. Спасибо!")

    # Сохраняем ответ
    feedback = FeedbackResponse(
        user_id=user.id,
        text=request.text,
        source=request.source,
    )
    db.add(feedback)

    # Помечаем что опрос показан
    user.feedback_asked = True

    await db.commit()

    logger.info(f"Feedback saved from user {user.id}: {request.text[:50]}...")

    return FeedbackSubmitResponse(
        success=True, message="Спасибо за обратную связь! Мы учтём ваше мнение."
    )


@router.get("/status")
async def get_feedback_status(
    user: User = Depends(get_current_user),
) -> dict:
    """
    Проверить, нужно ли показывать опрос пользователю.

    Возвращает should_ask=True если:
    - Пользователь ещё не отвечал на опрос
    - (количество генераций проверяется на фронте/боте)
    """
    return {
        "should_ask": not user.feedback_asked,
        "feedback_asked": user.feedback_asked,
    }
