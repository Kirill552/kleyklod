"""
Обработчики команд /start, /help и /settings.
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis

from bot.config import get_bot_settings
from bot.keyboards import get_main_menu_kb, get_settings_kb
from bot.keyboards.inline import (
    get_back_to_menu_kb,
    get_cancel_kb,
    get_help_kb,
    get_template_select_kb,
)
from bot.states import SettingsStates
from bot.utils import UserSettings

logger = logging.getLogger(__name__)

router = Router(name="start")


# Тексты
WELCOME_TEXT = """
<b>КлейКод</b> — этикетки WB + Честный Знак

Загрузите Excel с баркодами → получите PDF для печати.
Качество DataMatrix проверяется автоматически.

<b>Бесплатно:</b> 50 этикеток в месяц
<b>Больше возможностей:</b> kleykod.ru

Подробнее → /help
"""

HELP_TEXT = """
📖 <b>Как работает бот</b>

1️⃣ Отправьте Excel с баркодами WB
2️⃣ Отправьте PDF с кодами Честного Знака
3️⃣ Выберите нумерацию и получите PDF

━━━━━━━━━━━━━━━━━━━━

⚙️ <b>Настройки</b> — шаблон, реквизиты, автосохранение
📦 <b>База товаров</b> (PRO) — автоподстановка данных
🔢 <b>Нумерация</b> — без номеров / с 1 / продолжить
✂️ <b>Диапазон</b> — печать части партии (5-15 из 50)

━━━━━━━━━━━━━━━━━━━━

/start — меню | /settings — настройки
/products — база | /profile — лимиты
/help — справка

💬 @KleyKodSupport | 🌐 kleykod.ru
"""

CONSENT_TEXT = """
<b>Согласие на обработку данных</b>

Для использования сервиса необходимо согласие на обработку персональных данных в соответствии с 152-ФЗ.

Мы храним:
• Ваш Telegram ID (в зашифрованном виде)
• Статистику использования
• Историю генераций (для Pro)

Данные хранятся на серверах в РФ и защищены шифрованием.
"""

SETTINGS_TEXT = """
⚙️ <b>Настройки</b>

📋 <b>Шаблон:</b> {template}
🏢 <b>Организация:</b> {org}
📋 <b>ИНН:</b> {inn}
{autosave_line}
Изменить можно здесь или на сайте в разделе настроек.
"""

NO_SETTINGS_TEXT = """
⚙️ <b>Настройки</b>

<b>Организация:</b> не указана
<b>ИНН:</b> не указан

Данные запросятся при первой генерации или заполните сейчас.
"""

SETTINGS_CLEARED_TEXT = """
<b>Настройки очищены</b>

При следующей генерации данные организации будут запрошены заново.
"""

ENTER_ORG_TEXT = """
<b>Введите название организации</b>

Это название будет использоваться на этикетках.
"""

ENTER_INN_TEXT = """
<b>Введите ИНН организации</b>

ИНН будет использоваться на этикетках.
"""

SETTINGS_SAVED_TEXT = """
<b>Настройки сохранены!</b>

