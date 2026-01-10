"""
Тест импорта модуля payment для проверки синтаксиса.
"""

import sys
from pathlib import Path

# Добавляем путь к модулю бота
bot_path = Path(__file__).parent
sys.path.insert(0, str(bot_path))

try:
    # Пытаемся импортировать модуль payment
    from bot.handlers import payment

    print("✓ Модуль payment успешно импортирован")
    print(f"✓ Router name: {payment.router.name}")
    print(f"✓ Найдено обработчиков: {len(payment.router.observers)}")
    print(f"✓ Цены определены: {list(payment.PRICES.keys())}")

    # Проверяем наличие основных функций
    handlers = [
        "handle_deep_link_payment",
        "cb_buy_pro",
        "cb_buy_enterprise",
        "pre_checkout",
        "successful_payment",
        "cb_payment_history",
    ]

    for handler_name in handlers:
        if hasattr(payment, handler_name):
            print(f"✓ Обработчик {handler_name} найден")
        else:
            print(f"✗ Обработчик {handler_name} НЕ найден")

    print("\n✓ Все проверки пройдены!")
    sys.exit(0)

except SyntaxError as e:
    print(f"✗ Ошибка синтаксиса: {e}")
    sys.exit(1)

except ImportError as e:
    print(f"✗ Ошибка импорта: {e}")
    sys.exit(1)

except Exception as e:
    print(f"✗ Неожиданная ошибка: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
