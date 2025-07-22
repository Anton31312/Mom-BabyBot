/**
 * Модуль для синхронизации данных между локальным хранилищем и сервером
 * Обеспечивает работу приложения в офлайн-режиме и синхронизацию при восстановлении соединения
 * Интегрирован с Telegram ботом для отправки уведомлений
 */

class DataSync {
  constructor() {
    this.syncQueue = [];
    this.isSyncing = false;
    this.isOnline = navigator.onLine;
    this.syncInterval = null;
    this.SYNC_INTERVAL_MS = 30000; // 30 секунд
    this.STORAGE_KEYS = {
      SYNC_QUEUE: 'sync_queue',
      CACHED_DATA: 'cached_data',
      LAST_SYNC: 'last_sync_timestamp'
    };
    
    // Инициализация обработчиков событий
    this.initEventListeners();
  }
  
  /**
   * Инициализация обработчиков событий
   */
  initEventListeners() {
    // Обработчики онлайн/офлайн статуса
    window.addEventListener('online', this.handleOnlineStatus.bind(this));
    window.addEventListener('offline', this.handleOfflineStatus.bind(this));
    
    // Обработчик перед закрытием страницы
    window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
    
    // Инициализация периодической синхронизации
    this.startSyncInterval();
  }
  
  /**
   * Запуск периодической синхронизации
   */
  startSyncInterval() {
    // Очищаем предыдущий интервал, если он был
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    
    // Устанавливаем новый интервал
    this.syncInterval = setInterval(() => {
      if (this.isOnline) {
        this.syncQueuedData();
      }
    }, this.SYNC_INTERVAL_MS);
  }
  
  /**
   * Обработка перехода в онлайн
   */
  handleOnlineStatus() {
    console.log('Соединение восстановлено');
    this.isOnline = true;
    
    // Показываем уведомление о восстановлении соединения
    this.showNotification('Соединение восстановлено', 'Синхронизация данных...');
    
    // Запускаем синхронизацию
    this.syncQueuedData();
  }
  
  /**
   * Обработка перехода в офлайн
   */
  handleOfflineStatus() {
    console.log('Соединение потеряно');
    this.isOnline = false;
    
    // Показываем уведомление о потере соединения
    this.showNotification('Соединение потеряно', 'Данные будут сохранены локально и синхронизированы позже');
  }
  
  /**
   * Обработка события перед закрытием страницы
   */
  handleBeforeUnload() {
    // Сохраняем очередь синхронизации в localStorage
    this.saveQueueToStorage();
  }
  
