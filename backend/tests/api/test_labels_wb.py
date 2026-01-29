"""Тесты для API endpoint /labels/generate-wb."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateWbEndpoint:
    def test_generate_wb_unauthorized(self):
        """POST /api/v1/labels/generate-wb без авторизации возвращает 401"""
        response = client.post(
            "/api/v1/labels/generate-wb",
            json={
                "items": [{"barcode": "4601234567890"}],
                "label_size": "58x40",
            },
        )

        # Должен вернуть 401 (требуется авторизация)
        assert response.status_code == 401
