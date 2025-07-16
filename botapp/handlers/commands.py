import logging
from aiogram import types
from django.conf import settings
from botapp.models import User, get_sqlalchemy_session
from botapp.keyboards.keyboards import get_main_keyboard

# Настройка логирования
logging.basicConfig(
    level=getattr(settings, 'LOG_LEVEL', logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Список команд бота (без stats, так как она только для админов)
BOT_COMMANDS = [
    types.BotCommand(command="start", description="Начать опрос"),
    types.BotCommand(command="help", description="Помощь"),
    types.BotCommand(command="webapp", description="Открыть веб-приложение"),
    types.BotCommand(command="cancel", description="Отменить текущее действие")
]

# Список команд для администраторов
ADMIN_COMMANDS = BOT_COMMANDS + [
    types.BotCommand(command="stats", description="Статистика (только для администраторов)")
]

async def help_command(message: types.Message):
    """Обработчик команды /help и кнопки help"""
    help_text = """
🤖 Mom&BabyBot - ваш помощник во время беременности и после рождения ребенка.

📝 Основные команды:
/start - Начать опрос
/help - Показать это сообщение
/cancel - Отменить текущее действие

💡 Возможности бота:
• Отслеживание срока беременности
• Отслеживание возраста ребенка
• Получение полезных советов
• Персональные рекомендации

⭐️ Премиум-подписка:
• Расширенные советы
• Персональные рекомендации
• Эксклюзивные материалы

❓ Как использовать бота:
1. Начните с команды /start
2. Ответьте на вопросы о вашем статусе
3. Получайте полезные советы и рекомендации
4. Используйте кнопки меню для навигации

📱 Веб-интерфейс:
• Удобное управление данными
• Визуализация статистики
• Настройка уведомлений
• Управление подпиской
"""
    await message.answer(help_text, reply_markup=get_main_keyboard(message.from_user.id))

async def stats(message: types.Message):
    """Обработчик команды /stats и кнопки stats (только для администраторов)"""
    try:
        if message.from_user.id not in getattr(settings, 'ADMIN_IDS', []):
            await message.answer("У вас нет доступа к этой команде.")
            return
        
        # Получаем статистику через SQLAlchemy сессию
        session = get_sqlalchemy_session()
        try:
            total_users = session.query(User).count()
            pregnant_users = session.query(User).filter_by(is_pregnant=True).count()
            baby_users = session.query(User).filter_by(is_pregnant=False).count()
            premium_users = session.query(User).filter_by(is_premium=True).count()
            
            stats_text = f"""
📊 Статистика бота:

👥 Всего пользователей: {total_users}
🤰 Беременных: {pregnant_users}
👶 С детьми: {baby_users}
⭐️ Премиум-подписчиков: {premium_users}
"""
            await message.answer(stats_text, reply_markup=get_main_keyboard(message.from_user.id))
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer("Произошла ошибка при получении статистики.")

async def webapp_command(message: types.Message):
    """Обработчик команды /webapp и кнопки веб-приложения"""
    webapp_text = """
🌐 Telegram Mini App

Нажмите на кнопку ниже, чтобы открыть веб-приложение:
"""
    await message.answer(
        webapp_text,
        reply_markup=get_main_keyboard(message.from_user.id)
    )