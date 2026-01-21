
"""
Клиенты API маркетплейсов.

Пока поддерживается только Wildberries.
"""

from .wildberries import WBProduct, WildberriesAPI, WildberriesAPIError

__all__ = ["WildberriesAPI", "WBProduct", "WildberriesAPIError"]

