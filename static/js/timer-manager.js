/**
 * Timer Manager для приложения Mom&BabyBot
 * Управляет таймерами и их синхронизацией с Service Worker
 */

class TimerManager {
  constructor() {
    this.activeTimers = new Map();
    this.serviceWorkerRegistration = null;
    this.isInitialized = false;
    this.notificationPermission = 'default';
  }
  
  /**
   * Инициализация менеджера таймеров
   */
  async init() {
    if (this.isInitialized) return;
    
    // Регистрация Service Worker
    if ('serviceWorker' in navigator) {
      try {
        this.serviceWorkerRegistration = await navigator.serviceWorker.register('/static/js/service-worker.js');
        console.log('Service Worker зарегистрирован:', this.serviceWorkerRegistration);
        
        // Обработка сообщений от Service Worker
        navigator.serviceWorker.addEventListener('message', this.handleServiceWorkerMessage.bind(this));
        
        // Запрос разрешения на отправку уведомлений
        this.requestNotificationPermission();
        
        // Проверка наличия активных таймеров
        this.checkActiveTimers();
        
        this.isInitialized = true;
      } catch (error) {
        console.error('Ошибка при регистрации Service Worker:', error);
      }
    } else {
      console.warn('Service Worker не поддерживается в этом браузере');
    }
  }
  
  /**
   * Запрос разрешения на отправку уведомлений
   */
  async requestNotificationPermission() {
    if (!('Notification' in window)) {
      console.warn('Уведомления не поддерживаются в этом браузере');
      return;
    }
    
    try {
      const permission = await Notification.requestPermission();
      this.notificationPermission = permission;
      console.log('Разрешение на уведомления:', permission);
    } catch (error) {
      console.error('Ошибка при запросе разрешения на уведомления:', error);
    }
  }
  
  /**
   * Обработка сообщений от Service Worker
   */
  handleServiceWorkerMessage(event) {
    const data = event.data;
    
    switch (data.action) {
      case 'timerStarted':
        this.handleTimerStarted(data.timerId, data.startTime, data.timerType);
        break;
      case 'timerStopped':
        this.handleTimerStopped(data.timerId);
        break;
      case 'activeTimers':
        this.handleActiveTimers(data.timers);
        break;
    }
  }
  
  /**
   * Обработка запуска таймера
   */
  handleTimerStarted(timerId, startTime, timerType) {
    this.activeTimers.set(timerId, {
      startTime: startTime,
      type: timerType
    });
    
    // Вызываем событие для обновления UI
    this.dispatchTimerEvent('timerStarted', {
      timerId: timerId,
      startTime: startTime,
      timerType: timerType
    });
  }
  
  /**
   * Обработка остановки таймера
   */
  handleTimerStopped(timerId) {
    this.activeTimers.delete(timerId);
    
    // Вызываем событие для обновления UI
    this.dispatchTimerEvent('timerStopped', {
      timerId: timerId
    });
  }
  
  /**
   * Обработка списка активных таймеров
   */
  handleActiveTimers(timers) {
    // Очищаем текущий список
    this.activeTimers.clear();
    
    // Добавляем полученные таймеры
    timers.forEach(timer => {
      this.activeTimers.set(timer.timerId, {
        startTime: timer.startTime,
        type: timer.type
      });
    });
    
    // Вызываем событие для обновления UI
    this.dispatchTimerEvent('activeTimersUpdated', {
      timers: Array.from(this.activeTimers.entries()).map(([id, data]) => {
        return {
          timerId: id,
          startTime: data.startTime,
          type: data.type
        };
      })
    });
  }
  
