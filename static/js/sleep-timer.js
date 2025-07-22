/**
 * Модуль для работы с таймером сна
 * Использует TimerManager для фоновой работы и синхронизации
 */

// Глобальные переменные
let userId = null;
let childId = null;
let currentSessionId = null;
let timerInterval = null;
let startTime = null;
let sleepType = 'day';
let sleepQuality = 3;
let chart = null;

// DOM элементы
let timerElement;
let startButton;
let stopButton;
let currentSleepTypeElement;
let startTimeElement;
let sleepHistoryElement;
let noHistoryMessage;
let sleepQualityContainer;
let qualityButtons;

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  // Получаем DOM элементы
  timerElement = document.getElementById('timer');
  startButton = document.getElementById('startButton');
  stopButton = document.getElementById('stopButton');
  currentSleepTypeElement = document.getElementById('currentSleepType');
  startTimeElement = document.getElementById('startTime');
  sleepHistoryElement = document.getElementById('sleepHistory');
  noHistoryMessage = document.getElementById('noHistoryMessage');
  sleepQualityContainer = document.getElementById('sleepQualityContainer');
  qualityButtons = document.querySelectorAll('.quality-btn');
  
  // Получаем ID пользователя и ребенка
  userId = document.getElementById('userId')?.value;
  childId = document.getElementById('childId')?.value;
  
  if (!userId || !childId) {
    console.error('Не удалось получить ID пользователя или ребенка');
    return;
  }
  
  // Загрузка истории сна
  loadSleepHistory();
  
  // Загрузка статистики для графика
  loadSleepStatistics();
  
  // Обработчики событий для вкладок типа сна
  document.querySelectorAll('.neo-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.neo-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      if (tab.dataset.tabTarget === 'day-sleep') {
        sleepType = 'day';
        currentSleepTypeElement.textContent = 'Дневной';
      } else {
        sleepType = 'night';
        currentSleepTypeElement.textContent = 'Ночной';
      }
    });
  });
  
  // Обработчик для кнопки "Начать"
  startButton.addEventListener('click', startSleepTimer);
  
  // Обработчик для кнопки "Завершить"
  stopButton.addEventListener('click', stopSleepTimer);
  
  // Обработчики для кнопок качества сна
  qualityButtons.forEach(button => {
    button.addEventListener('click', () => {
      qualityButtons.forEach(btn => btn.classList.remove('bg-primary'));
      button.classList.add('bg-primary');
      sleepQuality = parseInt(button.dataset.quality);
    });
  });
  
  // Обработчики событий от TimerManager
  document.addEventListener('timerManager:timerStarted', (event) => {
    const { timerId, startTime: timerStartTime, timerType } = event.detail;
    
    // Проверяем, что это таймер сна для текущего ребенка
    if (timerType === 'sleep' && timerId.includes(`sleep-${childId}`)) {
      updateUIForActiveTimer(timerId, timerStartTime);
    }
  });
  
  document.addEventListener('timerManager:timerStopped', (event) => {
    const { timerId } = event.detail;
    
    // Проверяем, что это таймер сна для текущего ребенка
    if (timerId.includes(`sleep-${childId}`)) {
      resetUI();
      loadSleepHistory();
      loadSleepStatistics();
    }
  });
  
  // Проверка наличия активной сессии
  checkForActiveSleepSession();
});

// Функция для форматирования времени
function formatTime(seconds) {
  return TimerManager.formatTime(seconds);
}

// Функция для форматирования даты и времени
function formatDateTime(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Функция для расчета продолжительности в минутах
function calculateDuration(startTime, endTime) {
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
  return Math.round((end - start) / (1000 * 60));
}

// Функция для форматирования продолжительности
function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours > 0) {
    return `${hours} ч ${mins} мин`;
  } else {
    return `${mins} мин`;
  }
}

