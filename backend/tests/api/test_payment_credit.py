import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.routes.payments import yookassa_webhook
from app.db.models import User, UserPlan


@pytest.mark.asyncio
async def test_webhook_credits_labels_for_pro():
    # Setup
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, plan=UserPlan.FREE, label_balance=0)
    mock_db = AsyncMock()

    # Mock request
    mock_request = AsyncMock()
    mock_request.headers = {"X-Real-IP": "185.71.76.1"}  # Whitelisted IP
    mock_request.json.return_value = {
        "event": "payment.succeeded",
        "object": {
            "id": "pay_123",
            "metadata": {"user_id": str(user_id), "plan": "pro"},
            "amount": {"value": "490.00"},
        },
    }

    # Mock repos and services
    with (
        patch("app.api.routes.payments.is_yookassa_ip", return_value=True),
        patch(
            "app.repositories.UserRepository.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_user,
        ),
        patch(
            "app.repositories.PaymentRepository.get_by_external_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.repositories.PaymentRepository.create", new_callable=AsyncMock
        ) as mock_create_pay,
        patch(
            "app.repositories.PaymentRepository.activate_subscription", new_callable=AsyncMock
        ) as mock_activate,
        patch(
            "app.services.label_balance.LabelBalanceService.credit_labels", new_callable=AsyncMock
        ) as mock_credit,
    ):
        mock_create_pay.return_value = MagicMock(id=uuid.uuid4())

        # Execute
        result = await yookassa_webhook(mock_request, mock_db)

        # Assert
        assert result == {"status": "ok"}
        mock_activate.assert_called_once()
        mock_credit.assert_called_once_with(
            user_id=user_id,
            amount=2000,
            reason="subscription_renewal",
            reference_id=mock_create_pay.return_value.id,
            description="Начисление по тарифу Про (за платеж pay_123)",
        )
        mock_db.commit.assert_called_once()
