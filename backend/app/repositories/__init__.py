"""
Репозитории для работы с базой данных.

Repository Pattern обеспечивает:
- Абстракцию доступа к данным
- Централизованную логику запросов
- Упрощённое тестирование
"""

from app.repositories.generation_repository import GenerationRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.usage_repository import UsageRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "UserRepository",
    "UsageRepository",
    "PaymentRepository",
    "GenerationRepository",
]