  /**
   * Показ уведомления
   */
  showNotification(title, message) {
    // Проверяем поддержку уведомлений
    if (!('Notification' in window)) {
      console.warn('Уведомления не поддерживаются в этом браузере');
      return;
    }
    
    // Проверяем разрешение на уведомления
    if (Notification.permission === 'granted') {
      new Notification(title, { body: message });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          new Notification(title, { body: message });
        }
      });
    }
  }
  
  /**
   * Добавление запроса в очередь синхронизации
   * @param {Object} request - Объект запроса
   * @param {string} request.url - URL запроса
   * @param {string} request.method - Метод запроса (GET, POST, PUT, DELETE)
   * @param {Object} request.data - Данные запроса
   * @param {string} request.entityType - Тип сущности (sleep, feeding, etc.)
   * @param {string} request.entityId - ID сущности
   * @param {Function} request.onSuccess - Функция обратного вызова при успехе
   * @param {Function} request.onError - Функция обратного вызова при ошибке
   */
  addToSyncQueue(request) {
    // Добавляем временную метку
    request.timestamp = Date.now();
    
    // Добавляем запрос в очередь
    this.syncQueue.push(request);
    
    // Сохраняем очередь в localStorage
    this.saveQueueToStorage();
    
    // Если онлайн, пытаемся синхронизировать сразу
    if (this.isOnline) {
      this.syncQueuedData();
    }
  }
  
  /**
   * Сохранение очереди синхронизации в localStorage
   */
  saveQueueToStorage() {
    try {
      // Создаем копию очереди без функций обратного вызова
      const queueForStorage = this.syncQueue.map(request => {
        const { onSuccess, onError, ...requestData } = request;
        return requestData;
      });
      
      localStorage.setItem(this.STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(queueForStorage));
    } catch (error) {
      console.error('Ошибка при сохранении очереди синхронизации:', error);
    }
  }
  
  /**
   * Загрузка очереди синхронизации из localStorage
   */
  loadQueueFromStorage() {
    try {
      const queueJson = localStorage.getItem(this.STORAGE_KEYS.SYNC_QUEUE);
      if (queueJson) {
        this.syncQueue = JSON.parse(queueJson);
      }
    } catch (error) {
      console.error('Ошибка при загрузке очереди синхронизации:', error);
      this.syncQueue = [];
    }
  }
  
  /**
   * Синхронизация данных из очереди
   */
  async syncQueuedData() {
    // Если уже идет синхронизация или нет подключения, выходим
    if (this.isSyncing || !this.isOnline || this.syncQueue.length === 0) {
      return;
    }
    
    this.isSyncing = true;
    
    try {
      // Копируем очередь, чтобы не изменять ее во время итерации
      const queueCopy = [...this.syncQueue];
      
      // Обрабатываем каждый запрос
      for (let i = 0; i < queueCopy.length; i++) {
        const request = queueCopy[i];
        
        try {
          // Выполняем запрос
          const response = await fetch(request.url, {
            method: request.method,
            headers: {
              'Content-Type': 'application/json'
            },
            body: request.method !== 'GET' ? JSON.stringify(request.data) : undefined
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          // Получаем данные ответа
          const responseData = await response.json();
          
          // Удаляем запрос из очереди
          const index = this.syncQueue.findIndex(r => 
            r.url === request.url && 
            r.method === request.method && 
            r.timestamp === request.timestamp
          );
          
          if (index !== -1) {
            this.syncQueue.splice(index, 1);
          }
          
          // Обновляем кэшированные данные
          this.updateCachedData(request.entityType, request.entityId, responseData);
          
          // Вызываем функцию обратного вызова при успехе, если она есть
          if (request.onSuccess && typeof request.onSuccess === 'function') {
            request.onSuccess(responseData);
          }
        } catch (error) {
          console.error(`Ошибка при синхронизации запроса ${request.url}:`, error);
          
          // Если ошибка не связана с сетью, удаляем запрос из очереди
          if (error.name !== 'TypeError' && error.name !== 'NetworkError') {
            const index = this.syncQueue.findIndex(r => 
              r.url === request.url && 
              r.method === request.method && 
              r.timestamp === request.timestamp
            );
            
            if (index !== -1) {
              this.syncQueue.splice(index, 1);
            }
          }
          
          // Вызываем функцию обратного вызова при ошибке, если она есть
          if (request.onError && typeof request.onError === 'function') {
            request.onError(error);
          }
        }
      }
      
      // Сохраняем обновленную очередь
      this.saveQueueToStorage();
      
      // Обновляем время последней синхронизации
      localStorage.setItem(this.STORAGE_KEYS.LAST_SYNC, Date.now().toString());
      
    } catch (error) {
      console.error('Ошибка при синхронизации данных:', error);
    } finally {
      this.isSyncing = false;
    }
  }
  
  /**
   * Обновление кэшированных данных
   * @param {string} entityType - Тип сущности
   * @param {string} entityId - ID сущности
   * @param {Object} data - Данные для кэширования
   */
  updateCachedData(entityType, entityId, data) {
    try {
      // Получаем текущие кэшированные данные
      const cachedDataJson = localStorage.getItem(this.STORAGE_KEYS.CACHED_DATA);
      const cachedData = cachedDataJson ? JSON.parse(cachedDataJson) : {};
      
      // Инициализируем структуру, если она не существует
      if (!cachedData[entityType]) {
        cachedData[entityType] = {};
      }
      
      // Обновляем данные
      if (entityId) {
        cachedData[entityType][entityId] = {
          data: data,
          timestamp: Date.now()
        };
      } else {
        // Если ID не указан, обновляем коллекцию
        if (!cachedData[entityType].collection) {
          cachedData[entityType].collection = {};
        }
        
        // Если данные представляют собой массив, обновляем каждый элемент
        if (Array.isArray(data)) {
          data.forEach(item => {
            if (item.id) {
              cachedData[entityType].collection[item.id] = {
                data: item,
                timestamp: Date.now()
              };
            }
          });
        } else {
          // Если данные представляют собой объект с коллекцией
          const collection = data[`${entityType}_sessions`] || data[entityType] || [];
          if (Array.isArray(collection)) {
            collection.forEach(item => {
              if (item.id) {
                cachedData[entityType].collection[item.id] = {
                  data: item,
                  timestamp: Date.now()
                };
              }
            });
          }
        }
      }
      
      // Сохраняем обновленные данные
      localStorage.setItem(this.STORAGE_KEYS.CACHED_DATA, JSON.stringify(cachedData));
    } catch (error) {
      console.error('Ошибка при обновлении кэшированных данных:', error);
    }
  }
  
  /**
   * Получение кэшированных данных
   * @param {string} entityType - Тип сущности
   * @param {string} entityId - ID сущности (опционально)
   * @returns {Object|Array|null} - Кэшированные данные
   */
  getCachedData(entityType, entityId) {
    try {
      // Получаем текущие кэшированные данные
      const cachedDataJson = localStorage.getItem(this.STORAGE_KEYS.CACHED_DATA);
      if (!cachedDataJson) return null;
      
      const cachedData = JSON.parse(cachedDataJson);
      
      // Проверяем наличие данных для указанного типа
      if (!cachedData[entityType]) return null;
      
      // Если указан ID, возвращаем конкретную сущность
      if (entityId) {
        return cachedData[entityType][entityId]?.data || null;
      }
      
      // Иначе возвращаем коллекцию
      if (cachedData[entityType].collection) {
        // Преобразуем объект коллекции в массив
        return Object.values(cachedData[entityType].collection)
          .map(item => item.data)
          .sort((a, b) => {
            // Сортируем по времени создания (новые сверху)
            const dateA = new Date(a.start_time || a.timestamp || a.created_at);
            const dateB = new Date(b.start_time || b.timestamp || b.created_at);
            return dateB - dateA;
          });
      }
      
      return null;
    } catch (error) {
      console.error('Ошибка при получении кэшированных данных:', error);
      return null;
    }
  }
  
  /**
   * Выполнение запроса с поддержкой офлайн-режима
   * @param {Object} options - Параметры запроса
   * @param {string} options.url - URL запроса
   * @param {string} options.method - Метод запроса (GET, POST, PUT, DELETE)
   * @param {Object} options.data - Данные запроса
   * @param {string} options.entityType - Тип сущности
   * @param {string} options.entityId - ID сущности (опционально)
   * @param {boolean} options.useCache - Использовать кэш для GET-запросов
   * @param {Function} options.onSuccess - Функция обратного вызова при успехе
   * @param {Function} options.onError - Функция обратного вызова при ошибке
   */
  async request(options) {
    const { url, method, data, entityType, entityId, useCache = true, onSuccess, onError } = options;
    
    // Для GET-запросов пытаемся сначала получить данные из кэша
    if (method === 'GET' && useCache) {
      const cachedData = this.getCachedData(entityType, entityId);
      
      if (cachedData) {
        // Если есть кэшированные данные, возвращаем их
        if (onSuccess && typeof onSuccess === 'function') {
          onSuccess(cachedData);
        }
        
        // Если онлайн, выполняем запрос для обновления кэша
        if (this.isOnline) {
          try {
            const response = await fetch(url, {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json'
              }
            });
            
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const responseData = await response.json();
            
            // Обновляем кэш
            this.updateCachedData(entityType, entityId, responseData);
            
            // Вызываем функцию обратного вызова с обновленными данными
            if (onSuccess && typeof onSuccess === 'function') {
              onSuccess(responseData);
            }
          } catch (error) {
            console.error(`Ошибка при обновлении кэша для ${url}:`, error);
          }
        }
        
        return;
      }
    }
    
    // Если нет кэшированных данных или это не GET-запрос
    if (this.isOnline) {
      // Если онлайн, выполняем запрос
      try {
        const response = await fetch(url, {
          method: method,
          headers: {
            'Content-Type': 'application/json'
          },
          body: method !== 'GET' ? JSON.stringify(data) : undefined
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const responseData = await response.json();
        
        // Обновляем кэш для GET-запросов
        if (method === 'GET') {
          this.updateCachedData(entityType, entityId, responseData);
        }
        
        // Вызываем функцию обратного вызова при успехе
        if (onSuccess && typeof onSuccess === 'function') {
          onSuccess(responseData);
        }
      } catch (error) {
        console.error(`Ошибка при выполнении запроса ${url}:`, error);
        
        // Если это сетевая ошибка, добавляем запрос в очередь
        if (error.name === 'TypeError' || error.name === 'NetworkError') {
          this.addToSyncQueue({ url, method, data, entityType, entityId, onSuccess, onError });
        }
        
        // Вызываем функцию обратного вызова при ошибке
        if (onError && typeof onError === 'function') {
          onError(error);
        }
      }
    } else {
      // Если офлайн, добавляем запрос в очередь
      this.addToSyncQueue({ url, method, data, entityType, entityId, onSuccess, onError });
      
      // Для GET-запросов возвращаем пустые данные или заглушку
      if (method === 'GET' && onSuccess && typeof onSuccess === 'function') {
        if (entityId) {
          onSuccess({ id: entityId, offline: true });
        } else {
          onSuccess({ [entityType]: [], offline: true });
        }
      }
    }
  }
  
  /**
   * Разрешение конфликтов при синхронизации
   * @param {Object} localData - Локальные данные
   * @param {Object} serverData - Данные с сервера
   * @param {string} entityType - Тип сущности
   * @returns {Object} - Разрешенные данные
   */
  resolveConflict(localData, serverData, entityType) {
    // Стратегия разрешения конфликтов зависит от типа сущности
    switch (entityType) {
      case 'sleep':
      case 'feeding':
      case 'contraction':
      case 'kick':
        // Для таймеров и счетчиков используем стратегию "последний выигрывает"
        // Сравниваем временные метки обновления
        const localTimestamp = new Date(localData.updated_at || localData.end_time || localData.timestamp);
        const serverTimestamp = new Date(serverData.updated_at || serverData.end_time || serverData.timestamp);
        
        return serverTimestamp >= localTimestamp ? serverData : localData;
        
      case 'child':
      case 'measurement':
        // Для профилей и измерений объединяем данные
        return { ...localData, ...serverData };
        
      default:
        // По умолчанию используем данные с сервера
        return serverData;
    }
  }
  
  /**
   * Очистка устаревших кэшированных данных
   * @param {number} maxAge - Максимальный возраст данных в миллисекундах
   */
  clearOldCachedData(maxAge = 7 * 24 * 60 * 60 * 1000) { // По умолчанию 7 дней
    try {
      // Получаем текущие кэшированные данные
      const cachedDataJson = localStorage.getItem(this.STORAGE_KEYS.CACHED_DATA);
      if (!cachedDataJson) return;
      
      const cachedData = JSON.parse(cachedDataJson);
      const now = Date.now();
      
      // Проходим по всем типам сущностей
      Object.keys(cachedData).forEach(entityType => {
        // Проходим по коллекции
        if (cachedData[entityType].collection) {
          Object.keys(cachedData[entityType].collection).forEach(itemId => {
            const item = cachedData[entityType].collection[itemId];
            
            // Если данные устарели, удаляем их
            if (now - item.timestamp > maxAge) {
              delete cachedData[entityType].collection[itemId];
            }
          });
        }
        
        // Проходим по отдельным сущностям
        Object.keys(cachedData[entityType]).forEach(itemId => {
          if (itemId !== 'collection') {
            const item = cachedData[entityType][itemId];
            
            // Если данные устарели, удаляем их
            if (now - item.timestamp > maxAge) {
              delete cachedData[entityType][itemId];
            }
          }
        });
      });
      
      // Сохраняем обновленные данные
      localStorage.setItem(this.STORAGE_KEYS.CACHED_DATA, JSON.stringify(cachedData));
    } catch (error) {
      console.error('Ошибка при очистке устаревших кэшированных данных:', error);
    }
  }
}

// Создаем глобальный экземпляр DataSync
window.dataSync = new DataSync();

// Инициализируем DataSync при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  // Загружаем очередь синхронизации из localStorage
  window.dataSync.loadQueueFromStorage();
  
  // Очищаем устаревшие кэшированные данные
  window.dataSync.clearOldCachedData();
  
  // Если онлайн, запускаем синхронизацию
  if (window.dataSync.isOnline) {
    window.dataSync.syncQueuedData();
  }
});/**
 *
 Обработчик конфликтов синхронизации
 * Этот класс расширяет функциональность DataSync для обработки конфликтов
 */
