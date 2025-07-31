"""
Management command для обработки уведомлений о неделях беременности.

Эта команда должна запускаться регулярно (например, через cron)
для проверки новых недель беременности и отправки уведомлений.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from webapp.utils.notification_utils import process_pregnancy_notifications
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Обрабатывает уведомления о неделях беременности'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Обработать уведомления только для указанного пользователя (username)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано, но не выполнять действия'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Подробный вывод'
        )
    
    def handle(self, *args, **options):
        if options['verbose']:
            logging.basicConfig(level=logging.INFO)
        
        self.stdout.write(
            self.style.SUCCESS('Начинаем обработку уведомлений о беременности...')
        )
        
        try:
            if options['user']:
                # Обрабатываем уведомления для конкретного пользователя
                try:
                    user = User.objects.get(username=options['user'])
                    self.stdout.write(f"Обрабатываем уведомления для пользователя: {user.username}")
                    
                    if options['dry_run']:
                        self.stdout.write(
                            self.style.WARNING('Режим dry-run: изменения не будут сохранены')
                        )
                        # В режиме dry-run можно показать что будет сделано
                        from webapp.models import PregnancyInfo
                        from webapp.utils.pregnancy_utils import should_send_week_notification
                        from webapp.utils.notification_utils import detect_new_pregnancy_weeks_for_user
                        
                        pregnancies = PregnancyInfo.objects.filter(user=user, is_active=True)
                        new_weeks = detect_new_pregnancy_weeks_for_user(user)
                        
                        if new_weeks:
                            for week in new_weeks:
                                self.stdout.write(
                                    f"  Будет создано уведомление о {week} неделе"
                                )
                        else:
                            self.stdout.write("  Новых недель не обнаружено")
                    else:
                        from webapp.utils.notification_utils import check_and_create_pregnancy_week_notifications
                        notifications = check_and_create_pregnancy_week_notifications(user)
                        self.stdout.write(
                            f"Создано {len(notifications)} новых уведомлений"
                        )
                        
                        # Показываем детали созданных уведомлений
                        for notification in notifications:
                            self.stdout.write(
                                f"  - Неделя {notification.week_number}: {notification.title}"
                            )
                        
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Пользователь "{options["user"]}" не найден')
                    )
                    return
            else:
                # Обрабатываем уведомления для всех пользователей
                if options['dry_run']:
                    self.stdout.write(
                        self.style.WARNING('Режим dry-run: изменения не будут сохранены')
                    )
                    # Показываем статистику
                    from webapp.utils.notification_utils import schedule_daily_pregnancy_check
                    
                    # Используем функцию ежедневной проверки для получения статистики
                    # В режиме dry-run мы не создаем уведомления, но показываем что будет сделано
                    from webapp.models import PregnancyInfo
                    from webapp.utils.notification_utils import detect_new_pregnancy_weeks_for_user
                    
                    active_pregnancies = PregnancyInfo.objects.filter(is_active=True).select_related('user')
                    total_new_notifications = 0
                    users_with_new_weeks = 0
                    
                    for pregnancy in active_pregnancies:
                        new_weeks = detect_new_pregnancy_weeks_for_user(pregnancy.user)
                        if new_weeks:
                            users_with_new_weeks += 1
                            total_new_notifications += len(new_weeks)
                            self.stdout.write(
                                f"  {pregnancy.user.username}: недели {', '.join(map(str, new_weeks))}"
                            )
                    
                    self.stdout.write(
                        f"Активных беременностей: {active_pregnancies.count()}"
                    )
                    self.stdout.write(
                        f"Пользователей с новыми неделями: {users_with_new_weeks}"
                    )
                    self.stdout.write(
                        f"Будет создано {total_new_notifications} новых уведомлений"
                    )
                else:
                    # Используем улучшенную функцию обработки
                    from webapp.utils.notification_utils import schedule_daily_pregnancy_check
                    result = schedule_daily_pregnancy_check()
                    
                    if result['status'] == 'success':
                        self.stdout.write(
                            f"Проверено активных беременностей: {result['active_pregnancies_checked']}"
                        )
                        self.stdout.write(
                            f"Создано новых уведомлений: {result['new_notifications_created']}"
                        )
                        
                        # Показываем статистику по неделям
                        if result['weeks_notified']:
                            self.stdout.write("Уведомления созданы для недель:")
                            for week, count in result['weeks_notified'].items():
                                self.stdout.write(f"  - Неделя {week}: {count} пользователей")
                        
                        # Отправляем созданные уведомления
                        from webapp.utils.notification_utils import send_pregnancy_week_notifications
                        sent_count = send_pregnancy_week_notifications()
                        self.stdout.write(f"Отправлено уведомлений: {sent_count}")
                        
                        # Очищаем старые уведомления
                        from webapp.utils.notification_utils import cleanup_old_notifications
                        cleaned_count = cleanup_old_notifications()
                        self.stdout.write(f"Очищено старых уведомлений: {cleaned_count}")
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"Ошибка при ежедневной проверке: {result.get('error_message', 'Неизвестная ошибка')}")
                        )
            
            self.stdout.write(
                self.style.SUCCESS('Обработка уведомлений завершена успешно!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при обработке уведомлений: {e}')
            )
            logger.error(f"Ошибка в команде process_pregnancy_notifications: {e}")
            raise