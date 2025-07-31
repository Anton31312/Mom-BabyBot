"""
Тесты для утилит уведомлений о беременности.

Тестирует функциональность создания, отправки и управления
уведомлениями о новых неделях беременности.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch, MagicMock

from webapp.models import PregnancyInfo, PregnancyWeekNotification
from webapp.utils.notification_utils import (
    detect_new_pregnancy_weeks_for_user,
    check_and_create_pregnancy_week_notifications,
    schedule_daily_pregnancy_check,
    check_pregnancy_week_transitions,
    send_pregnancy_week_notifications,
    get_user_pregnancy_notifications,
    mark_notification_as_read,
    get_notification_statistics,
    cleanup_old_notifications,
    process_pregnancy_notifications
)


class NotificationUtilsTestCase(TestCase):
    """Базовый класс для тестов утилит уведомлений."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем информацию о беременности
        self.due_date = date.today() + timedelta(days=140)  # ~20 недель беременности
        self.pregnancy_info = PregnancyInfo.objects.create(
            user=self.user,
            due_date=self.due_date,
            is_active=True
        )
    
    def tearDown(self):
        """Очистка после тестов."""
        PregnancyWeekNotification.objects.all().delete()
        PregnancyInfo.objects.all().delete()
        User.objects.all().delete()


class DetectNewPregnancyWeeksTest(NotificationUtilsTestCase):
    """Тесты для определения новых недель беременности."""
    
    def test_detect_new_week_for_first_time(self):
        """Тест определения новой недели для пользователя без предыдущих уведомлений."""
        # Проверяем, что функция определяет текущую неделю как новую
        new_weeks = detect_new_pregnancy_weeks_for_user(self.user)
        
        self.assertEqual(len(new_weeks), 1)
        self.assertGreater(new_weeks[0], 0)
        self.assertLessEqual(new_weeks[0], 42)
    
    def test_detect_new_week_with_existing_notification(self):
        """Тест определения новой недели при наличии предыдущих уведомлений."""
        current_week = self.pregnancy_info.current_week
        
        # Создаем уведомление для текущей недели
        PregnancyWeekNotification.objects.create(
            user=self.user,
            pregnancy_info=self.pregnancy_info,
            week_number=current_week,
            title=f"Неделя {current_week}",
            message="Тестовое уведомление"
        )
        
        # Проверяем, что новых недель не обнаружено
        new_weeks = detect_new_pregnancy_weeks_for_user(self.user)
        self.assertEqual(len(new_weeks), 0)
    
    def test_detect_new_week_with_week_progression(self):
        """Тест определения новой недели при прогрессии беременности."""
        current_week = self.pregnancy_info.current_week
        
        # Создаем уведомление для предыдущей недели
        if current_week > 1:
            PregnancyWeekNotification.objects.create(
                user=self.user,
                pregnancy_info=self.pregnancy_info,
                week_number=current_week - 1,
                title=f"Неделя {current_week - 1}",
                message="Тестовое уведомление"
            )
            
            # Проверяем, что обнаружена новая неделя
            new_weeks = detect_new_pregnancy_weeks_for_user(self.user)
            self.assertEqual(len(new_weeks), 1)
            self.assertEqual(new_weeks[0], current_week)
    
    def test_detect_new_week_inactive_pregnancy(self):
        """Тест определения новой недели для неактивной беременности."""
        # Деактивируем беременность
        self.pregnancy_info.is_active = False
        self.pregnancy_info.save()
        
        # Проверяем, что новых недель не обнаружено
        new_weeks = detect_new_pregnancy_weeks_for_user(self.user)
        self.assertEqual(len(new_weeks), 0)