class ConflictResolver {
  constructor(dataSync) {
    this.dataSync = dataSync;
  }
  
  /**
   * Обработка конфликта данных
   * @param {Object} localData - Локальные данные
   * @param {Object} serverData - Данные с сервера
   * @param {string} entityType - Тип сущности
   * @returns {Object} - Разрешенные данные
   */
  resolveConflict(localData, serverData, entityType) {
    // Если одни из данных отсутствуют, возвращаем другие
    if (!localData) return serverData;
    if (!serverData) return localData;
    
    // Стратегия разрешения конфликтов зависит от типа сущности
    switch (entityType) {
      case 'sleep':
        return this.resolveSleepConflict(localData, serverData);
      
      case 'feeding':
        return this.resolveFeedingConflict(localData, serverData);
      
      case 'contraction':
      case 'kick':
        return this.resolveEventConflict(localData, serverData);
      
      case 'child':
      case 'measurement':
        return this.resolveProfileConflict(localData, serverData);
      
      default:
        // По умолчанию используем данные с сервера
        return serverData;
    }
  }
  
  /**
   * Разрешение конфликта для сессий сна
   */
  resolveSleepConflict(localData, serverData) {
    // Если локальная сессия завершена, а серверная нет, используем локальную
    if (localData.end_time && !serverData.end_time) {
      return localData;
    }
    
    // Если серверная сессия завершена, а локальная нет, используем серверную
    if (!localData.end_time && serverData.end_time) {
      return serverData;
    }
    
    // Если обе сессии завершены, используем ту, которая была обновлена позже
    if (localData.end_time && serverData.end_time) {
      const localEndTime = new Date(localData.end_time);
      const serverEndTime = new Date(serverData.end_time);
      
      return serverEndTime >= localEndTime ? serverData : localData;
    }
    
    // Если обе сессии не завершены, объединяем данные
    return { ...serverData, ...localData };
  }
  
