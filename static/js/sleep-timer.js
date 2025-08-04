/**
 * Модуль для работы с таймером сна
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
let elapsedSeconds = 0;

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
  
  // Проверка наличия активной сессии
  checkForActiveSleepSession();
});

// Функция для форматирования времени
function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  return [
    hours.toString().padStart(2, '0'),
    minutes.toString().padStart(2, '0'),
    secs.toString().padStart(2, '0')
  ].join(':');
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
  // Создаем временную сессию
  currentSessionId = `temp-${Date.now()}`;
  startTime = new Date();
  elapsedSeconds = 0;
  
  // Сохраняем активную сессию в localStorage
  const activeSession = {
    id: currentSessionId,
    type: sleepType,
    start_time: startTime.toISOString()
  };
  localStorage.setItem('activeSleepSession', JSON.stringify(activeSession));
  
  // Обновляем UI
  startButton.disabled = true;
  stopButton.disabled = false;
  startTimeElement.textContent = formatDateTime(startTime);
  currentSleepTypeElement.textContent = sleepType === 'day' ? 'Дневной' : 'Ночной';
  
  // Запускаем таймер
  timerInterval = setInterval(() => {
    elapsedSeconds++;
    timerElement.textContent = formatTime(elapsedSeconds);
  }, 1000);
  
  // Показываем уведомление
  showNotification('Таймер сна запущен', 'success');
}

// Функция для остановки таймера сна
function stopSleepTimer() {
  // Показываем контейнер для выбора качества сна
  sleepQualityContainer.classList.remove('hidden');
  
  // Останавливаем таймер
  clearInterval(timerInterval);
  
  // Создаем запись о сне
  const sleepSession = {
    id: currentSessionId,
    type: sleepType,
    start_time: startTime.toISOString(),
    end_time: new Date().toISOString(),
    duration: elapsedSeconds,
    quality: sleepQuality
  };
  
  // Сохраняем в localStorage
  const existingSessions = JSON.parse(localStorage.getItem('sleepSessions') || '[]');
  existingSessions.unshift(sleepSession);
  localStorage.setItem('sleepSessions', JSON.stringify(existingSessions.slice(0, 50))); // Храним только последние 50
  
  // Сбрасываем UI
  resetUI();
  
  // Перезагружаем историю сна и статистику
  loadSleepHistory();
  loadSleepStatistics();
  
  // Скрываем контейнер для выбора качества сна через 3 секунды
  setTimeout(() => {
    sleepQualityContainer.classList.add('hidden');
  }, 3000);
  
  // Показываем уведомление
  const durationMinutes = Math.round(elapsedSeconds / 60);
  showNotification(`Сон завершен: ${durationMinutes} мин`, 'success');
}

// Функция для загрузки истории сна
function loadSleepHistory() {
  // Загружаем данные из localStorage
  const sleepSessions = JSON.parse(localStorage.getItem('sleepSessions') || '[]');
  
  // Очищаем историю
  sleepHistoryElement.innerHTML = '';
  
  if (sleepSessions.length === 0) {
    sleepHistoryElement.innerHTML = '<p class="text-center text-dark-gray">История сна будет отображаться здесь</p>';
    return;
  }
  
  // Отображаем последние 10 сессий
  const recentSessions = sleepSessions.slice(0, 10);
  
  recentSessions.forEach(session => {
    const sessionElement = document.createElement('div');
    sessionElement.className = 'glass-card p-4 mb-4';
    
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
    
    sessionElement.innerHTML = `
      <div class="flex justify-between items-center mb-2">
        <span class="font-semibold">${typeLabel}</span>
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
}

// Функция для загрузки статистики сна
function loadSleepStatistics() {
  // Загружаем данные из localStorage и рассчитываем статистику
  const sleepSessions = JSON.parse(localStorage.getItem('sleepSessions') || '[]');
  
  let dayTotal = 0, dayCount = 0;
  let nightTotal = 0, nightCount = 0;
  
  sleepSessions.forEach(session => {
    if (session.duration) {
      const durationMinutes = Math.round(session.duration / 60);
      if (session.type === 'day') {
        dayTotal += durationMinutes;
        dayCount++;
      } else {
        nightTotal += durationMinutes;
        nightCount++;
      }
    }
  });
  
  const avgDaySleep = dayCount > 0 ? Math.round(dayTotal / dayCount) : 0;
  const avgNightSleep = nightCount > 0 ? Math.round(nightTotal / nightCount) : 0;
  
  // Создаем график
  createSleepChart({
    avg_day_sleep: avgDaySleep,
    avg_night_sleep: avgNightSleep
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
  // Проверяем localStorage на наличие активной сессии
  const activeSession = localStorage.getItem('activeSleepSession');
  if (activeSession) {
    const sessionData = JSON.parse(activeSession);
    currentSessionId = sessionData.id;
    startTime = new Date(sessionData.start_time);
    sleepType = sessionData.type;
    
    // Рассчитываем прошедшее время
    elapsedSeconds = Math.floor((Date.now() - startTime.getTime()) / 1000);
    
    // Обновляем UI
    startButton.disabled = true;
    stopButton.disabled = false;
    startTimeElement.textContent = formatDateTime(startTime);
    currentSleepTypeElement.textContent = sleepType === 'day' ? 'Дневной' : 'Ночной';
    
    // Устанавливаем правильную вкладку
    document.querySelectorAll('.neo-tab').forEach(tab => {
      tab.classList.remove('active');
      if ((tab.dataset.tabTarget === 'day-sleep' && sleepType === 'day') || 
          (tab.dataset.tabTarget === 'night-sleep' && sleepType === 'night')) {
        tab.classList.add('active');
      }
    });
    
    // Запускаем таймер
    timerInterval = setInterval(() => {
      elapsedSeconds++;
      timerElement.textContent = formatTime(elapsedSeconds);
    }, 1000);
    
    // Обновляем отображение сразу
    timerElement.textContent = formatTime(elapsedSeconds);
  }
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
  elapsedSeconds = 0;
  
  // Удаляем активную сессию из localStorage
  localStorage.removeItem('activeSleepSession');
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
    type === 'success' ? 'bg-green-100 text-green-800' : 
    type === 'error' ? 'bg-red-100 text-red-800' : 
    'bg-blue-100 text-blue-800'
  }`;
  notification.innerHTML = `
    <div class="flex items-center">
      <span class="mr-2">
        ${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}
      </span>
      <span>${message}</span>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.classList.add('opacity-0');
    notification.style.transition = 'opacity 0.5s ease';
    
    setTimeout(() => {
      if (document.body.contains(notification)) {
        document.body.removeChild(notification);
      }
    }, 500);
  }, 3000);
}