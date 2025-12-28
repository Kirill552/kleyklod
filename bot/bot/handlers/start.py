"""
Обработчики команд /start и /help.
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import get_main_menu_kb
from bot.keyboards.inline import get_back_to_menu_kb

router = Router(name="start")


# Тексты
WELCOME_TEXT = """
<b>KleyKod</b> — генератор этикеток для Wildberries

Объедините штрихкод WB и код Честного Знака в одну наклейку за секунды.

<b>Что умеет бот:</b>
• Склеивает PDF от WB и CSV с кодами ЧЗ
• Проверяет качество DataMatrix до печати
• Генерирует этикетки 58x40мм для термопринтера

<b>Бесплатно:</b> 50 этикеток в день

Нажмите «Создать этикетки» чтобы начать.
"""

HELP_TEXT = """
<b>Как создать этикетки:</b>

1. Нажмите «Создать этикетки»
2. Отправьте PDF с этикетками от Wildberries
3. Отправьте CSV/Excel файл с кодами Честного Знака
4. Получите готовый PDF для печати!

<b>Команды:</b>
/start — Главное меню
/help — Эта справка
/profile — Ваш профиль и статистика
/plans — Тарифные планы

<b>Поддержка:</b>
Вопросы → @KleyKodSupport
"""

ABOUT_TEXT = """
<b>О сервисе KleyKod</b>

KleyKod — это сервис для селлеров Wildberries и Ozon, который решает проблему «двух наклеек».

<b>Почему мы лучше:</b>
• Скорость: 1000 этикеток за 5 секунд
• Проверка качества: убережём от штрафов
• Прозрачные цены: 50 шт/день бесплатно

<b>Контакты:</b>
Сайт: kleykod.ru
Telegram: @KleyKodBot
Поддержка: @KleyKodSupport
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
        reply_markup=get_back_to_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery):
    """Callback для кнопки Помощь."""
    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=get_back_to_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery):
    """Callback для кнопки О сервисе."""
    await callback.message.edit_text(
        ABOUT_TEXT,
        reply_markup=get_back_to_menu_kb(),
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
        reply_markup=get_back_to_menu_kb(),
        parse_mode="HTML",
    )
