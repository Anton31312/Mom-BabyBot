/**
 * Service Worker для приложения Mom&BabyBot
 * Обеспечивает фоновую работу таймеров и локальное хранение данных
 */

const CACHE_NAME = 'mom-baby-bot-cache-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/maternal-theme.css',
  '/static/css/neomorphism.css',
  '/static/css/glassmorphism.css',
  '/static/css/style.css',
  '/static/js/neomorphism.js',
  '/static/js/glassmorphism.js',
  '/static/js/maternal-app.js',
  '/static/js/timer-manager.js',
  '/static/js/data-sync.js',
  '/static/js/sleep-timer.js',
  '/static/images/logo.png',
  '/static/images/badge.png'
];

// Установка Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Кэширование статических ресурсов');
        return cache.addAll(ASSETS_TO_CACHE);
      })
  );
  self.skipWaiting();
});

// Активация Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          return cacheName !== CACHE_NAME;
        }).map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
  self.clients.claim();
});

// Перехват запросов
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Для API запросов используем стратегию "сначала сеть, затем кэш"
  if (url.pathname.includes('/api/')) {
    event.respondWith(
      fetch(event.request.clone())
        .then(response => {
          // Если запрос успешен, кэшируем ответ
          if (response.ok) {
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
          }
          return response;
        })
        .catch(() => {
          // При ошибке сети пытаемся получить из кэша
          return caches.match(event.request)
            .then(cachedResponse => {
              if (cachedResponse) {
                return cachedResponse;
              }
              
              // Если в кэше нет, возвращаем заглушку для API
              if (event.request.headers.get('accept').includes('application/json')) {
                return new Response(
                  JSON.stringify({ 
                    error: 'offline',
                    message: 'Нет подключения к сети. Данные будут синхронизированы позже.',
                    offline: true 
                  }),
                  { 
                    status: 200, 
                    headers: { 'Content-Type': 'application/json' } 
                  }
                );
              }
              
              // Для других запросов возвращаем ошибку
              return new Response('Нет подключения к сети', { status: 503 });
            });
        })
    );
  } 
  // Для статических ресурсов используем стратегию "сначала кэш, затем сеть"
  else {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          // Возвращаем кэшированный ответ, если он есть
          if (response) {
            return response;
          }
          
          // Клонируем запрос, так как он может быть использован только один раз
          const fetchRequest = event.request.clone();
          
          return fetch(fetchRequest).then(response => {
            // Проверяем, что ответ валидный
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Клонируем ответ, так как он может быть использован только один раз
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
              
            return response;
          })
          .catch(() => {
            // Для HTML страниц возвращаем офлайн-страницу
            if (event.request.headers.get('accept').includes('text/html')) {
              return caches.match('/');
            }
            
            // Для других ресурсов возвращаем ошибку
            return new Response('Нет подключения к сети', { status: 503 });
          });
        })
    );
  }
});

// Обработка сообщений от клиента
self.addEventListener('message', event => {
  const data = event.data;
  
  if (data.action === 'startTimer') {
    // Запуск таймера в фоновом режиме
    startBackgroundTimer(data.timerId, data.startTime, data.timerType);
  } else if (data.action === 'stopTimer') {
    // Остановка таймера
    stopBackgroundTimer(data.timerId);
  } else if (data.action === 'checkTimers') {
    // Проверка активных таймеров
    checkActiveTimers();
  }
});

// Хранилище активных таймеров
const activeTimers = new Map();

// Запуск таймера в фоновом режиме
function startBackgroundTimer(timerId, startTime, timerType) {
  // Сохраняем информацию о таймере
  activeTimers.set(timerId, {
    startTime: startTime,
    type: timerType,
    intervalId: setInterval(() => {
      // Отправляем уведомление каждые 5 минут для длительных таймеров
      const elapsedMinutes = Math.floor((Date.now() - startTime) / (1000 * 60));
      if (elapsedMinutes > 0 && elapsedMinutes % 5 === 0) {
        sendTimerNotification(timerId, timerType, elapsedMinutes);
      }
    }, 60000) // Проверка каждую минуту
  });
  
  // Отправляем подтверждение клиенту
  self.clients.matchAll().then(clients => {
    clients.forEach(client => {
      client.postMessage({
        action: 'timerStarted',
        timerId: timerId,
        startTime: startTime,
        timerType: timerType
      });
    });
  });
}