class CheckAndCreateNotificationsTest(NotificationUtilsTestCase):
    """Тесты для проверки и создания уведомлений."""
    
    def test_create_notification_for_new_week(self):
        """Тест создания уведомления для новой недели."""
        # Проверяем, что уведомлений нет
        self.assertEqual(PregnancyWeekNotification.objects.count(), 0)
        
        # Создаем уведомления
        notifications = check_and_create_pregnancy_week_notifications(self.user)
        
        # Проверяем, что уведомление создано
        self.assertEqual(len(notifications), 1)
        self.assertEqual(PregnancyWeekNotification.objects.count(), 1)
        
        notification = notifications[0]
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.pregnancy_info, self.pregnancy_info)
        self.assertEqual(notification.week_number, self.pregnancy_info.current_week)
        self.assertEqual(notification.status, 'pending')
    
    def test_no_duplicate_notifications(self):
        """Тест предотвращения создания дублирующих уведомлений."""
        # Создаем первое уведомление
        notifications1 = check_and_create_pregnancy_week_notifications(self.user)
        self.assertEqual(len(notifications1), 1)
        
        # Пытаемся создать уведомления снова
        notifications2 = check_and_create_pregnancy_week_notifications(self.user)
        self.assertEqual(len(notifications2), 0)
        
        # Проверяем, что в базе только одно уведомление
        self.assertEqual(PregnancyWeekNotification.objects.count(), 1)
    
    def test_create_notifications_for_all_users(self):
        """Тест создания уведомлений для всех пользователей."""
        # Создаем второго пользователя с беременностью
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        pregnancy_info2 = PregnancyInfo.objects.create(
            user=user2,
            due_date=date.today() + timedelta(days=100),  # ~26 недель
            is_active=True
        )
        
        # Создаем уведомления для всех пользователей
        notifications = check_and_create_pregnancy_week_notifications()
        
        # Проверяем, что созданы уведомления для обоих пользователей
        self.assertEqual(len(notifications), 2)
        self.assertEqual(PregnancyWeekNotification.objects.count(), 2)
        
        # Проверяем, что уведомления созданы для правильных пользователей
        user_ids = [n.user.id for n in notifications]
        self.assertIn(self.user.id, user_ids)
        self.assertIn(user2.id, user_ids)


class ScheduleDailyPregnancyCheckTest(NotificationUtilsTestCase):
    """Тесты для ежедневной проверки беременностей."""
    
    def test_daily_check_success(self):
        """Тест успешной ежедневной проверки."""
        result = schedule_daily_pregnancy_check()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['active_pregnancies_checked'], 1)
        self.assertEqual(result['new_notifications_created'], 1)
        self.assertIn('timestamp', result)
        self.assertIn('weeks_notified', result)
    
    def test_daily_check_multiple_pregnancies(self):
        """Тест ежедневной проверки с несколькими беременностями."""
        # Создаем дополнительных пользователей
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            PregnancyInfo.objects.create(
                user=user,
                due_date=date.today() + timedelta(days=140 + i * 10),
                is_active=True
            )
        
        result = schedule_daily_pregnancy_check()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['active_pregnancies_checked'], 4)  # 1 + 3 новых
        self.assertEqual(result['new_notifications_created'], 4)


class CheckPregnancyWeekTransitionsTest(NotificationUtilsTestCase):
    """Тесты для проверки переходов между неделями."""
    
    def test_detect_week_transition(self):
        """Тест определения перехода на новую неделю."""
        current_week = self.pregnancy_info.current_week
        
        # Создаем уведомление для предыдущей недели
        if current_week > 1:
            PregnancyWeekNotification.objects.create(
                user=self.user,
                pregnancy_info=self.pregnancy_info,
                week_number=current_week - 1,
                title=f"Неделя {current_week - 1}",
                message="Предыдущая неделя"
            )
            
            result = check_pregnancy_week_transitions()
            
            self.assertEqual(result['users_checked'], 1)
            self.assertEqual(result['transitions_detected'], 1)
            self.assertEqual(result['notifications_created'], 1)
            self.assertEqual(len(result['details']), 1)
            self.assertEqual(result['details'][0]['week'], current_week)
    
    def test_no_transitions_detected(self):
        """Тест отсутствия переходов между неделями."""
        current_week = self.pregnancy_info.current_week
        
        # Создаем уведомление для текущей недели
        PregnancyWeekNotification.objects.create(
            user=self.user,
            pregnancy_info=self.pregnancy_info,
            week_number=current_week,
            title=f"Неделя {current_week}",
            message="Текущая неделя"
        )
        
        result = check_pregnancy_week_transitions()
        
        self.assertEqual(result['users_checked'], 1)
        self.assertEqual(result['transitions_detected'], 0)
        self.assertEqual(result['notifications_created'], 0)
        self.assertEqual(len(result['details']), 0)


