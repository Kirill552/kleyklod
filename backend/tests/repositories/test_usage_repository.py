import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models import User, UserPlan
from app.repositories.usage_repository import UsageRepository


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_check_limit_pro_uses_balance(mock_db_session):
    # Setup: Pro user with 100 balance
    user_id = uuid.uuid4()
    user = User(id=user_id, plan=UserPlan.PRO, label_balance=100)

    repo = UsageRepository(mock_db_session)

    # Execute: Request 50 labels
    result = await repo.check_limit(user, 50)

    # Assert
    assert result["allowed"] is True
    assert result["remaining"] == 100
    assert result["limit"] == 10000  # Accumulation cap


@pytest.mark.asyncio
async def test_check_limit_pro_fail(mock_db_session):
    # Setup: Pro user with 10 balance
    user_id = uuid.uuid4()
    user = User(id=user_id, plan=UserPlan.PRO, label_balance=10)

    repo = UsageRepository(mock_db_session)

    # Execute: Request 50 labels
    result = await repo.check_limit(user, 50)

    # Assert
    assert result["allowed"] is False
    assert result["remaining"] == 10  # current balance


@pytest.mark.asyncio
async def test_check_limit_free_monthly(mock_db_session):
    # Setup: Free user, already used 40 this month
    user_id = uuid.uuid4()
    user = User(id=user_id, plan=UserPlan.FREE)

    repo = UsageRepository(mock_db_session)

    # Mock get_monthly_usage to return 40
    mock_result = MagicMock()
    mock_result.scalar.return_value = 40
    mock_db_session.execute.return_value = mock_result

    # Execute: Request 20 labels (40 + 20 = 60 > 50)
    result = await repo.check_limit(user, 20, free_limit=50)

    # Assert
    assert result["allowed"] is False
    assert result["remaining"] == 10  # 50 - 40
    assert result["monthly_limit"] == 50