  /**
   * Запуск таймера
   */
  startTimer(timerId, timerType, metadata = {}) {
    const startTime = Date.now();
    
    // Сохраняем информацию о таймере в localStorage
    this.saveTimerToLocalStorage(timerId, startTime, timerType, metadata);
    
    // Отправляем сообщение Service Worker
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        action: 'startTimer',
        timerId: timerId,
        startTime: startTime,
        timerType: timerType,
        metadata: metadata
      });
    }
    
    // Добавляем таймер в список активных
    this.activeTimers.set(timerId, {
      startTime: startTime,
      type: timerType,
      metadata: metadata
    });
    
    return {
      timerId: timerId,
      startTime: startTime
    };
  }
  
  /**
   * Остановка таймера
   */
  stopTimer(timerId) {
    // Удаляем информацию о таймере из localStorage
    this.removeTimerFromLocalStorage(timerId);
    
    // Отправляем сообщение Service Worker
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        action: 'stopTimer',
        timerId: timerId
      });
    }
    
    // Удаляем таймер из списка активных
    this.activeTimers.delete(timerId);
  }
  
  /**
   * Проверка наличия активных таймеров
   */
  checkActiveTimers() {
    // Загружаем таймеры из localStorage
    this.loadTimersFromLocalStorage();
    
    // Отправляем запрос Service Worker
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        action: 'checkTimers'
      });
    }
  }
  
  /**
   * Сохранение информации о таймере в localStorage
   */
  saveTimerToLocalStorage(timerId, startTime, timerType, metadata) {
    try {
      const timers = this.getTimersFromLocalStorage();
      timers[timerId] = {
        startTime: startTime,
        type: timerType,
        metadata: metadata
      };
      localStorage.setItem('activeTimers', JSON.stringify(timers));
    } catch (error) {
      console.error('Ошибка при сохранении таймера в localStorage:', error);
    }
  }
  
  /**
   * Удаление информации о таймере из localStorage
   */
  removeTimerFromLocalStorage(timerId) {
    try {
      const timers = this.getTimersFromLocalStorage();
      delete timers[timerId];
      localStorage.setItem('activeTimers', JSON.stringify(timers));
    } catch (error) {
      console.error('Ошибка при удалении таймера из localStorage:', error);
    }
  }
  
  /**
   * Загрузка таймеров из localStorage
   */
  loadTimersFromLocalStorage() {
    const timers = this.getTimersFromLocalStorage();
    
    // Очищаем текущий список
    this.activeTimers.clear();
    
    // Добавляем загруженные таймеры
    Object.entries(timers).forEach(([timerId, data]) => {
      this.activeTimers.set(timerId, {
        startTime: data.startTime,
        type: data.type,
        metadata: data.metadata
      });
    });
    
    // Вызываем событие для обновления UI
    this.dispatchTimerEvent('activeTimersUpdated', {
      timers: Array.from(this.activeTimers.entries()).map(([id, data]) => {
        return {
          timerId: id,
          startTime: data.startTime,
          type: data.type,
          metadata: data.metadata
        };
      })
    });
  }
  
  /**
   * Получение таймеров из localStorage
   */
  getTimersFromLocalStorage() {
    try {
      const timersJson = localStorage.getItem('activeTimers');
      return timersJson ? JSON.parse(timersJson) : {};
    } catch (error) {
      console.error('Ошибка при получении таймеров из localStorage:', error);
      return {};
    }
  }
  
  /**
   * Отправка события таймера
   */
  dispatchTimerEvent(eventName, data) {
    const event = new CustomEvent(`timerManager:${eventName}`, {
      detail: data
    });
    document.dispatchEvent(event);
  }
  
  /**
   * Получение активного таймера по ID
   */
  getActiveTimer(timerId) {
    return this.activeTimers.get(timerId);
  }
  
  /**
   * Получение всех активных таймеров
   */
  getAllActiveTimers() {
    return Array.from(this.activeTimers.entries()).map(([id, data]) => {
      return {
        timerId: id,
        startTime: data.startTime,
        type: data.type,
        metadata: data.metadata
      };
    });
  }
  
  /**
   * Проверка наличия активных таймеров определенного типа
   */
  hasActiveTimersOfType(timerType) {
    for (const [_, data] of this.activeTimers.entries()) {
      if (data.type === timerType) {
        return true;
      }
    }
    return false;
  }
  
  /**
   * Форматирование времени
   */
  static formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return [
      hours.toString().padStart(2, '0'),
      minutes.toString().padStart(2, '0'),
      secs.toString().padStart(2, '0')
    ].join(':');
  }
  
  /**
   * Расчет прошедшего времени в секундах
   */
  static getElapsedSeconds(startTime) {
    return Math.floor((Date.now() - startTime) / 1000);
  }
}

// Создаем глобальный экземпляр TimerManager
window.timerManager = new TimerManager();

// Загрузка скрипта data-sync.js
function loadDataSyncScript() {
  return new Promise((resolve, reject) => {
    // Проверяем, загружен ли уже скрипт
    if (window.dataSync) {
      resolve();
      return;
    }
    
    const script = document.createElement('script');
    script.src = '/static/js/data-sync.js';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Не удалось загрузить скрипт data-sync.js'));
    document.head.appendChild(script);
  });
}

// Инициализируем TimerManager и загружаем DataSync при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
  window.timerManager.init();
  
  try {
    await loadDataSyncScript();
    console.log('DataSync успешно загружен');
  } catch (error) {
    console.error('Ошибка при загрузке DataSync:', error);
  }
});