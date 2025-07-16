from aiogram import types
from botapp.models import User, get_sqlalchemy_session

async def web_app_data(message: types.Message):
    """Обработчик данных от веб-приложения"""
    try:
        session = get_sqlalchemy_session()
        try:
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
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
                
            session.commit()
            
            await message.answer("Данные успешно обновлены!")
        finally:
            session.close()
        
    except Exception as e:
        await message.answer("Произошла ошибка при обновлении данных. Попробуйте позже.")