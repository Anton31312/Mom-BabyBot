from aiogram import types
from app.models.user import User, db

async def web_app_data(message: types.Message):
    """Обработчик данных от веб-приложения"""
    try:
        user = User.query.filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("Произошла ошибка. Пожалуйста, начните опрос заново с помощью /start")
            return
            
        # Получаем данные из web app
        data = message.web_app_data.data
        
        # Обновляем данные пользователя
        if user.is_pregnant:
            user.pregnancy_week = data.get('pregnancy_week')
        else:
            user.baby_age = data.get('baby_age')
            
        db.session.commit()
        
        await message.answer("Данные успешно обновлены!")
        
    except Exception as e:
        await message.answer("Произошла ошибка при обновлении данных. Попробуйте позже.") 