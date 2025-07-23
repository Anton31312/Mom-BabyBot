import logging
from aiogram import types
from botapp.models import User, get_sqlalchemy_session
from botapp.keyboards.keyboards import get_inline_keyboard

logger = logging.getLogger(__name__)

async def handle_subscribe(callback: types.CallbackQuery):
    """Обработка запроса на подписку"""
    try:
        session = get_sqlalchemy_session()
        try:
            user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
            if not user:
                await callback.answer("Произошла ошибка. Пожалуйста, начните с команды /start")
                return

            if user.is_premium:
                await callback.answer("У вас уже есть активная премиум-подписка!")
                return

            # Здесь можно добавить логику оплаты
            # Например, генерацию ссылки на оплату или интеграцию с платежной системой
            
            # Временная активация премиум-подписки для демонстрации
            user.is_premium = True
            session.commit()

            await callback.message.edit_text(
                "🎉 Поздравляем! Ваша премиум-подписка активирована!\n\n"
                "Теперь вам доступны:\n"
                "✅ Расширенные советы по беременности и уходу за ребенком\n"
                "✅ Персональные рекомендации\n"
                "✅ Приоритетная поддержка\n"
                "✅ Доступ к эксклюзивному контенту",
                reply_markup=get_inline_keyboard(is_premium=True)
            )
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке подписки: {e}")
        await callback.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def handle_unsubscribe(callback: types.CallbackQuery):
    """Обработка запроса на отмену подписки"""
    try:
        session = get_sqlalchemy_session()
        try:
            user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
            if not user:
                await callback.answer("Произошла ошибка. Пожалуйста, начните с команды /start")
                return

            if not user.is_premium:
                await callback.answer("У вас нет активной премиум-подписки.")
                return

            # Отмена премиум-подписки
            user.is_premium = False
            session.commit()

            await callback.message.edit_text(
                "Премиум-подписка отменена.\n"
                "Вы можете оформить подписку снова в любой момент.",
                reply_markup=get_inline_keyboard(is_premium=False)
            )
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Ошибка при отмене подписки: {e}")
        await callback.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def handle_webapp_unavailable(callback: types.CallbackQuery):
    """Обработка нажатия на кнопку недоступного веб-приложения"""
    await callback.answer("Веб-интерфейс недоступен в локальной среде разработки.")
    
    await callback.message.answer(
        "⚠️ Веб-интерфейс недоступен в локальной среде разработки.\n\n"
        "Для использования веб-интерфейса необходимо:\n"
        "1. Настроить публичный домен с SSL-сертификатом\n"
        "2. Обновить WEBAPP_URL в файле .env\n"
        "3. Запустить приложение на сервере\n\n"
        "Telegram требует, чтобы URL для веб-приложений был публично доступен и использовал HTTPS."
    )