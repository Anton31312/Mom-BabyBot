"""
Утилиты для отправки уведомлений через Telegram.

Этот модуль содержит функции для отправки уведомлений пользователям
через Telegram бота.
"""

import logging
import asyncio
import aiohttp
from django.conf import settings
from botapp.models import User, db_manager
from botapp.models_notification import (
    get_notification_preferences, log_notification
)

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """
    Класс для отправки уведомлений через Telegram API.
    """
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(self, chat_id, text, parse_mode="HTML", disable_notification=False):
        """
        Отправить сообщение пользователю через Telegram API.
        
        Аргументы:
            chat_id (int): ID чата пользователя (telegram_id)
            text (str): Текст сообщения
            parse_mode (str, optional): Режим форматирования (HTML, Markdown)
            disable_notification (bool, optional): Отключить звуковое уведомление
            
        Возвращает:
            dict: Ответ от Telegram API или None в случае ошибки
        """
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Error sending Telegram message: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception sending Telegram message: {e}")
            return None
    
    async def send_notification(self, user_id, notification_type, entity_id, text, disable_notification=False):
        """
        Отправить уведомление пользователю с учетом его настроек.
        
        Аргументы:
            user_id (int): ID пользователя в базе данных
            notification_type (str): Тип уведомления
            entity_id (int): ID связанной сущности
            text (str): Текст уведомления
            disable_notification (bool, optional): Отключить звуковое уведомление
            
        Возвращает:
            bool: True если уведомление отправлено успешно, иначе False
        """
        # Получаем пользователя
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.error(f"User with ID {user_id} not found")
                return False
            
            # Получаем настройки уведомлений
            preferences = get_notification_preferences(user_id)
            
            # Если настройки не найдены или уведомления отключены, выходим
            if not preferences or not preferences.enabled or not preferences.telegram_enabled:
                return False
            
            # Проверяем настройки для конкретного типа уведомлений
            if notification_type == 'sleep' and not preferences.sleep_timer_notifications:
                return False
            elif notification_type == 'feeding' and not preferences.feeding_timer_notifications:
                return False
            elif notification_type == 'contraction' and not preferences.contraction_counter_notifications:
                return False
            elif notification_type == 'kick' and not preferences.kick_counter_notifications:
                return False
            elif notification_type == 'vaccine' and not preferences.vaccine_reminder_notifications:
                return False
            
            # Отправляем уведомление
            result = await self.send_message(
                chat_id=user.telegram_id,
                text=text,
                disable_notification=disable_notification
            )
            
            # Логируем отправку
            status = 'sent' if result else 'failed'
            log_notification(
                user_id=user_id,
                notification_type=notification_type,
                entity_id=entity_id,
                channel='telegram',
                content=text,
                status=status
            )
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
        finally:
            db_manager.close_session(session)


# Создаем глобальный экземпляр нотификатора
telegram_notifier = TelegramNotifier()