  /**
   * Разрешение конфликта для сессий кормления
   */
  resolveFeedingConflict(localData, serverData) {
    // Для кормления используем стратегию "последний выигрывает"
    const localTimestamp = new Date(localData.updated_at || localData.timestamp);
    const serverTimestamp = new Date(serverData.updated_at || serverData.timestamp);
    
    return serverTimestamp >= localTimestamp ? serverData : localData;
  }
  
  /**
   * Разрешение конфликта для событий (схватки, шевеления)
   */
  resolveEventConflict(localData, serverData) {
    // Для событий объединяем списки событий
    if (localData.events && serverData.events) {
      // Создаем карту событий по ID
      const eventsMap = new Map();
      
      // Добавляем серверные события
      serverData.events.forEach(event => {
        eventsMap.set(event.id, event);
      });
      
      // Добавляем локальные события, если их нет на сервере или они новее
      localData.events.forEach(event => {
        if (!eventsMap.has(event.id)) {
          eventsMap.set(event.id, event);
        } else {
          const serverEvent = eventsMap.get(event.id);
          const localTimestamp = new Date(event.updated_at || event.timestamp);
          const serverTimestamp = new Date(serverEvent.updated_at || serverEvent.timestamp);
          
          if (localTimestamp > serverTimestamp) {
            eventsMap.set(event.id, event);
          }
        }
      });
      
      // Создаем новый объект с объединенными событиями
      return {
        ...serverData,
        events: Array.from(eventsMap.values())
      };
    }
    
    // Если нет списков событий, используем стратегию "последний выигрывает"
    const localTimestamp = new Date(localData.updated_at || localData.timestamp);
    const serverTimestamp = new Date(serverData.updated_at || serverData.timestamp);
    
    return serverTimestamp >= localTimestamp ? serverData : localData;
  }
  