// Функция для запуска таймера сна
function startSleepTimer() {
  // Используем dataSync для создания сессии сна с поддержкой офлайн-режима
  window.dataSync.request({
    url: `/api/users/${userId}/children/${childId}/sleep/`,
    method: 'POST',
    data: {
      type: sleepType
    },
    entityType: 'sleep',
    onSuccess: (data) => {
      currentSessionId = data.id;
      startTime = new Date(data.start_time);
      
      // Запускаем таймер через TimerManager
      const timerId = `sleep-${childId}-${currentSessionId}`;
      window.timerManager.startTimer(timerId, 'sleep', {
        userId: userId,
        childId: childId,
        sessionId: currentSessionId,
        sleepType: sleepType
      });
      
      // Обновляем UI
      updateUIForActiveTimer(timerId, startTime.getTime());
    },
    onError: (error) => {
      console.error('Ошибка при запуске таймера:', error);
      
      // Если мы в офлайн-режиме, создаем временный ID и запускаем таймер
      if (!navigator.onLine) {
        const tempId = `temp-${Date.now()}`;
        currentSessionId = tempId;
        startTime = new Date();
        
        // Запускаем таймер через TimerManager
        const timerId = `sleep-${childId}-${tempId}`;
        window.timerManager.startTimer(timerId, 'sleep', {
          userId: userId,
          childId: childId,
          sessionId: tempId,
          sleepType: sleepType,
          isOffline: true
        });
        
        // Обновляем UI
        updateUIForActiveTimer(timerId, startTime.getTime());
        
        // Показываем уведомление о работе в офлайн-режиме
        const offlineNotice = document.createElement('div');
        offlineNotice.className = 'mt-4 p-2 bg-yellow-100 text-yellow-800 rounded text-center text-sm';
        offlineNotice.textContent = 'Таймер запущен в офлайн-режиме. Данные будут синхронизированы с сервером при восстановлении соединения.';
        document.querySelector('.timer-container').appendChild(offlineNotice);
        
        // Удаляем уведомление через 5 секунд
        setTimeout(() => {
          if (offlineNotice.parentNode) {
            offlineNotice.parentNode.removeChild(offlineNotice);
          }
        }, 5000);
      } else {
        alert('Произошла ошибка при запуске таймера сна');
      }
    }
  });
}

// Функция для остановки таймера сна
function stopSleepTimer() {
  // Показываем контейнер для выбора качества сна
  sleepQualityContainer.classList.remove('hidden');
  
  // Останавливаем таймер
  clearInterval(timerInterval);
  
  // Проверяем, является ли сессия временной (созданной в офлайн-режиме)
  const isOfflineSession = currentSessionId && currentSessionId.toString().startsWith('temp-');
  
  // Используем dataSync для завершения сессии сна с поддержкой офлайн-режима
  window.dataSync.request({
    url: `/api/users/${userId}/children/${childId}/sleep/${currentSessionId}/`,
    method: 'PUT',
    data: {
      end_session: true,
      quality: sleepQuality
    },
    entityType: 'sleep',
    entityId: currentSessionId,
    onSuccess: (data) => {
      // Останавливаем таймер в TimerManager
      const timerId = `sleep-${childId}-${currentSessionId}`;
      window.timerManager.stopTimer(timerId);
      
      // Сбрасываем UI
      resetUI();
      
      // Перезагружаем историю сна и статистику
      loadSleepHistory();
      loadSleepStatistics();
      
      // Скрываем контейнер для выбора качества сна через 3 секунды
      setTimeout(() => {
        sleepQualityContainer.classList.add('hidden');
      }, 3000);
      
      // Отправляем уведомление через Telegram, если интеграция доступна
      if (window.telegramIntegration) {
        window.telegramIntegration.sendSleepCompletedNotification(data);
      }
    },
    onError: (error) => {
      console.error('Ошибка при остановке таймера:', error);
      
      // Если мы в офлайн-режиме, сохраняем данные локально
      if (!navigator.onLine || isOfflineSession) {
        // Останавливаем таймер в TimerManager
        const timerId = `sleep-${childId}-${currentSessionId}`;
        window.timerManager.stopTimer(timerId);
        
        // Сбрасываем UI
        resetUI();
        
        // Перезагружаем историю сна и статистику
        loadSleepHistory();
        loadSleepStatistics();
        
        // Скрываем контейнер для выбора качества сна через 3 секунды
        setTimeout(() => {
          sleepQualityContainer.classList.add('hidden');
        }, 3000);
        
        // Показываем уведомление о работе в офлайн-режиме
        const offlineNotice = document.createElement('div');
        offlineNotice.className = 'mt-4 p-2 bg-yellow-100 text-yellow-800 rounded text-center text-sm';
        offlineNotice.textContent = 'Данные сохранены локально и будут синхронизированы с сервером при восстановлении соединения.';
        document.querySelector('.timer-container').appendChild(offlineNotice);
        
        // Удаляем уведомление через 5 секунд
        setTimeout(() => {
          if (offlineNotice.parentNode) {
            offlineNotice.parentNode.removeChild(offlineNotice);
          }
        }, 5000);
      } else {
        alert('Произошла ошибка при завершении таймера сна');
      }
    }
  });
}