def send_telegram_notification(user_id, notification_type, entity_id, text, disable_notification=False):
    """
    Синхронная обертка для отправки уведомления через Telegram.
    
    Аргументы:
        user_id (int): ID пользователя в базе данных
        notification_type (str): Тип уведомления
        entity_id (int): ID связанной сущности
        text (str): Текст уведомления
        disable_notification (bool, optional): Отключить звуковое уведомление
        
    Возвращает:
        bool: True если уведомление отправлено успешно, иначе False
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            telegram_notifier.send_notification(
                user_id, notification_type, entity_id, text, disable_notification
            )
        )
    finally:
        loop.close()


def format_sleep_notification(child_name, duration_minutes, sleep_type):
    """
    Форматировать текст уведомления о сне.
    
    Аргументы:
        child_name (str): Имя ребенка
        duration_minutes (int): Продолжительность сна в минутах
        sleep_type (str): Тип сна ('day' или 'night')
        
    Возвращает:
        str: Отформатированный текст уведомления
    """
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    
    if hours > 0:
        duration_text = f"{hours} ч {minutes} мин"
    else:
        duration_text = f"{minutes} мин"
    
    sleep_type_text = "дневного" if sleep_type == "day" else "ночного"
    
    return f"🛌 <b>Сон завершен</b>\n\n" \
           f"Ребенок: <b>{child_name}</b>\n" \
           f"Тип: <b>{sleep_type_text}</b>\n" \
           f"Продолжительность: <b>{duration_text}</b>"


def format_feeding_notification(child_name, feeding_type, amount=None, duration=None, breast=None):
    """
    Форматировать текст уведомления о кормлении.
    
    Аргументы:
        child_name (str): Имя ребенка
        feeding_type (str): Тип кормления ('breast' или 'bottle')
        amount (float, optional): Количество в мл (для бутылочки)
        duration (int, optional): Продолжительность в минутах (для груди)
        breast (str, optional): Используемая грудь ('left', 'right', 'both')
        
    Возвращает:
        str: Отформатированный текст уведомления
    """
    if feeding_type == 'bottle':
        return f"🍼 <b>Кормление из бутылочки</b>\n\n" \
               f"Ребенок: <b>{child_name}</b>\n" \
               f"Количество: <b>{amount} мл</b>"
    else:
        breast_text = {
            'left': 'левая',
            'right': 'правая',
            'both': 'обе'
        }.get(breast, '')
        
        return f"🤱 <b>Грудное вскармливание</b>\n\n" \
               f"Ребенок: <b>{child_name}</b>\n" \
               f"Продолжительность: <b>{duration} мин</b>\n" \
               f"Грудь: <b>{breast_text}</b>"


def format_contraction_notification(count, avg_interval, duration):
    """
    Форматировать текст уведомления о схватках.
    
    Аргументы:
        count (int): Количество схваток
        avg_interval (float): Средний интервал между схватками в минутах
        duration (int): Общая продолжительность в минутах
        
    Возвращает:
        str: Отформатированный текст уведомления
    """
    hours = duration // 60
    minutes = duration % 60
    
    if hours > 0:
        duration_text = f"{hours} ч {minutes} мин"
    else:
        duration_text = f"{minutes} мин"
    
    return f"⏱️ <b>Сессия схваток завершена</b>\n\n" \
           f"Количество схваток: <b>{count}</b>\n" \
           f"Средний интервал: <b>{avg_interval:.1f} мин</b>\n" \
           f"Общая продолжительность: <b>{duration_text}</b>"


def format_kick_notification(count, duration):
    """
    Форматировать текст уведомления о шевелениях.
    
    Аргументы:
        count (int): Количество шевелений
        duration (int): Общая продолжительность в минутах
        
    Возвращает:
        str: Отформатированный текст уведомления
    """
    hours = duration // 60
    minutes = duration % 60
    
    if hours > 0:
        duration_text = f"{hours} ч {minutes} мин"
    else:
        duration_text = f"{minutes} мин"
    
    return f"👶 <b>Сессия шевелений завершена</b>\n\n" \
           f"Количество шевелений: <b>{count}</b>\n" \
           f"Общая продолжительность: <b>{duration_text}</b>"


def format_vaccine_notification(child_name, vaccine_name, due_date):
    """
    Форматировать текст напоминания о прививке.
    
    Аргументы:
        child_name (str): Имя ребенка
        vaccine_name (str): Название вакцины
        due_date (datetime): Дата прививки
        
    Возвращает:
        str: Отформатированный текст уведомления
    """
    formatted_date = due_date.strftime("%d.%m.%Y")
    
    return f"💉 <b>Напоминание о прививке</b>\n\n" \
           f"Ребенок: <b>{child_name}</b>\n" \
           f"Вакцина: <b>{vaccine_name}</b>\n" \
           f"Дата: <b>{formatted_date}</b>"