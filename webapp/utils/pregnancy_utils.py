"""
Утилиты для работы с беременностью и расчета недель беременности.

Этот модуль содержит функции для расчета текущей недели беременности,
определения важных дат и другие вспомогательные функции.
"""

from datetime import date, timedelta
from django.utils import timezone
from typing import Dict, Optional, Tuple


def calculate_pregnancy_start_date(due_date: date, 
                                 last_menstrual_period: Optional[date] = None,
                                 conception_date: Optional[date] = None) -> date:
    """
    Рассчитывает дату начала беременности на основе доступных данных.
    
    Args:
        due_date (date): Предполагаемая дата родов
        last_menstrual_period (date, optional): Дата последней менструации
        conception_date (date, optional): Дата зачатия
        
    Returns:
        date: Дата начала беременности
    """
    if last_menstrual_period:
        return last_menstrual_period
    elif conception_date:
        # Если известна дата зачатия, отнимаем 14 дней (овуляция обычно на 14 день цикла)
        return conception_date - timedelta(days=14)
    else:
        # Рассчитываем от ПДР (280 дней назад)
        return due_date - timedelta(days=280)


def calculate_current_pregnancy_week(start_date: date, 
                                   is_active: bool = True,
                                   reference_date: Optional[date] = None) -> Optional[int]:
    """
    Рассчитывает текущую неделю беременности.
    
    Args:
        start_date (date): Дата начала беременности
        is_active (bool): Активна ли беременность
        reference_date (date, optional): Дата для расчета (по умолчанию сегодня)
        
    Returns:
        int: Номер недели беременности (1-42) или None если беременность неактивна
    """
    if not is_active:
        return None
    
    if reference_date is None:
        reference_date = timezone.now().date()
    
    # Если беременность еще не началась
    if reference_date < start_date:
        return 0
    
    # Рассчитываем количество дней с начала беременности
    days_pregnant = (reference_date - start_date).days
    
    # Переводим в недели (начинаем с 1 недели)
    weeks = (days_pregnant // 7) + 1
    
    # Ограничиваем максимум 42 неделями
    return min(weeks, 42)


def calculate_current_day_of_week(start_date: date,
                                is_active: bool = True,
                                reference_date: Optional[date] = None) -> Optional[int]:
    """
    Рассчитывает текущий день недели беременности.
    
    Args:
        start_date (date): Дата начала беременности
        is_active (bool): Активна ли беременность
        reference_date (date, optional): Дата для расчета (по умолчанию сегодня)
        
    Returns:
        int: День недели (1-7) или None если беременность неактивна
    """
    if not is_active:
        return None
    
    if reference_date is None:
        reference_date = timezone.now().date()
    
    if reference_date < start_date:
        return 0
    
    days_pregnant = (reference_date - start_date).days
    return (days_pregnant % 7) + 1


def calculate_days_until_due(due_date: date, 
                           reference_date: Optional[date] = None) -> int:
    """
    Рассчитывает количество дней до ПДР.
    
    Args:
        due_date (date): Предполагаемая дата родов
        reference_date (date, optional): Дата для расчета (по умолчанию сегодня)
        
    Returns:
        int: Количество дней (может быть отрицательным, если ПДР прошла)
    """
    if reference_date is None:
        reference_date = timezone.now().date()
    
    return (due_date - reference_date).days


def calculate_weeks_until_due(due_date: date,
                            reference_date: Optional[date] = None) -> int:
    """
    Рассчитывает количество недель до ПДР.
    
    Args:
        due_date (date): Предполагаемая дата родов
        reference_date (date, optional): Дата для расчета (по умолчанию сегодня)
        
    Returns:
        int: Количество недель
    """
    days_until = calculate_days_until_due(due_date, reference_date)
    return days_until // 7


def determine_trimester(current_week: Optional[int]) -> Optional[int]:
    """
    Определяет текущий триместр беременности.
    
    Args:
        current_week (int): Текущая неделя беременности
        
    Returns:
        int: Номер триместра (1, 2, 3) или None если неделя не определена
    """
    if not current_week:
        return None
    
    if current_week <= 12:
        return 1
    elif current_week <= 28:
        return 2
    else:
        return 3


def calculate_progress_percentage(current_week: Optional[int]) -> float:
    """
    Рассчитывает процент прогресса беременности.
    
    Args:
        current_week (int): Текущая неделя беременности
        
    Returns:
        float: Процент от 0 до 100
    """
    if not current_week:
        return 0
    
    # Считаем прогресс от 40 недель (стандартная длительность)
    return min((current_week / 40) * 100, 100)


def is_pregnancy_overdue(due_date: date,
                        reference_date: Optional[date] = None) -> bool:
    """
    Проверяет, просрочена ли беременность.
    
    Args:
        due_date (date): Предполагаемая дата родов
        reference_date (date, optional): Дата для проверки (по умолчанию сегодня)
        
    Returns:
        bool: True если ПДР прошла
    """
    days_until = calculate_days_until_due(due_date, reference_date)
    return days_until < 0


def is_pregnancy_full_term(current_week: Optional[int]) -> bool:
    """
    Проверяет, является ли беременность доношенной (37+ недель).
    
    Args:
        current_week (int): Текущая неделя беременности
        
    Returns:
        bool: True если беременность доношенная
    """
    return current_week and current_week >= 37


def is_pregnancy_preterm_risk(current_week: Optional[int]) -> bool:
    """
    Проверяет, есть ли риск преждевременных родов (32-36 недель).
    
    Args:
        current_week (int): Текущая неделя беременности
        
    Returns:
        bool: True если есть риск преждевременных родов
    """
    return current_week and 32 <= current_week < 37


def get_week_description(current_week: Optional[int]) -> str:
    """
    Возвращает описание текущей недели беременности.
    
    Args:
        current_week (int): Текущая неделя беременности
        
    Returns:
        str: Описание недели
    """
    if current_week is None:
        return "Беременность неактивна"
    
    if current_week == 0:
        return "Беременность еще не началась"
    elif current_week <= 4:
        return f"{current_week} неделя - Имплантация и раннее развитие"
    elif current_week <= 8:
        return f"{current_week} неделя - Формирование основных органов"
    elif current_week <= 12:
        return f"{current_week} неделя - Первый триместр, завершение органогенеза"
    elif current_week <= 16:
        return f"{current_week} неделя - Второй триместр, активный рост"
    elif current_week <= 20:
        return f"{current_week} неделя - Середина беременности"
    elif current_week <= 24:
        return f"{current_week} неделя - Развитие легких и мозга"
    elif current_week <= 28:
        return f"{current_week} неделя - Конец второго триместра"
    elif current_week <= 32:
        return f"{current_week} неделя - Третий триместр, набор веса"
    elif current_week <= 36:
        return f"{current_week} неделя - Подготовка к родам"
    elif current_week <= 40:
        return f"{current_week} неделя - Доношенная беременность"
    else:
        return f"{current_week} неделя - Переношенная беременность"


def get_important_pregnancy_dates(start_date: date, due_date: date) -> Dict[str, date]:
    """
    Возвращает важные даты беременности.
    
    Args:
        start_date (date): Дата начала беременности
        due_date (date): Предполагаемая дата родов
        
    Returns:
        dict: Словарь с важными датами
    """
    return {
        'start_date': start_date,
        'first_trimester_end': start_date + timedelta(weeks=12),
        'second_trimester_end': start_date + timedelta(weeks=28),
        'full_term_start': start_date + timedelta(weeks=37),
        'due_date': due_date,
        'overdue_threshold': due_date + timedelta(weeks=2),
    }


def get_pregnancy_milestones(current_week: Optional[int]) -> Dict[str, bool]:
    """
    Возвращает информацию о достигнутых вехах беременности.
    
    Args:
        current_week (int): Текущая неделя беременности
        
    Returns:
        dict: Словарь с информацией о вехах
    """
    if not current_week:
        return {}
    
    return {
        'implantation_complete': current_week >= 2,
        'heart_beating': current_week >= 6,
        'first_trimester_complete': current_week >= 12,
        'anatomy_scan_time': 18 <= current_week <= 22,
        'viability_threshold': current_week >= 24,
        'second_trimester_complete': current_week >= 28,
        'third_trimester_started': current_week >= 29,
        'full_term': current_week >= 37,
        'overdue': current_week >= 42,
    }


def calculate_estimated_conception_date(due_date: date) -> date:
    """
    Рассчитывает предполагаемую дату зачатия на основе ПДР.
    
    Args:
        due_date (date): Предполагаемая дата родов
        
    Returns:
        date: Предполагаемая дата зачатия
    """
    # Зачатие обычно происходит на 14 день цикла (266 дней до родов)
    return due_date - timedelta(days=266)


def calculate_due_date_from_lmp(last_menstrual_period: date) -> date:
    """
    Рассчитывает ПДР на основе даты последней менструации (правило Негеле).
    
    Args:
        last_menstrual_period (date): Дата последней менструации
        
    Returns:
        date: Предполагаемая дата родов
    """
    # Правило Негеле: ПДР = ПМ + 280 дней
    return last_menstrual_period + timedelta(days=280)


def calculate_due_date_from_conception(conception_date: date) -> date:
    """
    Рассчитывает ПДР на основе даты зачатия.
    
    Args:
        conception_date (date): Дата зачатия
        
    Returns:
        date: Предполагаемая дата родов
    """
    # От зачатия до родов обычно 266 дней
    return conception_date + timedelta(days=266)


def get_pregnancy_week_range(week: int) -> Tuple[date, date]:
    """
    Возвращает диапазон дат для указанной недели беременности.
    
    Args:
        week (int): Номер недели беременности
        start_date (date): Дата начала беременности
        
    Returns:
        tuple: Кортеж (начало_недели, конец_недели)
    """
    if week < 1:
        raise ValueError("Неделя беременности должна быть больше 0")
    
    # Неделя начинается с (week-1)*7 дня и длится 7 дней
    days_from_start = (week - 1) * 7
    week_start = days_from_start
    week_end = days_from_start + 6
    
    return (week_start, week_end)


def is_high_risk_week(current_week: Optional[int]) -> bool:
    """
    Определяет, является ли текущая неделя беременности высокого риска.
    
    Args:
        current_week (int): Текущая неделя беременности
        
    Returns:
        bool: True если неделя высокого риска
    """
    if not current_week:
        return False
    
    # Первый триместр (высокий риск выкидыша)
    # Недоношенность (32-36 недель)
    # Переношенность (42+ недель)
    return (current_week < 12 or 
            (32 <= current_week < 37) or 
            current_week >= 42)


def get_recommended_checkup_schedule(current_week: Optional[int]) -> Dict[str, str]:
    """
    Возвращает рекомендуемый график осмотров для текущей недели.
    
    Args:
        current_week (int): Текущая неделя беременности
        
    Returns:
        dict: Информация о рекомендуемых осмотрах
    """
    if not current_week:
        return {}
    
    if current_week <= 28:
        return {
            'frequency': 'Каждые 4 недели',
            'next_visit': 'Через 4 недели',
            'priority': 'routine'
        }
    elif current_week <= 36:
        return {
            'frequency': 'Каждые 2 недели',
            'next_visit': 'Через 2 недели',
            'priority': 'increased'
        }
    else:
        return {
            'frequency': 'Каждую неделю',
            'next_visit': 'Через 1 неделю',
            'priority': 'high'
        }


def detect_new_pregnancy_week(pregnancy_info, last_checked_week: Optional[int] = None) -> Optional[int]:
    """
    Определяет, наступила ли новая неделя беременности.
    
    Args:
        pregnancy_info: Объект PregnancyInfo
        last_checked_week (int, optional): Последняя проверенная неделя
        
    Returns:
        int: Номер новой недели или None если новой недели нет
    """
    if not pregnancy_info.is_active:
        return None
    
    current_week = pregnancy_info.current_week
    
    if not current_week or current_week <= 0:
        return None
    
    # Если это первая проверка или текущая неделя больше последней проверенной
    if last_checked_week is None or current_week > last_checked_week:
        return current_week
    
    return None


def get_week_milestone_message(week_number: int) -> Dict[str, str]:
    """
    Возвращает специальное сообщение для важных недель беременности.
    
    Args:
        week_number (int): Номер недели беременности
        
    Returns:
        dict: Словарь с заголовком и сообщением для важных недель
    """
    milestones = {
        4: {
            'title': '🎉 4 недели - Имплантация завершена!',
            'message': 'Эмбрион успешно прикрепился к стенке матки. Начинается активное развитие!'
        },
        6: {
            'title': '💓 6 недель - Сердце начало биться!',
            'message': 'У вашего малыша начало биться сердечко! Это важная веха в развитии.'
        },
        8: {
            'title': '👶 8 недель - Эмбрион стал плодом!',
            'message': 'Поздравляем! Теперь ваш малыш официально называется плодом, а не эмбрионом.'
        },
        12: {
            'title': '🌟 12 недель - Конец первого триместра!',
            'message': 'Вы прошли самый критический период! Риск выкидыша значительно снижается.'
        },
        16: {
            'title': '🤱 16 недель - Второй триместр в разгаре!',
            'message': 'Многие мамы чувствуют себя лучше во втором триместре. Наслаждайтесь этим временем!'
        },
        20: {
            'title': '🔍 20 недель - Время УЗИ!',
            'message': 'Половина пути пройдена! Самое время для детального УЗИ и определения пола малыша.'
        },
        24: {
            'title': '🏥 24 недели - Порог жизнеспособности!',
            'message': 'Важная веха: при преждевременных родах у малыша есть шансы на выживание с медицинской помощью.'
        },
        28: {
            'title': '🎊 28 недель - Третий триместр!',
            'message': 'Добро пожаловать в третий триместр! Малыш активно растет и набирает вес.'
        },
        32: {
            'title': '🧠 32 недели - Развитие мозга!',
            'message': 'Мозг малыша активно развивается. Легкие тоже почти готовы к самостоятельному дыханию.'
        },
        36: {
            'title': '📅 36 недель - Почти готовы!',
            'message': 'Малыш считается почти доношенным. Начинайте готовиться к родам!'
        },
        37: {
            'title': '✅ 37 недель - Доношенная беременность!',
            'message': 'Поздравляем! Ваша беременность считается доношенной. Малыш готов к рождению!'
        },
        40: {
            'title': '🎯 40 недель - ПДР наступила!',
            'message': 'Предполагаемая дата родов наступила! Скоро вы встретитесь со своим малышом!'
        }
    }
    
    return milestones.get(week_number, {})


def should_send_week_notification(pregnancy_info, week_number: int) -> bool:
    """
    Определяет, следует ли отправлять уведомление о данной неделе.
    
    Args:
        pregnancy_info: Объект PregnancyInfo
        week_number (int): Номер недели беременности
        
    Returns:
        bool: True если уведомление должно быть отправлено
    """
    # Не отправляем уведомления для неактивных беременностей
    if not pregnancy_info.is_active:
        return False
    
    # Не отправляем уведомления для недель меньше 1 или больше 42
    if week_number < 1 or week_number > 42:
        return False
    
    # Проверяем, не было ли уже отправлено уведомление для этой недели
    from webapp.models import PregnancyWeekNotification
    
    existing_notification = PregnancyWeekNotification.objects.filter(
        user=pregnancy_info.user,
        pregnancy_info=pregnancy_info,
        week_number=week_number
    ).exists()
    
    return not existing_notification


def create_week_notification_content(week_number: int) -> Dict[str, str]:
    """
    Создает контент для уведомления о неделе беременности.
    
    Args:
        week_number (int): Номер недели беременности
        
    Returns:
        dict: Словарь с заголовком и сообщением
    """
    # Проверяем, есть ли специальное сообщение для этой недели
    milestone = get_week_milestone_message(week_number)
    
    if milestone:
        return milestone
    
    # Создаем стандартное сообщение
    week_description = get_week_description(week_number)
    trimester = determine_trimester(week_number)
    
    title = f"🤱 {week_number} неделя беременности"
    
    # Добавляем эмодзи в зависимости от триместра
    if trimester == 1:
        title = f"🌱 {week_number} неделя беременности"
    elif trimester == 2:
        title = f"🌸 {week_number} неделя беременности"
    elif trimester == 3:
        title = f"🌺 {week_number} неделя беременности"
    
    message = f"""Поздравляем! Вы достигли {week_number} недели беременности.

{week_description}

Общие рекомендации:
• Регулярно посещайте врача
• Принимайте назначенные витамины
• Следите за своим самочувствием
• Достаточно отдыхайте
• Питайтесь правильно и разнообразно

Желаем вам здоровья и легкой беременности! 💕"""
    
    return {
        'title': title,
        'message': message
    }