from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from django.conf import settings


def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Создает основную клавиатуру"""
    keyboard = [
        [KeyboardButton(text="📊 Статистика")] if user_id in getattr(settings, 'ADMIN_IDS', []) else [],
        [KeyboardButton(text="❓ Помощь")],
    ]
    
    # Only add the Web App button if not running locally
    webapp_url = getattr(settings, 'WEBAPP_URL', '')
    if webapp_url and not ('localhost' in webapp_url or '127.0.0.1' in webapp_url):
        keyboard.append([KeyboardButton(text="🌐 Открыть приложение", web_app={"url": webapp_url})])
    else:
        keyboard.append([KeyboardButton(text="🌐 Веб-интерфейс недоступен локально")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_pregnancy_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для вопроса о беременности"""
    keyboard = [
        [KeyboardButton(text="Да, я беременна")],
        [KeyboardButton(text="Нет, у меня есть ребенок")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_baby_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для выбора возраста ребенка"""
    keyboard = [
        [KeyboardButton(text="0-3 месяца")],
        [KeyboardButton(text="3-6 месяцев")],
        [KeyboardButton(text="6-12 месяцев")],
        [KeyboardButton(text="1-2 года")],
        [KeyboardButton(text="2-3 года")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_inline_keyboard(is_premium: bool = False) -> InlineKeyboardMarkup:
    """Создает инлайн-клавиатуру для премиум-подписки"""
    keyboard = []
    if is_premium:
        keyboard.append([InlineKeyboardButton(text="❌ Отписаться", callback_data="unsubscribe")])
    else:
        keyboard.append([InlineKeyboardButton(text="⭐️ Подписаться", callback_data="subscribe")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_yes_no_keyboard():
    """Создает клавиатуру с кнопками Да/Нет"""
    keyboard = [
        [KeyboardButton("Да"), KeyboardButton("Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_pregnancy_weeks_keyboard():
    """Создает клавиатуру для выбора срока беременности"""
    keyboard = [
        [str(i) for i in range(1, 4)],
        [str(i) for i in range(4, 7)],
        [str(i) for i in range(7, 10)],
        ["Более 9 месяцев"]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_baby_age_keyboard():
    """Создает клавиатуру для выбора возраста ребенка"""
    keyboard = [
        ["До 1 года"],
        ["1-2 года"],
        ["2-3 года"],
        ["Более 3 лет"]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_web_app_keyboard(webapp_url):
    """Создает клавиатуру с кнопкой веб-приложения"""
    # Check if the URL is valid (not localhost or 127.0.0.1)
    if webapp_url and not ('localhost' in webapp_url or '127.0.0.1' in webapp_url):
        return {
            "inline_keyboard": [[
                {"text": "📱 Открыть приложение", "web_app": {"url": webapp_url}}
            ]]
        }
    else:
        # Return a simple message button instead
        return {
            "inline_keyboard": [[
                {"text": "⚠️ Веб-интерфейс недоступен локально", "callback_data": "webapp_unavailable"}
            ]]
        }

def remove_keyboard() -> ReplyKeyboardRemove:
    """Удаляет клавиатуру"""
    return ReplyKeyboardRemove()