  /**
   * Разрешение конфликта для профилей и измерений
   */
  resolveProfileConflict(localData, serverData) {
    // Для профилей и измерений объединяем данные
    // При этом для полей, которые есть в обоих объектах, используем более новые
    const result = { ...serverData };
    
    Object.keys(localData).forEach(key => {
      // Если поле есть только в локальных данных, добавляем его
      if (!(key in serverData)) {
        result[key] = localData[key];
        return;
      }
      
      // Если поле есть в обоих объектах, сравниваем временные метки
      if (localData.updated_at && serverData.updated_at) {
        const localTimestamp = new Date(localData.updated_at);
        const serverTimestamp = new Date(serverData.updated_at);
        
        if (localTimestamp > serverTimestamp) {
          result[key] = localData[key];
        }
      }
    });
    
    return result;
  }
}

// Добавляем обработчик конфликтов к DataSync
document.addEventListener('DOMContentLoaded', () => {
  if (window.dataSync) {
    window.dataSync.conflictResolver = new ConflictResolver(window.dataSync);
    
    // Переопределяем метод resolveConflict
    const originalResolveConflict = window.dataSync.resolveConflict;
    window.dataSync.resolveConflict = function(localData, serverData, entityType) {
      if (this.conflictResolver) {
        return this.conflictResolver.resolveConflict(localData, serverData, entityType);
      }
      return originalResolveConflict.call(this, localData, serverData, entityType);
    };
  }
});