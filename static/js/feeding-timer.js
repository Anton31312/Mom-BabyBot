/**
 * Трекер кормления грудью
 * 
 * Этот скрипт обеспечивает функциональность трекера кормления, включая:
 * - Запуск и остановку таймера кормления
 * - Переключение между грудями
 * - Запись сессий кормления
 * - Отображение статистики и истории кормления
 * - Синхронизацию с сервером
 */

// Глобальные переменные
let currentSession = null;
let timerInterval = null;
let elapsedTime = 0;
let currentBreast = 'left'; // 'left' или 'right'
let isTimerRunning = false;
let isPaused = false;
let userId = null;
let childId = null;
let feedingChart = null;

// DOM элементы
const timerDisplay = document.getElementById('timer');
const startButton = document.getElementById('startButton');
const pauseButton = document.getElementById('pauseButton');
const stopButton = document.getElementById('stopButton');
const switchButton = document.getElementById('switchButton');
const leftBreastButton = document.getElementById('leftBreastButton');
const rightBreastButton = document.getElementById('rightBreastButton');
const currentBreastDisplay = document.getElementById('currentBreast');
const sessionTimeDisplay = document.getElementById('sessionTime');
const leftTimeDisplay = document.getElementById('leftTime');
const rightTimeDisplay = document.getElementById('rightTime');
const feedingHistory = document.getElementById('feedingHistory');

// Время для каждой груди
let leftBreastTime = 0;
let rightBreastTime = 0;

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Получаем ID пользователя и ребенка из скрытых полей
    const userIdElement = document.getElementById('userId');
    const childIdElement = document.getElementById('childId');
    
    if (userIdElement) userId = userIdElement.value;
    if (childIdElement) childId = childIdElement.value;
    
    if (!userId || !childId) {
        console.error('Не удалось получить ID пользователя или ребенка');
        return;
    }
    
    // Настройка обработчиков событий
    if (startButton) startButton.addEventListener('click', startFeeding);
    if (pauseButton) pauseButton.addEventListener('click', pauseFeeding);
    if (stopButton) stopButton.addEventListener('click', stopFeeding);
    if (switchButton) switchButton.addEventListener('click', switchBreast);
    if (leftBreastButton) leftBreastButton.addEventListener('click', () => selectBreast('left'));
    if (rightBreastButton) rightBreastButton.addEventListener('click', () => selectBreast('right'));
    
    // Загрузка истории кормления
    loadFeedingHistory();
    
    // Проверка активной сессии
    checkActiveSession();
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
 * Обновляет отображение таймера
 */
function updateTimer() {
    if (!isTimerRunning || isPaused) return;
    
    elapsedTime++;
    
    // Увеличиваем время для текущей груди
    if (currentBreast === 'left') {
        leftBreastTime++;
    } else {
        rightBreastTime++;
    }
    
    // Обновляем отображение
    updateDisplay();
}

/**
 * Обновляет отображение времени
 */
function updateDisplay() {
    if (timerDisplay) timerDisplay.textContent = formatTime(elapsedTime);
    if (sessionTimeDisplay) sessionTimeDisplay.textContent = formatTime(elapsedTime);
    if (leftTimeDisplay) leftTimeDisplay.textContent = formatTime(leftBreastTime);
    if (rightTimeDisplay) rightTimeDisplay.textContent = formatTime(rightBreastTime);
    if (currentBreastDisplay) {
        currentBreastDisplay.textContent = currentBreast === 'left' ? 'Левая грудь' : 'Правая грудь';
    }
}

/**
 * Выбирает грудь для кормления
 * @param {string} breast - 'left' или 'right'
 */
function selectBreast(breast) {
    currentBreast = breast;
    
    // Обновляем активную кнопку
    if (leftBreastButton && rightBreastButton) {
        leftBreastButton.classList.toggle('active', breast === 'left');
        rightBreastButton.classList.toggle('active', breast === 'right');
    }
    
    updateDisplay();
}

/**
 * Начинает сессию кормления
 */
async function startFeeding() {
    try {
        // Создаем новую сессию на сервере
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/timer/start/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                feeding_type: 'breast',
                breast_side: currentBreast
            })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось начать сессию кормления');
        }
        
        currentSession = await response.json();
        
        // Обновляем состояние
        isTimerRunning = true;
        isPaused = false;
        elapsedTime = 0;
        leftBreastTime = 0;
        rightBreastTime = 0;
        
        // Обновляем UI
        if (startButton) startButton.disabled = true;
        if (pauseButton) pauseButton.disabled = false;
        if (stopButton) stopButton.disabled = false;
        if (switchButton) switchButton.disabled = false;
        
        // Запускаем таймер
        timerInterval = setInterval(updateTimer, 1000);
        
        // Обновляем отображение
        updateDisplay();
        
        // Показываем уведомление
        showNotification('Кормление начато', 'success');
    } catch (error) {
        console.error('Ошибка при начале кормления:', error);
        showNotification('Ошибка при начале кормления', 'error');
    }
}

