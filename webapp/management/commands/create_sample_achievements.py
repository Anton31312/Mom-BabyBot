"""
Команда для создания примеров достижений в системе.

Эта команда создает набор достижений для демонстрации функциональности
системы достижений, соответствующей требованию 9.3.
"""

from django.core.management.base import BaseCommand
from webapp.models import Achievement


class Command(BaseCommand):
    help = 'Создает примеры достижений для демонстрации системы'
    
    def handle(self, *args, **options):
        """Создает примеры достижений."""
        
        achievements_data = [
            # Достижения по беременности
            {
                'title': 'Первый триместр',
                'description': 'Поздравляем! Вы достигли 12 недели беременности',
                'achievement_type': 'pregnancy_milestone',
                'difficulty': 'easy',
                'icon': '🤱',
                'points': 15,
                'condition_type': 'pregnancy_week',
                'condition_value': 12,
            },
            {
                'title': 'Второй триместр',
                'description': 'Добро пожаловать во второй триместр! 14 недель позади',
                'achievement_type': 'pregnancy_milestone',
                'difficulty': 'medium',
                'icon': '🤰',
                'points': 20,
                'condition_type': 'pregnancy_week',
                'condition_value': 14,
            },
            {
                'title': 'Третий триместр',
                'description': 'Финальная прямая! Вы достигли 28 недели беременности',
                'achievement_type': 'pregnancy_milestone',
                'difficulty': 'hard',
                'icon': '👶',
                'points': 30,
                'condition_type': 'pregnancy_week',
                'condition_value': 28,
            },
            
            # Достижения по кормлению
            {
                'title': 'Первое кормление',
                'description': 'Вы записали свой первый сеанс кормления',
                'achievement_type': 'feeding_milestone',
                'difficulty': 'easy',
                'icon': '🍼',
                'points': 10,
                'condition_type': 'feeding_sessions',
                'condition_value': 1,
            },
            {
                'title': 'Опытная мама',
                'description': 'Вы записали уже 10 сеансов кормления',
                'achievement_type': 'feeding_milestone',
                'difficulty': 'medium',
                'icon': '🤱',
                'points': 25,
                'condition_type': 'feeding_sessions',
                'condition_value': 10,
            },
            {
                'title': 'Мастер кормления',
                'description': 'Невероятно! 50 сеансов кормления записано',
                'achievement_type': 'feeding_milestone',
                'difficulty': 'hard',
                'icon': '👑',
                'points': 50,
                'condition_type': 'feeding_sessions',
                'condition_value': 50,
            },
            
            # Достижения по здоровью
            {
                'title': 'Следим за весом',
                'description': 'Вы начали отслеживать свой вес',
                'achievement_type': 'health_milestone',
                'difficulty': 'easy',
                'icon': '⚖️',
                'points': 10,
                'condition_type': 'weight_records',
                'condition_value': 1,
            },
            {
                'title': 'Контроль веса',
                'description': 'Отлично! Вы записали уже 5 измерений веса',
                'achievement_type': 'health_milestone',
                'difficulty': 'medium',
                'icon': '📊',
                'points': 20,
                'condition_type': 'weight_records',
                'condition_value': 5,
            },
            {
                'title': 'Мониторинг давления',
                'description': 'Вы начали отслеживать артериальное давление',
                'achievement_type': 'health_milestone',
                'difficulty': 'easy',
                'icon': '🩺',
                'points': 15,
                'condition_type': 'blood_pressure_records',
                'condition_value': 1,
            },
            {
                'title': 'Здоровый контроль',
                'description': 'Превосходно! 10 измерений давления записано',
                'achievement_type': 'health_milestone',
                'difficulty': 'medium',
                'icon': '💚',
                'points': 30,
                'condition_type': 'blood_pressure_records',
                'condition_value': 10,
            },
            
            # Достижения по использованию приложения
            {
                'title': 'Новичок',
                'description': 'Добро пожаловать в приложение! Заполните свой профиль',
                'achievement_type': 'app_usage',
                'difficulty': 'easy',
                'icon': '🌟',
                'points': 5,
                'condition_type': 'data_completeness',
                'condition_value': 50,
            },
            {
                'title': 'Активный пользователь',
                'description': 'Отлично! Ваш профиль заполнен на 80%',
                'achievement_type': 'app_usage',
                'difficulty': 'medium',
                'icon': '⭐',
                'points': 15,
                'condition_type': 'data_completeness',
                'condition_value': 80,
            },
            {
                'title': 'Перфекционист',
                'description': 'Невероятно! Ваш профиль заполнен полностью',
                'achievement_type': 'app_usage',
                'difficulty': 'hard',
                'icon': '🏆',
                'points': 25,
                'condition_type': 'data_completeness',
                'condition_value': 100,
            },
            
            # Особые достижения
            {
                'title': 'Первый день',
                'description': 'Добро пожаловать! Сегодня ваш первый день в приложении',
                'achievement_type': 'special_event',
                'difficulty': 'easy',
                'icon': '🎉',
                'points': 10,
                'condition_type': 'special_date',
                'condition_value': 1,
                'condition_data': {'date': '2025-01-01'},  # Будет обновлено при создании
                'is_hidden': True,
            },
            {
                'title': 'Постоянство',
                'description': 'Вы используете приложение уже неделю подряд!',
                'achievement_type': 'app_usage',
                'difficulty': 'medium',
                'icon': '📅',
                'points': 20,
                'condition_type': 'consecutive_days',
                'condition_value': 7,
                'is_hidden': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for achievement_data in achievements_data:
            # Обновляем дату для особых достижений
            if achievement_data.get('condition_type') == 'special_date':
                from django.utils import timezone
                today = timezone.now().date()
                achievement_data['condition_data'] = {'date': today.strftime('%Y-%m-%d')}
            
            achievement, created = Achievement.objects.get_or_create(
                title=achievement_data['title'],
                defaults=achievement_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создано достижение: {achievement.title}')
                )
            else:
                # Обновляем существующее достижение
                for key, value in achievement_data.items():
                    if key != 'title':  # Не обновляем title, так как он используется для поиска
                        setattr(achievement, key, value)
                achievement.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Обновлено достижение: {achievement.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nГотово! Создано: {created_count}, обновлено: {updated_count} достижений'
            )
        )
        
        # Выводим статистику по типам достижений
        self.stdout.write('\nСтатистика по типам достижений:')
        for choice in Achievement.ACHIEVEMENT_TYPE_CHOICES:
            count = Achievement.objects.filter(achievement_type=choice[0]).count()
            self.stdout.write(f'  {choice[1]}: {count}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nВсего достижений в системе: {Achievement.objects.count()}'
            )
        )