// Функция для загрузки истории сна
function loadSleepHistory() {
  // Используем dataSync для загрузки данных с поддержкой офлайн-режима
  window.dataSync.request({
    url: `/api/users/${userId}/children/${childId}/sleep/`,
    method: 'GET',
    entityType: 'sleep',
    useCache: true,
    onSuccess: (data) => {
      const sleepSessions = data.sleep_sessions || [];
      
      // Очищаем историю
      sleepHistoryElement.innerHTML = '';
      
      if (sleepSessions.length === 0) {
        sleepHistoryElement.innerHTML = '<p class="text-center text-dark-gray">История сна пуста</p>';
        return;
      }
      
      // Сортируем сессии по дате (новые сверху)
      sleepSessions.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
      
      // Отображаем последние 10 сессий
      const recentSessions = sleepSessions.slice(0, 10);
      
      recentSessions.forEach(session => {
        const sessionElement = document.createElement('div');
        sessionElement.className = 'glass-card p-4';
        
        const typeLabel = session.type === 'day' ? 'Дневной сон' : 'Ночной сон';
        const startTime = formatDateTime(session.start_time);
        const endTime = session.end_time ? formatDateTime(session.end_time) : 'В процессе';
        const duration = session.end_time ? formatDuration(calculateDuration(session.start_time, session.end_time)) : 'В процессе';
        
        let qualityStars = '';
        if (session.quality) {
          for (let i = 1; i <= 5; i++) {
            if (i <= session.quality) {
              qualityStars += '★';
            } else {
              qualityStars += '☆';
            }
          }
        }
        
        // Добавляем индикатор офлайн-режима, если данные не синхронизированы
        const offlineIndicator = session.offline ? 
          '<span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded ml-2">Не синхронизировано</span>' : '';
        
        sessionElement.innerHTML = `
          <div class="flex justify-between items-center mb-2">
            <span class="font-semibold">${typeLabel}${offlineIndicator}</span>
            <span class="text-sm text-dark-gray">${startTime}</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span class="text-dark-gray">Окончание:</span>
              <span>${endTime}</span>
            </div>
            <div>
              <span class="text-dark-gray">Продолжительность:</span>
              <span>${duration}</span>
            </div>
            ${session.quality ? `
            <div>
              <span class="text-dark-gray">Качество:</span>
              <span class="text-yellow-500">${qualityStars}</span>
            </div>
            ` : ''}
          </div>
        `;
        
        sleepHistoryElement.appendChild(sessionElement);
      });
      
      // Если данные загружены из офлайн-кэша, показываем уведомление
      if (data.offline) {
        const offlineNotice = document.createElement('div');
        offlineNotice.className = 'mt-4 p-2 bg-yellow-100 text-yellow-800 rounded text-center text-sm';
        offlineNotice.textContent = 'Данные загружены из локального кэша. Они будут синхронизированы с сервером при восстановлении соединения.';
        sleepHistoryElement.appendChild(offlineNotice);
      }
    },
    onError: (error) => {
      console.error('Ошибка при загрузке истории сна:', error);
      sleepHistoryElement.innerHTML = '<p class="text-center text-dark-gray">Не удалось загрузить историю сна</p>';
    }
  });
}

// Функция для загрузки статистики сна
function loadSleepStatistics() {
  // Используем dataSync для загрузки статистики с поддержкой офлайн-режима
  window.dataSync.request({
    url: `/api/users/${userId}/children/${childId}/sleep/statistics/`,
    method: 'GET',
    entityType: 'sleep_statistics',
    useCache: true,
    onSuccess: (data) => {
      // Создаем график
      createSleepChart(data);
      
      // Если данные загружены из офлайн-кэша, показываем уведомление
      if (data.offline) {
        const chartContainer = document.getElementById('sleepChart');
        const offlineNotice = document.createElement('div');
        offlineNotice.className = 'mt-2 p-2 bg-yellow-100 text-yellow-800 rounded text-center text-xs';
        offlineNotice.textContent = 'Статистика загружена из локального кэша и может быть неактуальной.';
        chartContainer.appendChild(offlineNotice);
      }
    },
    onError: (error) => {
      console.error('Ошибка при загрузке статистики сна:', error);
      document.getElementById('sleepChart').innerHTML = '<p class="text-center text-dark-gray">Не удалось загрузить статистику сна</p>';
      
      // Если мы в офлайн-режиме, показываем заглушку
      if (!navigator.onLine) {
        createSleepChart({
          avg_day_sleep: 0,
          avg_night_sleep: 0,
          offline: true
        });
        
        const chartContainer = document.getElementById('sleepChart');
        const offlineNotice = document.createElement('div');
        offlineNotice.className = 'mt-2 p-2 bg-yellow-100 text-yellow-800 rounded text-center text-xs';
        offlineNotice.textContent = 'Статистика недоступна в офлайн-режиме. Данные будут обновлены при восстановлении соединения.';
        chartContainer.appendChild(offlineNotice);
      }
    }
  });
}