class SendPregnancyWeekNotificationsTest(NotificationUtilsTestCase):
    """Тесты для отправки уведомлений о неделях беременности."""
    
    def test_send_pending_notifications(self):
        """Тест отправки ожидающих уведомлений."""
        # Создаем уведомление в статусе pending
        notification = PregnancyWeekNotification.objects.create(
            user=self.user,
            pregnancy_info=self.pregnancy_info,
            week_number=self.pregnancy_info.current_week,
            title="Тестовое уведомление",
            message="Сообщение",
            status='pending'
        )
        
        # Отправляем уведомления
        sent_count = send_pregnancy_week_notifications()
        
        self.assertEqual(sent_count, 1)
        
        # Проверяем, что статус изменился
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'sent')
        self.assertIsNotNone(notification.sent_at)
    
    def test_send_specific_notifications(self):
        """Тест отправки конкретных уведомлений."""
        # Создаем несколько уведомлений
        notifications = []
        for i in range(3):
            notification = PregnancyWeekNotification.objects.create(
                user=self.user,
                pregnancy_info=self.pregnancy_info,
                week_number=self.pregnancy_info.current_week + i,
                title=f"Уведомление {i}",
                message=f"Сообщение {i}",
                status='pending'
            )
            notifications.append(notification)
        
        # Отправляем только первые два уведомления
        sent_count = send_pregnancy_week_notifications(notifications[:2])
        
        self.assertEqual(sent_count, 2)
        
        # Проверяем статусы
        notifications[0].refresh_from_db()
        notifications[1].refresh_from_db()
        notifications[2].refresh_from_db()
        
        self.assertEqual(notifications[0].status, 'sent')
        self.assertEqual(notifications[1].status, 'sent')
        self.assertEqual(notifications[2].status, 'pending')


class GetUserPregnancyNotificationsTest(NotificationUtilsTestCase):
    """Тесты для получения уведомлений пользователя."""
    
    def test_get_user_notifications(self):
        """Тест получения уведомлений пользователя."""
        # Создаем несколько уведомлений
        for i in range(5):
            PregnancyWeekNotification.objects.create(
                user=self.user,
                pregnancy_info=self.pregnancy_info,
                week_number=i + 1,
                title=f"Неделя {i + 1}",
                message=f"Сообщение {i + 1}"
            )
        
        # Получаем уведомления
        notifications = get_user_pregnancy_notifications(self.user, limit=3)
        
        self.assertEqual(len(notifications), 3)
        # Проверяем, что уведомления отсортированы по дате создания (новые первые)
        self.assertGreaterEqual(notifications[0].created_at, notifications[1].created_at)
        self.assertGreaterEqual(notifications[1].created_at, notifications[2].created_at)
    
    def test_get_notifications_empty_result(self):
        """Тест получения уведомлений при их отсутствии."""
        notifications = get_user_pregnancy_notifications(self.user)
        self.assertEqual(len(notifications), 0)


class MarkNotificationAsReadTest(NotificationUtilsTestCase):
    """Тесты для отметки уведомлений как прочитанных."""
    
    def test_mark_notification_as_read(self):
        """Тест отметки уведомления как прочитанного."""
        # Создаем уведомление
        notification = PregnancyWeekNotification.objects.create(
            user=self.user,
            pregnancy_info=self.pregnancy_info,
            week_number=self.pregnancy_info.current_week,
            title="Тестовое уведомление",
            message="Сообщение",
            status='sent'
        )
        
        # Отмечаем как прочитанное
        result = mark_notification_as_read(notification.id, self.user)
        
        self.assertTrue(result)
        
        # Проверяем изменения
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'read')
        self.assertIsNotNone(notification.read_at)
    
    def test_mark_nonexistent_notification(self):
        """Тест отметки несуществующего уведомления."""
        result = mark_notification_as_read(999, self.user)
        self.assertFalse(result)
    
    def test_mark_notification_wrong_user(self):
        """Тест отметки уведомления другого пользователя."""
        # Создаем другого пользователя
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Создаем уведомление для первого пользователя
        notification = PregnancyWeekNotification.objects.create(
            user=self.user,
            pregnancy_info=self.pregnancy_info,
            week_number=self.pregnancy_info.current_week,
            title="Тестовое уведомление",
            message="Сообщение"
        )
        
        # Пытаемся отметить как прочитанное от имени другого пользователя
        result = mark_notification_as_read(notification.id, other_user)
        self.assertFalse(result)


