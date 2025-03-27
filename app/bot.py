import logging
import asyncio
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import Config
from app.handlers.commands import help_command, stats, webapp_command, BOT_COMMANDS, ADMIN_COMMANDS
from app.handlers.conversation import *
from app.handlers.web_app import web_app_data
from app.handlers.callbacks import handle_subscribe, handle_unsubscribe
from app.states.states import SurveyStates

# Настройка логирования
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные для управления ботом
bot = None
dp = None
scheduler = None
bot_thread = None
is_running = False
flask_app = None

def create_bot(app):
    """Создание экземпляров бота и диспетчера"""
    global bot, dp, scheduler, flask_app
    flask_app = app
    
    # Создаем экземпляры бота и диспетчера
    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    scheduler = AsyncIOScheduler()

    # Добавляем конфигурацию в контекст приложения
    with app.app_context():
        app.config['ADMIN_IDS'] = Config.ADMIN_IDS

    # Создаем обертки для обработчиков с контекстом приложения
    async def start_survey_wrapper(message: types.Message, state: FSMContext):
        with app.app_context():
            await start_survey(message, state)

    async def handle_pregnancy_answer_wrapper(message: types.Message, state: FSMContext):
        with app.app_context():
            await handle_pregnancy_answer(message, state)

    async def handle_pregnancy_week_wrapper(message: types.Message, state: FSMContext):
        with app.app_context():
            await handle_pregnancy_week(message, state)

    async def handle_baby_question_wrapper(message: types.Message, state: FSMContext):
        with app.app_context():
            await handle_baby_question(message, state)

    async def handle_baby_age_wrapper(message: types.Message, state: FSMContext):
        with app.app_context():
            await handle_baby_age(message, state)

    async def cancel_wrapper(message: types.Message, state: FSMContext):
        with app.app_context():
            await cancel(message, state)

    async def web_app_data_wrapper(message: types.Message):
        with app.app_context():
            await web_app_data(message)

    async def stats_wrapper(message: types.Message):
        with app.app_context():
            await stats(message)

    # Регистрация хендлеров с обертками
    dp.message.register(start_survey_wrapper, Command("start"))
    dp.message.register(help_command, Command("help"))
    dp.message.register(help_command, lambda message: message.text == "❓ Помощь")
    dp.message.register(stats_wrapper, Command("stats"))
    dp.message.register(stats_wrapper, lambda message: message.text == "📊 Статистика")
    dp.message.register(webapp_command, Command("webapp"))
    dp.message.register(webapp_command, lambda message: message.text == "🌐 Открыть приложение")
    dp.message.register(cancel_wrapper, Command("cancel"))
    dp.message.register(web_app_data_wrapper, lambda message: message.web_app_data is not None)

    # Регистрация callback-обработчиков для премиум-подписки
    dp.callback_query.register(handle_subscribe, lambda c: c.data == "subscribe")
    dp.callback_query.register(handle_unsubscribe, lambda c: c.data == "unsubscribe")

    # Регистрация хендлеров для опроса
    dp.message.register(handle_pregnancy_answer_wrapper, SurveyStates.pregnancy_question)
    dp.message.register(handle_pregnancy_week_wrapper, SurveyStates.pregnancy_week)
    dp.message.register(handle_baby_question_wrapper, SurveyStates.baby_question)
    dp.message.register(handle_baby_age_wrapper, SurveyStates.baby_age)

async def set_commands():
    """Установка команд бота"""
    # Устанавливаем команды для всех пользователей
    await bot.set_my_commands(BOT_COMMANDS)
    
    # Устанавливаем команды для администраторов
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.set_my_commands(ADMIN_COMMANDS, scope=types.BotCommandScopeChat(chat_id=admin_id))
        except Exception as e:
            logger.error(f"Ошибка при установке команд для администратора {admin_id}: {e}")

async def main():
    """Основная функция запуска бота"""
    global is_running
    try:
        logger.info("Запуск бота...")
        await set_commands()
        is_running = True
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        is_running = False
        raise
    finally:
        is_running = False
        if bot:
            await bot.session.close()

def run_async_bot():
    """Запуск бота в отдельном потоке"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Ошибка в потоке бота: {e}")
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except Exception as e:
            logger.error(f"Ошибка при закрытии цикла событий: {e}")

def run_bot(app):
    """Запуск бота в отдельном потоке"""
    global bot_thread, is_running
    
    if is_running:
        logger.warning("Бот уже запущен")
        return bot_thread
    
    # Создаем экземпляры бота и диспетчера
    create_bot(app)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_async_bot, name="BotThread")
    bot_thread.daemon = True
    bot_thread.start()
    
    return bot_thread

def stop_bot():
    """Остановка бота"""
    global is_running, bot_thread, bot, dp
    
    if not is_running:
        logger.warning("Бот не запущен")
        return
    
    is_running = False
    
    try:
        if dp:
            asyncio.run(dp.stop_polling())
        if bot:
            asyncio.run(bot.session.close())
    except Exception as e:
        logger.error(f"Ошибка при остановке бота: {e}")
    
    if bot_thread and bot_thread.is_alive():
        bot_thread.join(timeout=5)
        if bot_thread.is_alive():
            logger.warning("Не удалось корректно остановить бота")
    
    bot_thread = None
    bot = None
    dp = None
    logger.info("Бот остановлен") 