// Функция для создания графика сна
function createSleepChart(data) {
  const ctx = document.getElementById('sleepChartCanvas').getContext('2d');
  
  // Если график уже существует, уничтожаем его
  if (chart) {
    chart.destroy();
  }
  
  // Создаем новый график
  chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Дневной сон', 'Ночной сон'],
      datasets: [{
        label: 'Среднее время сна (мин)',
        data: [data.avg_day_sleep, data.avg_night_sleep],
        backgroundColor: [
          'rgba(255, 214, 224, 0.7)',
          'rgba(226, 214, 255, 0.7)'
        ],
        borderColor: [
          'rgba(255, 214, 224, 1)',
          'rgba(226, 214, 255, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Минуты'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const value = context.raw;
              return formatDuration(value);
            }
          }
        }
      }
    }
  });
}

// Функция для проверки наличия активной сессии
function checkForActiveSleepSession() {
  // Проверяем наличие активных таймеров сна для текущего ребенка
  const activeTimers = window.timerManager.getAllActiveTimers();
  
  for (const timer of activeTimers) {
    if (timer.type === 'sleep' && timer.metadata?.childId == childId) {
      currentSessionId = timer.metadata.sessionId;
      startTime = new Date(timer.startTime);
      sleepType = timer.metadata.sleepType;
      
      // Обновляем UI
      updateUIForActiveTimer(timer.timerId, timer.startTime);
      return;
    }
  }
  
  // Если активный таймер не найден, проверяем API
  checkActiveSessionFromAPI();
}

// Функция для проверки активной сессии через API
function checkActiveSessionFromAPI() {
  // Используем dataSync для проверки активной сессии с поддержкой офлайн-режима
  window.dataSync.request({
    url: `/api/users/${userId}/children/${childId}/sleep/active/`,
    method: 'GET',
    entityType: 'active_sleep',
    useCache: true,
    onSuccess: (data) => {
      if (data && data.id) {
        currentSessionId = data.id;
        startTime = new Date(data.start_time);
        sleepType = data.type;
        
        // Запускаем таймер через TimerManager
        const timerId = `sleep-${childId}-${currentSessionId}`;
        window.timerManager.startTimer(timerId, 'sleep', {
          userId: userId,
          childId: childId,
          sessionId: currentSessionId,
          sleepType: sleepType
        });
        
        // Обновляем UI
        updateUIForActiveTimer(timerId, startTime.getTime());
      }
    },
    onError: (error) => {
      console.error('Ошибка при проверке активной сессии:', error);
      
      // В офлайн-режиме не показываем ошибку, просто продолжаем работу
      if (!navigator.onLine) {
        console.log('Работа в офлайн-режиме, активные сессии будут проверены при восстановлении соединения');
      }
    }
  });
}

// Функция для обновления UI при активном таймере
function updateUIForActiveTimer(timerId, timerStartTime) {
  // Обновляем UI
  startButton.disabled = true;
  stopButton.disabled = false;
  startTimeElement.textContent = formatDateTime(new Date(timerStartTime));
  
  // Устанавливаем правильный тип сна
  document.querySelectorAll('.neo-tab').forEach(tab => {
    tab.classList.remove('active');
    if ((tab.dataset.tabTarget === 'day-sleep' && sleepType === 'day') || 
        (tab.dataset.tabTarget === 'night-sleep' && sleepType === 'night')) {
      tab.classList.add('active');
    }
  });
  
  currentSleepTypeElement.textContent = sleepType === 'day' ? 'Дневной' : 'Ночной';
  
  // Запускаем таймер для обновления отображения
  clearInterval(timerInterval);
  
  const updateTimerDisplay = () => {
    const elapsedSeconds = TimerManager.getElapsedSeconds(timerStartTime);
    timerElement.textContent = formatTime(elapsedSeconds);
  };
  
  // Обновляем отображение сразу
  updateTimerDisplay();
  
  // Запускаем интервал для обновления отображения
  timerInterval = setInterval(updateTimerDisplay, 1000);
}

// Функция для сброса UI
function resetUI() {
  clearInterval(timerInterval);
  startButton.disabled = false;
  stopButton.disabled = true;
  timerElement.textContent = '00:00:00';
  startTimeElement.textContent = '-';
  currentSessionId = null;
  startTime = null;
}