// Остановка таймера
function stopBackgroundTimer(timerId) {
  if (activeTimers.has(timerId)) {
    clearInterval(activeTimers.get(timerId).intervalId);
    activeTimers.delete(timerId);
    
    // Отправляем подтверждение клиенту
    self.clients.matchAll().then(clients => {
      clients.forEach(client => {
        client.postMessage({
          action: 'timerStopped',
          timerId: timerId
        });
      });
    });
  }
}

// Проверка активных таймеров
function checkActiveTimers() {
  const timersData = Array.from(activeTimers.entries()).map(([id, data]) => {
    return {
      timerId: id,
      startTime: data.startTime,
      type: data.type
    };
  });
  
  // Отправляем информацию о активных таймерах клиенту
  self.clients.matchAll().then(clients => {
    clients.forEach(client => {
      client.postMessage({
        action: 'activeTimers',
        timers: timersData
      });
    });
  });
}

// Отправка уведомления о работающем таймере
function sendTimerNotification(timerId, timerType, elapsedMinutes) {
  let title, body;
  
  switch (timerType) {
    case 'sleep':
      const sleepType = timerId.includes('day') ? 'дневного' : 'ночного';
      title = `Таймер ${sleepType} сна активен`;
      body = `Ребенок спит уже ${elapsedMinutes} минут`;
      break;
    case 'feeding':
      title = 'Таймер кормления активен';
      body = `Кормление продолжается уже ${elapsedMinutes} минут`;
      break;
    case 'contraction':
      title = 'Счетчик схваток активен';
      body = `Отслеживание схваток: ${elapsedMinutes} минут`;
      break;
    case 'kick':
      title = 'Счетчик шевелений активен';
      body = `Отслеживание шевелений: ${elapsedMinutes} минут`;
      break;
    default:
      title = 'Таймер активен';
      body = `Таймер работает уже ${elapsedMinutes} минут`;
  }
  
  // Отправляем уведомление через браузер
  self.registration.showNotification(title, {
    body: body,
    icon: '/static/images/logo.png',
    badge: '/static/images/badge.png',
    tag: `timer-${timerId}`,
    renotify: true,
    data: {
      timerId: timerId,
      timerType: timerType
    },
    actions: [
      {
        action: 'open',
        title: 'Открыть'
      },
      {
        action: 'stop',
        title: 'Остановить'
      }
    ]
  });
  
  // Пытаемся отправить уведомление через Telegram, если есть метаданные пользователя
  const timer = activeTimers.get(timerId);
  if (timer && timer.metadata && timer.metadata.userId) {
    // Получаем данные из метаданных таймера
    const { userId, childId } = timer.metadata;
    
    // Формируем данные для уведомления
    const notificationData = {
      notification_type: timerType,
      entity_id: timerId.split('-').pop(),
      data: {
        child_id: childId,
        duration_minutes: elapsedMinutes,
        message: body
      }
    };
    
    // Для разных типов таймеров добавляем специфичные данные
    if (timerType === 'sleep') {
      notificationData.data.sleep_type = timerId.includes('day') ? 'day' : 'night';
    }
    
    // Отправляем запрос на сервер для отправки уведомления через Telegram
    // Но делаем это только каждые 30 минут, чтобы не спамить
    if (elapsedMinutes % 30 === 0) {
      fetch(`/api/users/${userId}/notifications/send/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(notificationData)
      }).catch(error => {
        console.error('Ошибка при отправке уведомления через Telegram:', error);
      });
    }
  }
}

// Обработка кликов по уведомлениям
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'stop') {
    // Остановка таймера при клике на кнопку "Остановить"
    const timerId = event.notification.data.timerId;
    stopBackgroundTimer(timerId);
  } else {
    // Открытие приложения при клике на уведомление или кнопку "Открыть"
    event.waitUntil(
      self.clients.matchAll({ type: 'window' }).then(clientList => {
        // Если есть открытое окно, фокусируемся на нем
        for (const client of clientList) {
          if (client.url.includes('/tools/') && 'focus' in client) {
            return client.focus();
          }
        }
        // Если нет открытого окна, открываем новое
        if (self.clients.openWindow) {
          let url = '/';
          const timerType = event.notification.data.timerType;
          
          // Определяем URL в зависимости от типа таймера
          switch (timerType) {
            case 'sleep':
              url = '/tools/sleep_timer/';
              break;
            case 'feeding':
              url = '/tools/feeding_tracker/';
              break;
            case 'contraction':
              url = '/tools/contraction_counter/';
              break;
            case 'kick':
              url = '/tools/kick_counter/';
              break;
          }
          
          return self.clients.openWindow(url);
        }
      })
    );
  }
});