{field}: {value}
"""

TEMPLATE_NAMES = {
    "basic": "Базовый",
    "professional": "Профессиональный",
    "extended": "Расширенный",
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    # Сбрасываем состояние
    await state.clear()

    # TODO: Проверить, зарегистрирован ли пользователь
    # TODO: Если нет — показать согласие на обработку ПДн

    await message.answer(
        WELCOME_TEXT,
        reply_markup=get_main_menu_kb(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    await message.answer(
        HELP_TEXT,
        reply_markup=get_help_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery):
    """Callback для кнопки Помощь."""
    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=get_help_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.edit_text(
        WELCOME_TEXT,
        reply_markup=get_main_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена текущей операции."""
    await state.clear()
    await callback.message.edit_text(
        "Операция отменена.\n\n" + WELCOME_TEXT,
        reply_markup=get_main_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer("Отменено")


@router.callback_query(F.data == "consent_accept")
async def cb_consent_accept(callback: CallbackQuery):
    """Принятие согласия на обработку ПДн."""
    # TODO: Сохранить согласие в БД

    await callback.message.edit_text(
        "Спасибо! Согласие принято.\n\n" + WELCOME_TEXT,
        reply_markup=get_main_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer("Согласие принято")


# Обработка текстовых команд (reply keyboard)
@router.message(F.text == "Помощь")
async def text_help(message: Message):
    """Текстовая команда Помощь."""
    await message.answer(
        HELP_TEXT,
        reply_markup=get_help_kb(),
        parse_mode="HTML",
    )


# ===== Настройки пользователя =====


async def _get_redis() -> Redis:
    """Получить Redis клиент."""
    settings = get_bot_settings()
    return Redis.from_url(settings.redis_url)


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Показать текущие настройки пользователя."""
    telegram_id = message.from_user.id

    redis = await _get_redis()
    try:
        user_settings = UserSettings(redis)
        settings_data = await user_settings.get(telegram_id)

        # Получаем профиль для проверки тарифа
        from bot.utils import get_api_client

        api = get_api_client()
        profile = await api.get_user_profile(telegram_id)
        plan = profile.get("plan", "free") if profile else "free"
        has_auto_save = plan in ("pro", "enterprise")

        if settings_data:
            org = settings_data.get("organization_name") or "не задана"
            inn = settings_data.get("inn") or "не задан"
            layout = settings_data.get("layout", "basic")
            template_name = TEMPLATE_NAMES.get(layout, "Базовый")
            auto_save = settings_data.get("auto_save_products", False)

            autosave_line = ""
            if has_auto_save:
                status = "✅ Вкл" if auto_save else "❌ Выкл"
                autosave_line = f"\n💾 <b>Автосохранение:</b> {status}"

            await message.answer(
                SETTINGS_TEXT.format(
                    template=template_name,
                    org=org,
                    inn=inn,
                    autosave_line=autosave_line,
                ),
                reply_markup=get_settings_kb(has_auto_save, auto_save),
                parse_mode="HTML",
            )
        else:
            await message.answer(
                NO_SETTINGS_TEXT,
                reply_markup=get_settings_kb(has_auto_save, False),
                parse_mode="HTML",
            )
    finally:
        await redis.close()


@router.callback_query(F.data == "settings")
async def cb_settings(callback: CallbackQuery):
    """Показать настройки по кнопке из меню."""
    telegram_id = callback.from_user.id

    redis = await _get_redis()
    try:
        user_settings = UserSettings(redis)
        settings_data = await user_settings.get(telegram_id)

        # Получаем профиль для проверки тарифа
        from bot.utils import get_api_client

        api = get_api_client()
        profile = await api.get_user_profile(telegram_id)
        plan = profile.get("plan", "free") if profile else "free"
        has_auto_save = plan in ("pro", "enterprise")

        if settings_data:
            org = settings_data.get("organization_name") or "не задана"
            inn = settings_data.get("inn") or "не задан"
            layout = settings_data.get("layout", "basic")
            template_name = TEMPLATE_NAMES.get(layout, "Базовый")
            auto_save = settings_data.get("auto_save_products", False)

            autosave_line = ""
            if has_auto_save:
                status = "✅ Вкл" if auto_save else "❌ Выкл"
                autosave_line = f"\n💾 <b>Автосохранение:</b> {status}"

            await callback.message.edit_text(
                SETTINGS_TEXT.format(
                    template=template_name,
                    org=org,
                    inn=inn,
                    autosave_line=autosave_line,
                ),
                reply_markup=get_settings_kb(has_auto_save, auto_save),
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                NO_SETTINGS_TEXT,
                reply_markup=get_settings_kb(has_auto_save, False),
                parse_mode="HTML",
            )
    finally:
        await redis.close()

    await callback.answer()


@router.callback_query(F.data == "settings_org")
async def cb_settings_org(callback: CallbackQuery, state: FSMContext):
    """Начало изменения названия организации."""
    await state.set_state(SettingsStates.waiting_organization)
    await callback.message.edit_text(
        ENTER_ORG_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings_inn")
async def cb_settings_inn(callback: CallbackQuery, state: FSMContext):
    """Начало изменения ИНН."""
    await state.set_state(SettingsStates.waiting_inn)
    await callback.message.edit_text(
        ENTER_INN_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings_clear")
async def cb_settings_clear(callback: CallbackQuery):
    """Очистка всех настроек пользователя."""
    telegram_id = callback.from_user.id

    redis = await _get_redis()
    try:
        user_settings = UserSettings(redis)
        await user_settings.clear(telegram_id)
        logger.info(f"[SETTINGS] Настройки очищены для пользователя {telegram_id}")

        await callback.message.edit_text(
            SETTINGS_CLEARED_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
    finally:
        await redis.close()

    await callback.answer("Настройки очищены")


@router.callback_query(F.data == "settings_template")
async def cb_settings_template(callback: CallbackQuery, state: FSMContext):
    """Показать выбор шаблона с фото-коллажем."""
    from pathlib import Path

    from aiogram.types import FSInputFile

    telegram_id = callback.from_user.id

    redis = await _get_redis()
    try:
        user_settings = UserSettings(redis)
        settings_data = await user_settings.get(telegram_id)
        current = settings_data.get("layout", "basic") if settings_data else "basic"

        # Отправляем фото-коллаж
        collage_path = Path(__file__).parent.parent / "assets" / "templates-collage.png"
        photo = FSInputFile(collage_path)

        await state.set_state(SettingsStates.selecting_template)

        # Удаляем старое сообщение и отправляем фото
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption="<b>Выберите шаблон этикетки</b>",
            reply_markup=get_template_select_kb(current),
            parse_mode="HTML",
        )
    finally:
        await redis.close()

    await callback.answer()


@router.callback_query(SettingsStates.selecting_template, F.data.startswith("template:"))
async def cb_template_selected(callback: CallbackQuery, state: FSMContext):
    """Сохранить выбранный шаблон."""
    telegram_id = callback.from_user.id
    template = callback.data.split(":")[1]

    redis = await _get_redis()
    try:
        user_settings = UserSettings(redis)
        await user_settings.save(telegram_id, layout=template)
        logger.info(f"[SETTINGS] Шаблон {template} сохранён для пользователя {telegram_id}")

        template_name = TEMPLATE_NAMES.get(template, template)

        # Удаляем фото и отправляем текстовое подтверждение
        await callback.message.delete()
        await callback.message.answer(
            SETTINGS_SAVED_TEXT.format(field="Шаблон", value=template_name),
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
    finally:
        await redis.close()

    await state.clear()
    await callback.answer("Шаблон сохранён")


@router.callback_query(F.data.startswith("settings_autosave:"))
async def cb_toggle_autosave(callback: CallbackQuery):
    """Переключить автосохранение товаров."""
    telegram_id = callback.from_user.id
    action = callback.data.split(":")[1]
    new_value = action == "on"

    redis = await _get_redis()
    try:
        user_settings = UserSettings(redis)
        await user_settings.save(telegram_id, auto_save_products=new_value)
        logger.info(f"[SETTINGS] Автосохранение {'вкл' if new_value else 'выкл'} для {telegram_id}")
    finally:
        await redis.close()

    status = "включено" if new_value else "выключено"
    await callback.answer(f"Автосохранение {status}")

    # Перерисовываем настройки
    await cb_settings(callback)


@router.message(SettingsStates.waiting_organization, F.text)
async def receive_organization(message: Message, state: FSMContext):
    """Получение нового названия организации."""
    telegram_id = message.from_user.id
    organization_name = message.text.strip()

    redis = await _get_redis()
    try:
        user_settings = UserSettings(redis)
        await user_settings.save(telegram_id, organization_name=organization_name)
        logger.info(f"[SETTINGS] Организация сохранена для пользователя {telegram_id}")

        await message.answer(
            SETTINGS_SAVED_TEXT.format(field="Организация", value=organization_name),
            reply_markup=get_settings_kb(),
            parse_mode="HTML",
        )
    finally:
        await redis.close()

    await state.clear()


@router.message(SettingsStates.waiting_inn, F.text)
async def receive_inn(message: Message, state: FSMContext):
    """Получение нового ИНН."""
    telegram_id = message.from_user.id
    inn = message.text.strip()

    # Валидация ИНН (10 или 12 цифр)
    if not inn.isdigit() or len(inn) not in (10, 12):
        await message.answer(
            "ИНН должен содержать 10 или 12 цифр. Попробуйте ещё раз.",
            reply_markup=get_cancel_kb(),
        )
        return

    redis = await _get_redis()
    try:
        user_settings = UserSettings(redis)
        await user_settings.save(telegram_id, inn=inn)
        logger.info(f"[SETTINGS] ИНН сохранен для пользователя {telegram_id}")

        await message.answer(
            SETTINGS_SAVED_TEXT.format(field="ИНН", value=inn),
            reply_markup=get_settings_kb(),
            parse_mode="HTML",
        )
    finally:
        await redis.close()

    await state.clear()
