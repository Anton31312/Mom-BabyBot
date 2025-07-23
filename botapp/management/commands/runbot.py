import logging
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command as AiogramCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from botapp.handlers import *
from botapp.states.states import SurveyStates

# Настройка логирования
logging.basicConfig(
    level=getattr(settings, 'LOG_LEVEL', logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запуск Telegram бота'

    def add_arguments(self, parser):
        parser.add_argument(
            '--webhook',
            action='store_true',
            help='Запуск в режиме webhook',
        )

    def handle(self, *args, **options):
        """Основной метод команды"""
        if options['webhook']:
            self.stdout.write('Запуск бота в режиме webhook...')
            # Здесь можно добавить логику для webhook режима
        else:
            self.stdout.write('Запуск бота в режиме polling...')
            asyncio.run(self.run_bot())

    async def run_bot(self):
        """Запуск бота"""
        try:
            # Создаем экземпляры бота и диспетчера
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            storage = MemoryStorage()
            dp = Dispatcher(storage=storage)

            # Регистрация хендлеров команд
            dp.message.register(start_survey, AiogramCommand("start"))
            dp.message.register(help_command, AiogramCommand("help"))
            dp.message.register(help_command, lambda message: message.text == "❓ Помощь")
            dp.message.register(stats, AiogramCommand("stats"))
            dp.message.register(stats, lambda message: message.text == "📊 Статистика")
            dp.message.register(webapp_command, AiogramCommand("webapp"))
            dp.message.register(webapp_command, lambda message: message.text == "🌐 Открыть приложение")
            dp.message.register(cancel, AiogramCommand("cancel"))
            dp.message.register(web_app_data, lambda message: message.web_app_data is not None)

            # Регистрация callback-обработчиков для премиум-подписки
            dp.callback_query.register(handle_subscribe, lambda c: c.data == "subscribe")
            dp.callback_query.register(handle_unsubscribe, lambda c: c.data == "unsubscribe")
            dp.callback_query.register(handle_webapp_unavailable, lambda c: c.data == "webapp_unavailable")

            # Регистрация хендлеров для опроса
            dp.message.register(handle_pregnancy_answer, SurveyStates.pregnancy_question)
            dp.message.register(handle_pregnancy_week, SurveyStates.pregnancy_week)
            dp.message.register(handle_baby_question, SurveyStates.baby_question)
            dp.message.register(handle_baby_age, SurveyStates.baby_age)
            dp.message.register(handle_baby_age, SurveyStates.waiting_for_baby_age)

            # Установка команд бота
            await self.set_commands(bot)

            logger.info("Бот запущен...")
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise
        finally:
            if 'bot' in locals():
                await bot.session.close()

    async def set_commands(self, bot: Bot):
        """Установка команд бота"""
        try:
            # Устанавливаем команды для всех пользователей
            await bot.set_my_commands(BOT_COMMANDS)
            
            # Устанавливаем команды для администраторов
            admin_ids = getattr(settings, 'ADMIN_IDS', [])
            for admin_id in admin_ids:
                try:
                    await bot.set_my_commands(
                        ADMIN_COMMANDS, 
                        scope=types.BotCommandScopeChat(chat_id=admin_id)
                    )
                except Exception as e:
                    logger.error(f"Ошибка при установке команд для администратора {admin_id}: {e}")
                    
            logger.info("Команды бота установлены")
        except Exception as e:
            logger.error(f"Ошибка при установке команд: {e}")