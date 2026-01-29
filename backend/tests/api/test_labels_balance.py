import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.db.models import User, UserPlan
from app.main import app


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session


@pytest.fixture
def test_client(mock_db_session):
    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_debits_balance_for_pro(test_client, _mock_db_session):
    # Setup: Pro user
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, plan=UserPlan.PRO, label_balance=1000, telegram_id="12345")

    # Mock user repo to return this user
    with (
        patch(
            "app.repositories.UserRepository.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_user,
        ),
        patch(
            "app.repositories.UserRepository.get_by_telegram_id",
            new_callable=AsyncMock,
            return_value=mock_user,
        ),
        patch(
            "app.repositories.UsageRepository.check_limit",
            new_callable=AsyncMock,
            return_value={"allowed": True, "remaining": 1000, "limit": 10000, "plan": "pro"},
        ),
        patch("app.repositories.UsageRepository.record_usage", new_callable=AsyncMock),
        patch(
            "app.services.label_balance.LabelBalanceService.debit_labels", new_callable=AsyncMock
        ) as mock_debit,
        patch("app.services.excel_parser.ExcelBarcodeParser.parse"),
        patch(
            "app.services.label_generator.LabelGenerator.generate", return_value=b"pdf_content"
        ),
        patch("app.services.file_storage.RedisFileStorage.save", new_callable=AsyncMock),
    ):
        # Request generation with codes (must be long enough to pass crypto check)
        long_code = "010467004977480221" + "A" * 70
        response = test_client.post(
            "/api/v1/labels/generate-from-excel",
            data={
                "organization_name": "Test Org",
                "telegram_id": 12345,
                "codes": f'["{long_code}"]',
            },
            files={
                "barcodes_excel": (
                    "test.xlsx",
                    b"content",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        # Assert
        if response.status_code != 200:
            print(f"DEBUG: {response.json()}")
        assert response.status_code == 200
        # Check if debit_labels was called
        mock_debit.assert_called_once()


@pytest.mark.asyncio
async def test_generate_fails_on_insufficient_balance_pro(test_client, _mock_db_session):
    # Setup: Pro user with low balance
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, plan=UserPlan.PRO, label_balance=10, telegram_id="12345")

    with (
        patch("app.repositories.UserRepository.get_by_telegram_id", return_value=mock_user),
        patch(
            "app.repositories.UsageRepository.check_limit",
            return_value={
                "allowed": False,
                "remaining": 10,
                "limit": 10000,
                "plan": "pro",
                "used_today": 0,
            },
        ),
    ):
        response = test_client.post(
            "/api/v1/labels/generate-from-excel",
            data={
                "organization_name": "Test Org",
                "telegram_id": 12345,
                "codes": '["code1", "code2"]',
            },
            files={
                "barcodes_excel": (
                    "test.xlsx",
                    b"content",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert response.status_code == 403
