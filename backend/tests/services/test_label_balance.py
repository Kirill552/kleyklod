import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LabelTransaction, TransactionType, User, UserPlan
from app.services.label_balance import LabelBalanceService


@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_credit_labels_caps_at_10k_for_pro(mock_db_session):
    # Setup
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, plan=UserPlan.PRO, label_balance=9000)

    # Mock result for get_user_for_update
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_result

    service = LabelBalanceService(mock_db_session)

    # Execute: Credit 2000, should cap at 10000
    new_balance = await service.credit_labels(user_id, 2000, "subscription_renewal")

    # Assert
    assert new_balance == 10000
    assert mock_user.label_balance == 10000
    mock_db_session.add.assert_called_once()
    transaction = mock_db_session.add.call_args[0][0]
    assert isinstance(transaction, LabelTransaction)
    assert transaction.amount == 2000
    assert transaction.balance_after == 10000
    assert transaction.type == TransactionType.CREDIT
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_debit_labels_insufficient_funds(mock_db_session):
    # Setup
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, plan=UserPlan.PRO, label_balance=10)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_result

    service = LabelBalanceService(mock_db_session)

    # Execute & Assert
    with pytest.raises(ValueError, match="Insufficient balance"):
        await service.debit_labels(user_id, 20, "generation")


@pytest.mark.asyncio
async def test_debit_labels_success(mock_db_session):
    # Setup
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, plan=UserPlan.PRO, label_balance=100)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_result

    service = LabelBalanceService(mock_db_session)

    # Execute
    new_balance = await service.debit_labels(user_id, 30, "generation")

    # Assert
    assert new_balance == 70
    assert mock_user.label_balance == 70
    mock_db_session.add.assert_called_once()
    transaction = mock_db_session.add.call_args[0][0]
    assert transaction.type == TransactionType.DEBIT
    assert transaction.amount == 30
    assert transaction.balance_after == 70


@pytest.mark.asyncio
async def test_get_transactions(mock_db_session):
    # Setup
    user_id = uuid.uuid4()
    mock_transactions = [
        LabelTransaction(user_id=user_id, amount=100, type=TransactionType.CREDIT),
        LabelTransaction(user_id=user_id, amount=20, type=TransactionType.DEBIT),
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_transactions
    mock_db_session.execute.return_value = mock_result

    service = LabelBalanceService(mock_db_session)

    # Execute
    txs = await service.get_transactions(user_id)

    # Assert
    assert len(txs) == 2
    assert txs[0].amount == 100
    assert txs[1].amount == 20
    mock_db_session.execute.assert_called_once()
