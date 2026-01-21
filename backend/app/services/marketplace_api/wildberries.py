"""
Клиент Wildberries Content API.

Документация: https://dev.wildberries.ru/openapi/api-information
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# WB Content API
WB_API_URL = "https://content-api.wildberries.ru"


@dataclass
class WBProduct:
    """Товар с Wildberries."""

    barcode: str
    name: str
    article: str | None = None
    brand: str | None = None
    size: str | None = None
    color: str | None = None
    nm_id: int | None = None  # Артикул WB


class WildberriesAPIError(Exception):
    """Ошибка WB API."""

    pass


class WildberriesAPI:
    """
    Клиент Wildberries Content API.

    Использование:
        api = WildberriesAPI(api_key="...")
        if await api.validate():
            products = await api.get_all_products()
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": api_key}

    async def validate(self) -> bool:
        """
        Проверить валидность API ключа.

        Returns:
            True если ключ валиден
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{WB_API_URL}/content/v2/get/cards/list",
                    headers=self.headers,
                    json={"settings": {"cursor": {"limit": 1}}},
                )

                if response.status_code == 401:
                    return False
                if response.status_code == 200:
                    return True

                # Другие ошибки
                logger.warning(f"WB API validate: status={response.status_code}")
                return False

        except httpx.RequestError as e:
            logger.error(f"WB API validate error: {e}")
            return False

    async def get_products_count(self) -> int:
        """
        Получить количество товаров.

        Returns:
            Количество карточек товаров
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{WB_API_URL}/content/v2/get/cards/list",
                    headers=self.headers,
                    json={"settings": {"cursor": {"limit": 1}}},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("cursor", {}).get("total", 0)

        except httpx.HTTPStatusError as e:
            raise WildberriesAPIError(f"HTTP {e.response.status_code}") from e
        except Exception as e:
            raise WildberriesAPIError(str(e)) from e

    async def get_all_products(self, limit: int = 100) -> list[WBProduct]:
        """
        Получить все товары с пагинацией.

        Args:
            limit: Товаров за запрос (max 100)

        Returns:
            Список товаров
        """
        products: list[WBProduct] = []
        cursor = {"limit": min(limit, 100)}

        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                try:
                    response = await client.post(
                        f"{WB_API_URL}/content/v2/get/cards/list",
                        headers=self.headers,
                        json={"settings": {"cursor": cursor}},
                    )
                    response.raise_for_status()
                    data = response.json()

                except httpx.HTTPStatusError as e:
                    raise WildberriesAPIError(f"HTTP {e.response.status_code}") from e
                except Exception as e:
                    raise WildberriesAPIError(str(e)) from e

                cards = data.get("cards", [])
                if not cards:
                    break

                for card in cards:
                    # Извлекаем данные карточки
                    nm_id = card.get("nmID")
                    vendor_code = card.get("vendorCode", "")
                    brand = card.get("brand", "")

                    # Название и цвет из характеристик
                    name = ""
                    color = None
                    for char in card.get("characteristics", []):
                        char_name = char.get("name", "")
                        if char_name == "Предмет":
                            name = str(char.get("value", ""))
                        elif char_name == "Цвет":
                            color = str(char.get("value", ""))
                    if not name:
                        name = card.get("subjectName", vendor_code)

                    # Размеры и баркоды
                    for size_data in card.get("sizes", []):
                        tech_size = size_data.get("techSize", "")

                        for barcode in size_data.get("skus", []):
                            products.append(
                                WBProduct(
                                    barcode=barcode,
                                    name=name,
                                    article=vendor_code,
                                    brand=brand,
                                    size=tech_size if tech_size else None,
                                    color=color,
                                    nm_id=nm_id,
                                )
                            )

                # Пагинация
                cursor_data = data.get("cursor", {})
                nm_id_next = cursor_data.get("nmID")
                updated_at_next = cursor_data.get("updatedAt")

                if not nm_id_next:
                    break

                cursor = {
                    "limit": min(limit, 100),
                    "nmID": nm_id_next,
                    "updatedAt": updated_at_next,
                }

        return products
