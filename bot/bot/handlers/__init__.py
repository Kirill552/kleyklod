# Handlers
from bot.handlers.start import router as start_router
from bot.handlers.generate import router as generate_router
from bot.handlers.profile import router as profile_router
from bot.handlers.payment import router as payment_router

__all__ = ["start_router", "generate_router", "profile_router", "payment_router"]
