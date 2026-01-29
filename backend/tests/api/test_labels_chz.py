"""Тесты для API endpoint /labels/generate-chz."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateChzEndpoint:
    def test_generate_chz_unauthorized(self):
        """POST /api/v1/labels/generate-chz без авторизации возвращает 401"""
        csv_content = b"010467004977480221JNlMVstBYYuQ91EE0692Wh0KGcGm6HpwZf+7aWtp/DaNgFU="

        response = client.post(
            "/api/v1/labels/generate-chz",
            files={"csv_file": ("codes.csv", csv_content, "text/csv")},
            data={"label_size": "58x40"},
        )

        # Должен вернуть 401 (требуется авторизация)
        assert response.status_code == 401
