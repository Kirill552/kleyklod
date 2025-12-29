# Handlers
from bot.handlers.apikey import router as apikey_router
from bot.handlers.generate import router as generate_router
from bot.handlers.history import router as history_router
from bot.handlers.payment import router as payment_router
from bot.handlers.profile import router as profile_router
from bot.handlers.start import router as start_router

__all__ = [
    "start_router",
    "generate_router",
    "profile_router",
    "payment_router",
    "apikey_router",
    "history_router",
]