class NotificationStatisticsTest(NotificationUtilsTestCase):
    """Тесты для статистики уведомлений."""
    
    def test_get_notification_statistics(self):
        """Тест получения статистики уведомлений."""
        # Создаем уведомления с разными статусами
        statuses = ['pending', 'sent', 'read', 'failed']
        for i, status in enumerate(statuses):
            PregnancyWeekNotification.objects.create(
                user=self.user,
                pregnancy_info=self.pregnancy_info,
                week_number=i + 1,
                title=f"Уведомление {i + 1}",
                message=f"Сообщение {i + 1}",
                status=status
            )
        
        # Получаем статистику
        stats = get_notification_statistics(self.user)
        
        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['pending'], 1)
        self.assertEqual(stats['sent'], 1)
        self.assertEqual(stats['read'], 1)
        self.assertEqual(stats['failed'], 1)
        self.assertEqual(stats['delivery_rate'], 50.0)  # (sent + read) / total * 100
        self.assertEqual(stats['read_rate'], 50.0)  # read / (sent + read) * 100
    
    def test_get_statistics_empty(self):
        """Тест получения статистики при отсутствии уведомлений."""
        stats = get_notification_statistics(self.user)
        
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['pending'], 0)
        self.assertEqual(stats['sent'], 0)
        self.assertEqual(stats['read'], 0)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['delivery_rate'], 0)
        self.assertEqual(stats['read_rate'], 0)


class CleanupOldNotificationsTest(NotificationUtilsTestCase):
    """Тесты для очистки старых уведомлений."""
    
    def test_cleanup_old_notifications(self):
        """Тест очистки старых прочитанных уведомлений."""
        # Создаем старое прочитанное уведомление
        old_notification = PregnancyWeekNotification.objects.create(
            user=self.user,
            pregnancy_info=self.pregnancy_info,
            week_number=1,
            title="Старое уведомление",
            message="Старое сообщение",
            status='read'
        )
        
        # Устанавливаем старую дату прочтения
        old_date = timezone.now() - timedelta(days=100)
        old_notification.read_at = old_date
        old_notification.save()
        
        # Создаем новое прочитанное уведомление
        new_notification = PregnancyWeekNotification.objects.create(
            user=self.user,
            pregnancy_info=self.pregnancy_info,
            week_number=2,
            title="Новое уведомление",
            message="Новое сообщение",
            status='read',
            read_at=timezone.now()
        )
        
        # Очищаем старые уведомления (старше 90 дней)
        cleaned_count = cleanup_old_notifications(days_old=90)
        
        self.assertEqual(cleaned_count, 1)
        
        # Проверяем, что старое уведомление удалено, а новое осталось
        self.assertFalse(PregnancyWeekNotification.objects.filter(id=old_notification.id).exists())
        self.assertTrue(PregnancyWeekNotification.objects.filter(id=new_notification.id).exists())


class ProcessPregnancyNotificationsTest(NotificationUtilsTestCase):
    """Тесты для основной функции обработки уведомлений."""
    
    def test_process_pregnancy_notifications(self):
        """Тест полного процесса обработки уведомлений."""
        result = process_pregnancy_notifications()
        
        self.assertIn('new_notifications_created', result)
        self.assertIn('notifications_sent', result)
        self.assertIn('old_notifications_cleaned', result)
        self.assertIn('timestamp', result)
        
        # Проверяем, что создано уведомление
        self.assertGreater(result['new_notifications_created'], 0)
        
        # Проверяем, что уведомление есть в базе
        self.assertEqual(PregnancyWeekNotification.objects.count(), 1)