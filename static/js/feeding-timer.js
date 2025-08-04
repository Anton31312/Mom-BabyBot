/**
 * Трекер кормления грудью с поддержкой одновременного кормления
 * 
 * Этот скрипт обеспечивает функциональность трекера кормления, включая:
 * - Независимые таймеры для каждой груди
 * - Одновременное кормление с двух грудей
 * - Запись сессий кормления
 * - Отображение статистики и истории кормления
 * - Синхронизацию с сервером
 */

// Глобальные переменные
let currentSession = null;
let leftTimerInterval = null;
let rightTimerInterval = null;
let sessionInterval = null;
let userId = null;
let childId = null;
let feedingChart = null;

// Состояние таймеров
let leftTimer = {
    isRunning: false,
    isPaused: false,
    elapsedTime: 0,
    startTime: null,
    pausedTime: 0
};

let rightTimer = {
    isRunning: false,
    isPaused: false,
    elapsedTime: 0,
    startTime: null,
    pausedTime: 0
};

// DOM элементы
const leftTimerDisplay = document.getElementById('leftTimer');
const rightTimerDisplay = document.getElementById('rightTimer');
const leftStartButton = document.getElementById('leftStartButton');
const leftPauseButton = document.getElementById('leftPauseButton');
const leftStopButton = document.getElementById('leftStopButton');
const rightStartButton = document.getElementById('rightStartButton');
const rightPauseButton = document.getElementById('rightPauseButton');
const rightStopButton = document.getElementById('rightStopButton');
const startBothButton = document.getElementById('startBothButton');
const pauseBothButton = document.getElementById('pauseBothButton');
const stopAllButton = document.getElementById('stopAllButton');
const leftStatus = document.getElementById('leftStatus');
const rightStatus = document.getElementById('rightStatus');
const totalSessionTimeDisplay = document.getElementById('totalSessionTime');
const leftTotalTimeDisplay = document.getElementById('leftTotalTime');
const rightTotalTimeDisplay = document.getElementById('rightTotalTime');
const feedingHistory = document.getElementById('feedingHistory');

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Получаем ID пользователя и ребенка из скрытых полей
    const userIdElement = document.getElementById('userId');
    const childIdElement = document.getElementById('childId');
    
    if (userIdElement) userId = userIdElement.value;
    if (childIdElement) childId = childIdElement.value;
    
    // Настройка обработчиков событий
    if (leftStartButton) leftStartButton.addEventListener('click', () => startTimer('left'));
    if (leftPauseButton) leftPauseButton.addEventListener('click', () => pauseTimer('left'));
    if (leftStopButton) leftStopButton.addEventListener('click', () => stopTimer('left'));
    if (rightStartButton) rightStartButton.addEventListener('click', () => startTimer('right'));
    if (rightPauseButton) rightPauseButton.addEventListener('click', () => pauseTimer('right'));
    if (rightStopButton) rightStopButton.addEventListener('click', () => stopTimer('right'));
    if (startBothButton) startBothButton.addEventListener('click', startBothTimers);
    if (pauseBothButton) pauseBothButton.addEventListener('click', pauseBothTimers);
    if (stopAllButton) stopAllButton.addEventListener('click', stopAllTimers);
    
    // Загрузка истории кормления
    loadFeedingHistory();
    
    // Проверка активной сессии
    checkActiveSession();
    
    // Запуск обновления общего времени сессии
    sessionInterval = setInterval(updateSessionTime, 1000);
});

/**
 * Форматирует время в формат ММ:СС
 * @param {number} seconds - Время в секундах
 * @returns {string} Отформатированное время
 */
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Форматирует дату и время
 * @param {Date|string} date - Дата для форматирования
 * @returns {string} Отформатированная дата и время
 */