/**
 * Приостанавливает/возобновляет кормление
 */
async function pauseFeeding() {
    if (!currentSession) return;
    
    try {
        const action = isPaused ? 'resume' : 'pause';
        
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/${currentSession.id}/timer/pause/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ action })
        });
        
        if (!response.ok) {
            throw new Error(`Не удалось ${action === 'pause' ? 'приостановить' : 'возобновить'} кормление`);
        }
        
        // Переключаем состояние паузы
        isPaused = !isPaused;
        
        // Обновляем кнопку
        if (pauseButton) {
            pauseButton.textContent = isPaused ? 'Продолжить' : 'Пауза';
        }
        
        // Показываем уведомление
        showNotification(isPaused ? 'Кормление приостановлено' : 'Кормление возобновлено', 'info');
    } catch (error) {
        console.error('Ошибка при паузе кормления:', error);
        showNotification('Ошибка при изменении состояния кормления', 'error');
    }
}

/**
 * Переключает грудь во время кормления
 */
async function switchBreast() {
    if (!currentSession || !isTimerRunning) return;
    
    try {
        const newBreast = currentBreast === 'left' ? 'right' : 'left';
        
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/${currentSession.id}/timer/switch/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                new_breast: newBreast
            })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось переключить грудь');
        }
        
        // Переключаем грудь
        selectBreast(newBreast);
        
        // Показываем уведомление
        showNotification(`Переключено на ${newBreast === 'left' ? 'левую' : 'правую'} грудь`, 'info');
    } catch (error) {
        console.error('Ошибка при переключении груди:', error);
        showNotification('Ошибка при переключении груди', 'error');
    }
}

/**
 * Завершает сессию кормления
 */
async function stopFeeding() {
    if (!currentSession) return;
    
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/${currentSession.id}/timer/stop/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                left_breast_time: leftBreastTime,
                right_breast_time: rightBreastTime,
                total_time: elapsedTime
            })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось завершить сессию кормления');
        }
        
        // Останавливаем таймер
        clearInterval(timerInterval);
        isTimerRunning = false;
        isPaused = false;
        
        // Обновляем UI
        if (startButton) startButton.disabled = false;
        if (pauseButton) {
            pauseButton.disabled = true;
            pauseButton.textContent = 'Пауза';
        }
        if (stopButton) stopButton.disabled = true;
        if (switchButton) switchButton.disabled = true;
        
        // Показываем результаты
        const totalMinutes = Math.round(elapsedTime / 60);
        showNotification(`Кормление завершено: ${totalMinutes} мин`, 'success');
        
        // Обновляем историю
        loadFeedingHistory();
        
        // Сбрасываем сессию
        currentSession = null;
        elapsedTime = 0;
        leftBreastTime = 0;
        rightBreastTime = 0;
        updateDisplay();
    } catch (error) {
        console.error('Ошибка при завершении кормления:', error);
        showNotification('Ошибка при завершении кормления', 'error');
    }
}

/**
 * Проверяет наличие активной сессии кормления
 */
async function checkActiveSession() {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/active/`);
        
        if (!response.ok) {
            return; // Нет активной сессии
        }
        
        const activeSession = await response.json();
        
        if (activeSession && activeSession.id) {
            // Восстанавливаем активную сессию
            currentSession = activeSession;
            isTimerRunning = true;
            
            // Рассчитываем прошедшее время
            const startTime = new Date(activeSession.start_time);
            const now = new Date();
            elapsedTime = Math.floor((now - startTime) / 1000);
            
            // Восстанавливаем время для каждой груди (если доступно)
            leftBreastTime = activeSession.left_breast_time || 0;
            rightBreastTime = activeSession.right_breast_time || 0;
            
            // Устанавливаем текущую грудь
            if (activeSession.current_breast) {
                selectBreast(activeSession.current_breast);
            }
            
            // Обновляем UI
            if (startButton) startButton.disabled = true;
            if (pauseButton) pauseButton.disabled = false;
            if (stopButton) stopButton.disabled = false;
            if (switchButton) switchButton.disabled = false;
            
            // Запускаем таймер
            timerInterval = setInterval(updateTimer, 1000);
            
            // Обновляем отображение
            updateDisplay();
            
            showNotification('Восстановлена активная сессия кормления', 'info');
        }
    } catch (error) {
        console.error('Ошибка при проверке активной сессии:', error);
    }
}

/**
 * Загружает историю кормления с сервера
 */
async function loadFeedingHistory() {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить историю кормления');
        }
        
        const data = await response.json();
        const sessions = data.feeding_sessions || [];
        
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
                    breastInfo = `
                        <div class="grid grid-cols-2 gap-2 mt-2 text-sm">
                            <div>Левая грудь: ${leftTime} мин</div>
                            <div>Правая грудь: ${rightTime} мин</div>
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
    } catch (error) {
        console.error('Ошибка при загрузке истории кормления:', error);
        if (feedingHistory) {
            feedingHistory.innerHTML = '<p class="text-center text-dark-gray">Не удалось загрузить историю кормления</p>';
        }
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