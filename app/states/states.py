from aiogram.fsm.state import State, StatesGroup

class SurveyStates(StatesGroup):
    """Состояния для опроса"""
    pregnancy_question = State()
    pregnancy_week = State()
    baby_question = State()
    baby_age = State() 