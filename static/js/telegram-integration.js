/**
 * Модуль для интеграции с Telegram ботом
 * Обеспечивает отправку уведомлений через Telegram
 */

class TelegramIntegration {
  constructor() {
    this.notificationPreferences = null;
    this.userId = null;
    this.childId = null;
    this.childName = null;
  }
  
  /**
   * Инициализация модуля
   * @param {number} userId - ID пользователя
   * @param {number} childId - ID ребенка (опционально)
   * @param {string} childName - Имя ребенка (опционально)
   */
  init(userId, childId = null, childName = null) {
    this.userId = userId;
    this.childId = childId;
    this.childName = childName;
    
    // Загружаем настройки уведомлений
    this.loadNotificationPreferences();
  }
  
  /**
   * Загрузка настроек уведомлений
   */
  loadNotificationPreferences() {
    if (!this.userId) {
      console.warn('Не указан ID пользователя для загрузки настроек уведомлений');
      return;
    }
    
    // Используем dataSync для загрузки настроек
    window.dataSync.request({
      url: `/api/users/${this.userId}/notifications/preferences/`,
      method: 'GET',
      entityType: 'notification_preferences',
      useCache: true,
      onSuccess: (data) => {
        this.notificationPreferences = data;
        console.log('Настройки уведомлений загружены:', data);
      },
      onError: (error) => {
        console.error('Ошибка при загрузке настроек уведомлений:', error);
      }
    });
  }
  
  /**
   * Обновление настроек уведомлений
   * @param {Object} preferences - Новые настройки
   */
  updateNotificationPreferences(preferences) {
    if (!this.userId) {
      console.warn('Не указан ID пользователя для обновления настроек уведомлений');
      return;
    }
    
    // Используем dataSync для обновления настроек
    window.dataSync.request({
      url: `/api/users/${this.userId}/notifications/preferences/`,
      method: 'POST',
      data: preferences,
      entityType: 'notification_preferences',
      onSuccess: (data) => {
        this.notificationPreferences = data;
        console.log('Настройки уведомлений обновлены:', data);
      },
      onError: (error) => {
        console.error('Ошибка при обновлении настроек уведомлений:', error);
      }
    });
  }
  
  /**
   * Проверка, включены ли уведомления определенного типа
   * @param {string} notificationType - Тип уведомления
   * @returns {boolean} - Включены ли уведомления
   */
  isNotificationEnabled(notificationType) {
    if (!this.notificationPreferences) {
      return false;
    }
    
    // Проверяем общие настройки
    if (!this.notificationPreferences.enabled || !this.notificationPreferences.telegram_enabled) {
      return false;
    }
    
    // Проверяем настройки для конкретного типа
    switch (notificationType) {
      case 'sleep':
        return this.notificationPreferences.sleep_timer_notifications;
      case 'feeding':
        return this.notificationPreferences.feeding_timer_notifications;
      case 'contraction':
        return this.notificationPreferences.contraction_counter_notifications;
      case 'kick':
        return this.notificationPreferences.kick_counter_notifications;
      case 'vaccine':
        return this.notificationPreferences.vaccine_reminder_notifications;
      default:
        return false;
    }
  }
  
  /**
   * Отправка уведомления через Telegram
   * @param {string} notificationType - Тип уведомления
   * @param {number} entityId - ID сущности
   * @param {Object} data - Данные для уведомления
   */
  sendNotification(notificationType, entityId, data) {
    if (!this.userId) {
      console.warn('Не указан ID пользователя для отправки уведомления');
      return;
    }
    
    // Проверяем, включены ли уведомления
    if (!this.isNotificationEnabled(notificationType)) {
      console.log(`Уведомления типа ${notificationType} отключены`);
      return;
    }
    
    // Формируем данные для запроса
    const requestData = {
      notification_type: notificationType,
      entity_id: entityId,
      data: data
    };
    
    // Отправляем запрос на сервер
    fetch(`/api/users/${this.userId}/notifications/send/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Уведомление отправлено:', data);
    })
    .catch(error => {
      console.error('Ошибка при отправке уведомления:', error);
    });
  }
  
  /**
   * Отправка уведомления о завершении сессии сна
   * @param {Object} sleepSession - Данные о сессии сна
   */
  sendSleepCompletedNotification(sleepSession) {
    if (!this.isNotificationEnabled('sleep')) {
      return;
    }
    
    // Получаем имя ребенка
    const childName = this.childName || 'Ребенок';
    
    // Формируем данные для уведомления
    const data = {
      child_name: childName,
      duration_minutes: sleepSession.duration || 0,
      sleep_type: sleepSession.type || 'day',
      quality: sleepSession.quality
    };
    
    // Отправляем уведомление
    this.sendNotification('sleep', sleepSession.id, data);
  }
  
  /**
   * Отправка уведомления о завершении сессии кормления
   * @param {Object} feedingSession - Данные о сессии кормления
   */
  sendFeedingCompletedNotification(feedingSession) {
    if (!this.isNotificationEnabled('feeding')) {
      return;
    }
    
    // Получаем имя ребенка
    const childName = this.childName || 'Ребенок';
    
    // Формируем данные для уведомления
    const data = {
      child_name: childName,
      feeding_type: feedingSession.type || 'bottle',
      amount: feedingSession.amount,
      duration: feedingSession.duration,
      breast: feedingSession.breast
    };
    
    // Отправляем уведомление
    this.sendNotification('feeding', feedingSession.id, data);
  }
  
  /**
   * Отправка уведомления о завершении сессии схваток
   * @param {Object} contractionSession - Данные о сессии схваток
   */
  sendContractionCompletedNotification(contractionSession) {
    if (!this.isNotificationEnabled('contraction')) {
      return;
    }
    
    // Формируем данные для уведомления
    const data = {
      count: contractionSession.count || 0,
      avg_interval: contractionSession.average_interval || 0,
      duration: contractionSession.duration || 0
    };
    
    // Отправляем уведомление
    this.sendNotification('contraction', contractionSession.id, data);
  }
  
  /**
   * Отправка уведомления о завершении сессии шевелений
   * @param {Object} kickSession - Данные о сессии шевелений
   */
  sendKickCompletedNotification(kickSession) {
    if (!this.isNotificationEnabled('kick')) {
      return;
    }
    
    // Формируем данные для уведомления
    const data = {
      count: kickSession.count || 0,
      duration: kickSession.duration || 0
    };
    
    // Отправляем уведомление
    this.sendNotification('kick', kickSession.id, data);
  }
  
  /**
   * Отправка тестового уведомления
   */
  sendTestNotification() {
    if (!this.userId) {
      console.warn('Не указан ID пользователя для отправки тестового уведомления');
      return;
    }
    
    // Отправляем запрос на сервер
    fetch(`/api/users/${this.userId}/notifications/test/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ type: 'test' })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Тестовое уведомление отправлено:', data);
      alert('Тестовое уведомление отправлено в Telegram');
    })
    .catch(error => {
      console.error('Ошибка при отправке тестового уведомления:', error);
      alert('Ошибка при отправке тестового уведомления');
    });
  }
}

// Создаем глобальный экземпляр TelegramIntegration
window.telegramIntegration = new TelegramIntegration();

// Инициализируем TelegramIntegration при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  // Получаем ID пользователя и ребенка из скрытых полей
  const userId = document.getElementById('userId')?.value;
  const childId = document.getElementById('childId')?.value;
  const childName = document.getElementById('childName')?.value;
  
  if (userId) {
    window.telegramIntegration.init(userId, childId, childName);
  }
});