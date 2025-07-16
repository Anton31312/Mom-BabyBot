import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from botapp.states.states import SurveyStates
from botapp.models import User, get_user, get_sqlalchemy_session
from botapp.keyboards.keyboards import *

logger = logging.getLogger(__name__)

async def start_survey(message: types.Message, state: FSMContext):
    """Начало опроса"""
    try:
        session = get_sqlalchemy_session()
        try:
            user = await get_user(message.from_user.id)
            if not user:
                user = User(telegram_id=message.from_user.id)
                session.add(user)
                session.commit()
            
            await state.set_state(SurveyStates.pregnancy_question)
            await message.answer(
                "Вы беременны или у вас уже есть ребенок?",
                reply_markup=get_pregnancy_keyboard()
            )
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Ошибка при начале опроса: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def handle_pregnancy_answer(message: types.Message, state: FSMContext):
    """Обработка ответа на вопрос о беременности"""
    try:
        session = get_sqlalchemy_session()
        try:
            user = await get_user(message.from_user.id)
            if not user:
                await message.answer("Пожалуйста, начните опрос заново с помощью команды /start")
                return
            
            if message.text == "Да, я беременна":
                user.is_pregnant = True
                await state.set_state(SurveyStates.pregnancy_week)
                await message.answer("На какой неделе беременности вы находитесь?")
            elif message.text == "Нет, у меня есть ребенок":
                user.is_pregnant = False
                await state.set_state(SurveyStates.baby_question)
                await message.answer(
                    "Выберите возраст вашего ребенка:",
                    reply_markup=get_baby_keyboard()
                )
            else:
                await message.answer("Пожалуйста, выберите один из предложенных вариантов.")
            
            session.commit()
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке ответа о беременности: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def handle_pregnancy_week(message: types.Message, state: FSMContext):
    """Обработка недели беременности"""
    try:
        week = int(message.text)
        if not 1 <= week <= 42:
            await message.answer("Пожалуйста, введите корректный срок беременности (от 1 до 42 недель)")
            return

        session = get_sqlalchemy_session()
        try:
            user = await get_user(message.from_user.id)
            if not user:
                await message.answer("Произошла ошибка. Пожалуйста, начните опрос заново с команды /start")
                return

            user.pregnancy_week = week
            session.commit()

            await message.answer(
                f"Отлично! Вы на {week} неделе беременности.\n"
                f"Теперь вы будете получать полезные советы и рекомендации, "
                f"соответствующие вашему сроку беременности.",
                reply_markup=get_main_keyboard(message.from_user.id)
            )
            await state.clear()
        finally:
            session.close()
    except ValueError:
        await message.answer("Пожалуйста, введите число")
    except Exception as e:
        logger.error(f"Ошибка при обработке недели беременности: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз")

async def handle_baby_question(message: types.Message, state: FSMContext):
    """Обработка вопроса о ребенке"""
    try:
        session = get_sqlalchemy_session()
        try:
            user = await get_user(message.from_user.id)
            if not user:
                await message.answer("Произошла ошибка. Пожалуйста, начните опрос заново с команды /start")
                return

            if message.text == "Да, у меня есть ребенок":
                user.is_pregnant = False
                session.commit()
                await message.answer(
                    "Отлично! Теперь укажите возраст вашего ребенка:",
                    reply_markup=get_baby_keyboard()
                )
                await state.set_state(SurveyStates.waiting_for_baby_age)
            else:
                await message.answer(
                    "Пожалуйста, выберите один из предложенных вариантов.",
                    reply_markup=get_main_keyboard(message.from_user.id)
                )
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке вопроса о ребенке: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз")

async def handle_baby_age(message: types.Message, state: FSMContext):
    """Обработка возраста ребенка"""
    try:
        age = message.text
        session = get_sqlalchemy_session()
        try:
            user = await get_user(message.from_user.id)
            if not user:
                await message.answer("Произошла ошибка. Пожалуйста, начните опрос заново с команды /start")
                return

            user.baby_age = age
            session.commit()

            await message.answer(
                f"Отлично! Вашему ребенку {age}.\n"
                f"Теперь вы будете получать полезные советы и рекомендации, "
                f"соответствующие возрасту вашего ребенка.",
                reply_markup=get_main_keyboard(message.from_user.id)
            )
            await state.clear()
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке возраста ребенка: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз")

async def cancel(message: types.Message, state: FSMContext):
    """Отмена опроса"""
    try:
        await state.clear()
        await message.answer(
            "Опрос отменен. Вы можете начать заново с помощью команды /start",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    except Exception as e:
        logger.error(f"Ошибка при отмене опроса: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")