function formatDateTime(date) {
    const d = new Date(date);
    return d.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Запускает таймер для указанной груди
 * @param {string} side - 'left' или 'right'
 */
function startTimer(side) {
    const timer = side === 'left' ? leftTimer : rightTimer;
    
    if (timer.isRunning) return;
    
    // Создаем сессию если её нет
    if (!currentSession) {
        currentSession = {
            id: `temp-${Date.now()}`,
            start_time: new Date().toISOString(),
            feeding_type: 'breast',
            left_breast_time: 0,
            right_breast_time: 0
        };
        localStorage.setItem('activeFeedingSession', JSON.stringify(currentSession));
    }
    
    timer.isRunning = true;
    timer.isPaused = false;
    timer.startTime = Date.now() - timer.pausedTime;
    
    // Запускаем интервал для этой груди
    const interval = setInterval(() => updateTimerDisplay(side), 1000);
    if (side === 'left') {
        leftTimerInterval = interval;
    } else {
        rightTimerInterval = interval;
    }
    
    // Обновляем UI
    updateButtonStates(side);
    updateStatus(side, 'Кормление...');
    
    showNotification(`Начато кормление ${side === 'left' ? 'левой' : 'правой'} грудью`, 'success');
}

/**
 * Приостанавливает/возобновляет таймер для указанной груди
 * @param {string} side - 'left' или 'right'
 */
function pauseTimer(side) {
    const timer = side === 'left' ? leftTimer : rightTimer;
    
    if (!timer.isRunning) return;
    
    timer.isPaused = !timer.isPaused;
    
    if (timer.isPaused) {
        timer.pausedTime = timer.elapsedTime;
        updateStatus(side, 'Пауза');
    } else {
        timer.startTime = Date.now() - timer.pausedTime;
        updateStatus(side, 'Кормление...');
    }
    
    updateButtonStates(side);
    showNotification(`${timer.isPaused ? 'Приостановлено' : 'Возобновлено'} кормление ${side === 'left' ? 'левой' : 'правой'} грудью`, 'info');
}

/**
 * Останавливает таймер для указанной груди
 * @param {string} side - 'left' или 'right'
 */
function stopTimer(side) {
    const timer = side === 'left' ? leftTimer : rightTimer;
    const interval = side === 'left' ? leftTimerInterval : rightTimerInterval;
    
    if (!timer.isRunning) return;
    
    // Останавливаем таймер
    clearInterval(interval);
    if (side === 'left') {
        leftTimerInterval = null;
    } else {
        rightTimerInterval = null;
    }
    
    // Сохраняем финальное время
    if (currentSession) {
        if (side === 'left') {
            currentSession.left_breast_time = timer.elapsedTime;
        } else {
            currentSession.right_breast_time = timer.elapsedTime;
        }
        localStorage.setItem('activeFeedingSession', JSON.stringify(currentSession));
    }
    
    // Сбрасываем состояние таймера
    timer.isRunning = false;
    timer.isPaused = false;
    timer.elapsedTime = 0;
    timer.startTime = null;
    timer.pausedTime = 0;
    
    // Обновляем UI
    updateButtonStates(side);
    updateStatus(side, 'Завершено');
    updateTimerDisplay(side);
    
    const minutes = Math.round(timer.elapsedTime / 60);
    showNotification(`Завершено кормление ${side === 'left' ? 'левой' : 'правой'} грудью: ${minutes} мин`, 'success');
    
    // Проверяем, нужно ли завершить всю сессию
    if (!leftTimer.isRunning && !rightTimer.isRunning && currentSession) {
        setTimeout(() => {
            if (confirm('Завершить всю сессию кормления?')) {
                finishSession();
            }
        }, 1000);
    }
}

/**
 * Обновляет отображение таймера для указанной груди
 * @param {string} side - 'left' или 'right'
 */
function updateTimerDisplay(side) {
    const timer = side === 'left' ? leftTimer : rightTimer;
    const display = side === 'left' ? leftTimerDisplay : rightTimerDisplay;
    
    if (!timer.isRunning || timer.isPaused) return;
    
    timer.elapsedTime = Math.floor((Date.now() - timer.startTime) / 1000);
    
    if (display) {
        display.textContent = formatTime(timer.elapsedTime);
    }
    
    // Обновляем общее время
    if (side === 'left') {
        if (leftTotalTimeDisplay) leftTotalTimeDisplay.textContent = formatTime(timer.elapsedTime);
    } else {
        if (rightTotalTimeDisplay) rightTotalTimeDisplay.textContent = formatTime(timer.elapsedTime);
    }
}

/**
 * Обновляет общее время сессии
 */
function updateSessionTime() {
    if (!currentSession) return;
    
    const totalTime = leftTimer.elapsedTime + rightTimer.elapsedTime;
    if (totalSessionTimeDisplay) {
        totalSessionTimeDisplay.textContent = formatTime(totalTime);
    }
}

/**
 * Обновляет состояние кнопок для указанной груди
 * @param {string} side - 'left' или 'right'
 */
function updateButtonStates(side) {
    const timer = side === 'left' ? leftTimer : rightTimer;
    const startBtn = side === 'left' ? leftStartButton : rightStartButton;
    const pauseBtn = side === 'left' ? leftPauseButton : rightPauseButton;
    const stopBtn = side === 'left' ? leftStopButton : rightStopButton;
    
    if (startBtn) startBtn.disabled = timer.isRunning;
    if (pauseBtn) {
        pauseBtn.disabled = !timer.isRunning;
        pauseBtn.textContent = timer.isPaused ? 'Продолжить' : 'Пауза';
    }
    if (stopBtn) stopBtn.disabled = !timer.isRunning;
    
    // Обновляем общие кнопки
    const anyRunning = leftTimer.isRunning || rightTimer.isRunning;
    if (startBothButton) startBothButton.disabled = anyRunning;
    if (pauseBothButton) pauseBothButton.disabled = !anyRunning;
    if (stopAllButton) stopAllButton.disabled = !anyRunning;
}

/**
 * Обновляет статус для указанной груди
 * @param {string} side - 'left' или 'right'
 * @param {string} status - Текст статуса
 */
function updateStatus(side, status) {
    const statusElement = side === 'left' ? leftStatus : rightStatus;
    if (statusElement) {
        statusElement.textContent = status;
    }
}

/**
 * Запускает оба таймера одновременно
 */
function startBothTimers() {
    startTimer('left');
    startTimer('right');
    showNotification('Начато кормление с обеих грудей', 'success');
}

/**
 * Приостанавливает/возобновляет оба таймера
 */
function pauseBothTimers() {
    const leftPaused = leftTimer.isPaused;
    const rightPaused = rightTimer.isPaused;
    
    if (leftTimer.isRunning) pauseTimer('left');
    if (rightTimer.isRunning) pauseTimer('right');
    
    const action = (leftPaused && rightPaused) ? 'возобновлено' : 'приостановлено';
    showNotification(`Кормление ${action} для обеих грудей`, 'info');
}

/**
 * Останавливает все таймеры и завершает сессию
 */
function stopAllTimers() {
    if (leftTimer.isRunning) stopTimer('left');
    if (rightTimer.isRunning) stopTimer('right');
    
    setTimeout(() => {
        finishSession();
    }, 500);
}

/**
 * Завершает всю сессию кормления
 */
function finishSession() {
    if (!currentSession) return;
    
    // Завершаем сессию
    currentSession.end_time = new Date().toISOString();
    currentSession.duration = currentSession.left_breast_time + currentSession.right_breast_time;
    
    // Сохраняем в историю
    const feedingSessions = JSON.parse(localStorage.getItem('feedingSessions') || '[]');
    feedingSessions.unshift(currentSession);
    localStorage.setItem('feedingSessions', JSON.stringify(feedingSessions.slice(0, 50)));
    
    // Удаляем активную сессию
    localStorage.removeItem('activeFeedingSession');
    
    // Останавливаем все интервалы
    if (leftTimerInterval) clearInterval(leftTimerInterval);
    if (rightTimerInterval) clearInterval(rightTimerInterval);
    leftTimerInterval = null;
    rightTimerInterval = null;
    
    // Сбрасываем состояние
    leftTimer = { isRunning: false, isPaused: false, elapsedTime: 0, startTime: null, pausedTime: 0 };
    rightTimer = { isRunning: false, isPaused: false, elapsedTime: 0, startTime: null, pausedTime: 0 };
    
    // Обновляем UI
    updateButtonStates('left');
    updateButtonStates('right');
    updateStatus('left', 'Готов к началу');
    updateStatus('right', 'Готов к началу');
    
    if (leftTimerDisplay) leftTimerDisplay.textContent = '00:00';
    if (rightTimerDisplay) rightTimerDisplay.textContent = '00:00';
    if (leftTotalTimeDisplay) leftTotalTimeDisplay.textContent = '00:00';
    if (rightTotalTimeDisplay) rightTotalTimeDisplay.textContent = '00:00';
    if (totalSessionTimeDisplay) totalSessionTimeDisplay.textContent = '00:00';
    
    // Показываем результаты
    const totalMinutes = Math.round(currentSession.duration / 60);
    const leftMinutes = Math.round(currentSession.left_breast_time / 60);
    const rightMinutes = Math.round(currentSession.right_breast_time / 60);
    
    showNotification(`Сессия завершена: ${totalMinutes} мин (Л: ${leftMinutes}, П: ${rightMinutes})`, 'success');
    
    // Обновляем историю
    loadFeedingHistory();
    
    // Сбрасываем сессию
    currentSession = null;
}

/**
 * Проверяет наличие активной сессии кормления
 */
function checkActiveSession() {
    const activeSession = localStorage.getItem('activeFeedingSession');
    if (activeSession) {
        currentSession = JSON.parse(activeSession);
        
        // Восстанавливаем состояние таймеров
        const sessionStartTime = new Date(currentSession.start_time);
        const now = new Date();
        const totalElapsed = Math.floor((now - sessionStartTime) / 1000);
        
        // Восстанавливаем левый таймер
        if (currentSession.left_breast_time > 0) {
            leftTimer.isRunning = true;
            leftTimer.elapsedTime = currentSession.left_breast_time;
            leftTimer.startTime = now.getTime() - (currentSession.left_breast_time * 1000);
            leftTimerInterval = setInterval(() => updateTimerDisplay('left'), 1000);
            updateStatus('left', 'Кормление...');
        }
        
        // Восстанавливаем правый таймер
        if (currentSession.right_breast_time > 0) {
            rightTimer.isRunning = true;
            rightTimer.elapsedTime = currentSession.right_breast_time;
            rightTimer.startTime = now.getTime() - (currentSession.right_breast_time * 1000);
            rightTimerInterval = setInterval(() => updateTimerDisplay('right'), 1000);
            updateStatus('right', 'Кормление...');
        }
        
        // Обновляем UI
        updateButtonStates('left');
        updateButtonStates('right');
        updateTimerDisplay('left');
        updateTimerDisplay('right');
        
        showNotification('Восстановлена активная сессия кормления', 'info');
    }
}

/**
 * Загружает историю кормления из localStorage
 */
function loadFeedingHistory() {
    // Получаем сессии из localStorage
    const sessions = JSON.parse(localStorage.getItem('feedingSessions') || '[]');
    
    // Очищаем историю
    if (feedingHistory) {
        feedingHistory.innerHTML = '';
        
        if (sessions.length === 0) {
            feedingHistory.innerHTML = '<p class="text-center text-dark-gray">История кормления будет отображаться здесь</p>';
            return;
        }
        
        // Отображаем последние 10 сессий
        const recentSessions = sessions.slice(0, 10);
        
        recentSessions.forEach(session => {
            const sessionElement = document.createElement('div');
            sessionElement.className = 'glass-card p-4 mb-4';
            
            const startTime = formatDateTime(session.start_time);
            const duration = session.duration ? Math.round(session.duration / 60) : 0;
            const feedingType = session.feeding_type === 'breast' ? 'Грудное' : 'Бутылочка';
            
            let breastInfo = '';
            if (session.feeding_type === 'breast') {
                const leftTime = session.left_breast_time ? Math.round(session.left_breast_time / 60) : 0;
                const rightTime = session.right_breast_time ? Math.round(session.right_breast_time / 60) : 0;
                const totalTime = leftTime + rightTime;
                breastInfo = `
                    <div class="mt-2">
                        <div class="grid grid-cols-2 gap-2 text-sm mb-2">
                            <div class="text-center">
                                <div class="font-medium">Левая грудь</div>
                                <div class="text-accent-secondary">${leftTime} мин</div>
                            </div>
                            <div class="text-center">
                                <div class="font-medium">Правая грудь</div>
                                <div class="text-accent-secondary">${rightTime} мин</div>
                            </div>
                        </div>
                        <div class="text-center text-sm border-t pt-2">
                            <span class="font-medium">Общее время: ${totalTime} мин</span>
                        </div>
                    </div>
                `;
            }
            
            sessionElement.innerHTML = `
                <div class="flex justify-between items-center mb-2">
                    <span class="font-semibold">${feedingType}</span>
                    <span class="text-sm text-dark-gray">${startTime}</span>
                </div>
                <div class="text-sm">
                    <span class="text-dark-gray">Продолжительность:</span>
                    <span>${duration} мин</span>
                </div>
                ${breastInfo}
            `;
            
            feedingHistory.appendChild(sessionElement);
        });
    }
    
    // Обновляем график, если есть данные
    if (sessions.length > 0) {
        initializeFeedingChart(sessions);
    }
}

/**
 * Инициализирует график кормления
 * @param {Array} sessions - Массив сессий кормления
 */
function initializeFeedingChart(sessions) {
    const ctx = document.getElementById('feedingChart');
    if (!ctx) return;
    
    // Если график уже существует, уничтожаем его
    if (feedingChart) {
        feedingChart.destroy();
    }
    
    // Подготавливаем данные для графика (последние 7 дней)
    const last7Days = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        last7Days.push(date.toISOString().split('T')[0]);
    }
    
    const dailyData = {};
    last7Days.forEach(date => {
        dailyData[date] = { count: 0, duration: 0 };
    });
    
    // Группируем сессии по дням
    sessions.forEach(session => {
        const sessionDate = new Date(session.start_time).toISOString().split('T')[0];
        if (dailyData[sessionDate]) {
            dailyData[sessionDate].count++;
            dailyData[sessionDate].duration += session.duration || 0;
        }
    });
    
    const labels = last7Days.map(date => {
        const d = new Date(date);
        return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
    });
    
    const countData = last7Days.map(date => dailyData[date].count);
    const durationData = last7Days.map(date => Math.round(dailyData[date].duration / 60));
    
    // Создаем график
    feedingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Количество кормлений',
                    data: countData,
                    backgroundColor: 'rgba(255, 214, 224, 0.7)',
                    borderColor: 'rgba(255, 214, 224, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Общее время (мин)',
                    data: durationData,
                    backgroundColor: 'rgba(226, 214, 255, 0.7)',
                    borderColor: 'rgba(226, 214, 255, 1)',
                    borderWidth: 1,
                    type: 'line',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Количество кормлений'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Время (мин)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Статистика кормления за неделю'
                }
            }
        }
    });
}

/**
 * Получает CSRF токен для Django
 * @returns {string} CSRF токен
 */
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

/**
 * Показывает уведомление пользователю
 * @param {string} message - Текст уведомления
 * @param {string} type - Тип уведомления ('success', 'error', 'info')
 */
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
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
    
    // Добавляем уведомление на страницу
    document.body.appendChild(notification);
    
    // Удаляем уведомление через 3 секунды
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