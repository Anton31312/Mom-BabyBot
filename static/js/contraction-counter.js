/**
 * Счетчик схваток
 * 
 * Этот скрипт обеспечивает функциональность счетчика схваток, включая:
 * - Запуск и остановку сессии схваток
 * - Запись отдельных схваток
 * - Отображение статистики и истории схваток
 * - Синхронизацию с сервером
 */

// Глобальные переменные
let currentSession = null;
let timerInterval = null;
let elapsedTime = 0;
let contractionStartTime = null;
let contractionActive = false;
let userId = 1; // По умолчанию, в реальном приложении должно быть получено из сессии
let contractionChart = null; // Для хранения экземпляра графика

// DOM элементы
const timerDisplay = document.getElementById('timer');
const startButton = document.getElementById('startButton');
const contractionButton = document.getElementById('contractionButton');
const stopButton = document.getElementById('stopButton');
const contractionCount = document.getElementById('contractionCount');
const avgDuration = document.getElementById('avgDuration');
const avgInterval = document.getElementById('avgInterval');
const contractionHistory = document.getElementById('contractionHistory');
const contractionStats = document.getElementById('contractionStats');

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Настройка обработчиков событий
    startButton.addEventListener('click', startSession);
    contractionButton.addEventListener('click', toggleContraction);
    stopButton.addEventListener('click', stopSession);
    
    // Загрузка истории схваток
    loadContractionHistory();
});

/**
 * Форматирует время в формат ЧЧ:ММ:СС
 * @param {number} seconds - Время в секундах
 * @returns {string} Отформатированное время
 */
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

/**
 * Форматирует продолжительность в минутах и секундах
 * @param {number} seconds - Продолжительность в секундах
 * @returns {string} Отформатированная продолжительность
 */
function formatDuration(seconds) {
    if (!seconds) return '-';
    
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    
    if (minutes > 0) {
        return `${minutes} мин ${secs} сек`;
    } else {
        return `${secs} сек`;
    }
}

/**
 * Обновляет отображение таймера
 */
function updateTimer() {
    elapsedTime++;
    timerDisplay.textContent = formatTime(elapsedTime);
}

/**
 * Начинает новую сессию схваток
 */
async function startSession() {
    try {
        // Создаем новую сессию на сервере
        const response = await fetch(`/api/users/${userId}/contractions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error('Не удалось создать сессию схваток');
        }
        
        currentSession = await response.json();
        
        // Обновляем UI
        startButton.disabled = true;
        contractionButton.disabled = false;
        stopButton.disabled = false;
        
        // Запускаем таймер
        elapsedTime = 0;
        timerDisplay.textContent = formatTime(elapsedTime);
        timerInterval = setInterval(updateTimer, 1000);
        
        // Очищаем статистику
        contractionCount.textContent = '0';
        avgDuration.textContent = '-';
        avgInterval.textContent = '-';
        
        // Показываем уведомление
        showNotification('Сессия схваток начата', 'success');
    } catch (error) {
        console.error('Ошибка при начале сессии:', error);
        showNotification('Ошибка при начале сессии', 'error');
    }
}

/**
 * Переключает состояние схватки (начало/конец)
 */
async function toggleContraction() {
    if (!currentSession) return;
    
    if (!contractionActive) {
        // Начало схватки
        contractionStartTime = new Date();
        contractionActive = true;
        contractionButton.textContent = 'Завершить схватку';
        contractionButton.classList.add('active');
    } else {
        // Конец схватки
        const endTime = new Date();
        const durationSeconds = Math.round((endTime - contractionStartTime) / 1000);
        
        try {
            // Отправляем событие схватки на сервер
            const response = await fetch(`/api/users/${userId}/contractions/${currentSession.id}/events/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    duration: durationSeconds
                })
            });
            
            if (!response.ok) {
                throw new Error('Не удалось сохранить схватку');
            }
            
            // Обновляем UI
            contractionActive = false;
            contractionButton.textContent = 'Схватка';
            contractionButton.classList.remove('active');
            
            // Обновляем статистику
            updateStatistics();
            
            // Обновляем график
            updateContractionChart();
            
            // Добавляем схватку в историю текущей сессии
            addContractionToHistory(contractionStartTime, durationSeconds);
        } catch (error) {
            console.error('Ошибка при записи схватки:', error);
            showNotification('Ошибка при записи схватки', 'error');
        }
    }
}

/**
 * Завершает текущую сессию схваток
 */
async function stopSession() {
    if (!currentSession) return;
    
    try {
        // Если схватка активна, завершаем ее
        if (contractionActive) {
            await toggleContraction();
        }
        
        // Завершаем сессию на сервере
        const response = await fetch(`/api/users/${userId}/contractions/${currentSession.id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                end_session: true
            })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось завершить сессию схваток');
        }
        
        // Останавливаем таймер
        clearInterval(timerInterval);
        
        // Обновляем UI
        startButton.disabled = false;
        contractionButton.disabled = true;
        stopButton.disabled = true;
        
        // Обновляем историю схваток
        loadContractionHistory();
        
        // Показываем уведомление
        showNotification('Сессия схваток завершена', 'success');
        
        // Сбрасываем текущую сессию
        currentSession = null;
    } catch (error) {
        console.error('Ошибка при завершении сессии:', error);
        showNotification('Ошибка при завершении сессии', 'error');
    }
}

/**
 * Обновляет статистику текущей сессии
 */
async function updateStatistics() {
    try {
        // Получаем обновленные данные сессии
        const response = await fetch(`/api/users/${userId}/contractions/${currentSession.id}/`);
        
        if (!response.ok) {
            throw new Error('Не удалось получить данные сессии');
        }
        
        const sessionData = await response.json();
        
        // Обновляем счетчик схваток
        contractionCount.textContent = sessionData.count;
        
        // Обновляем среднюю продолжительность
        let totalDuration = 0;
        let validEvents = 0;
        
        sessionData.events.forEach(event => {
            if (event.duration) {
                totalDuration += event.duration;
                validEvents++;
            }
        });
        
        if (validEvents > 0) {
            const averageDuration = Math.round(totalDuration / validEvents);
            avgDuration.textContent = formatDuration(averageDuration);
        }
        
        // Обновляем средний интервал
        if (sessionData.average_interval) {
            avgInterval.textContent = formatDuration(Math.round(sessionData.average_interval * 60));
        }
    } catch (error) {
        console.error('Ошибка при обновлении статистики:', error);
    }
}

/**
 * Добавляет схватку в историю текущей сессии
 * @param {Date} startTime - Время начала схватки
 * @param {number} durationSeconds - Продолжительность схватки в секундах
 */
function addContractionToHistory(startTime, durationSeconds) {
    // Создаем элемент для схватки
    const contractionItem = document.createElement('div');
    contractionItem.className = 'neo-card p-4 mb-4';
    
    const timeString = startTime.toLocaleTimeString();
    const durationString = formatDuration(durationSeconds);
    
    contractionItem.innerHTML = `
        <div class="flex justify-between items-center">
            <div>
                <span class="font-semibold">Время:</span> ${timeString}
            </div>
            <div>
                <span class="font-semibold">Продолжительность:</span> ${durationString}
            </div>
        </div>
    `;
    
    // Если это первая схватка, очищаем сообщение "История схваток будет отображаться здесь"
    if (contractionHistory.querySelector('p')) {
        contractionHistory.innerHTML = '';
    }
    
    // Добавляем схватку в начало истории
    contractionHistory.insertBefore(contractionItem, contractionHistory.firstChild);
}

/**
 * Загружает историю схваток с сервера
 */
async function loadContractionHistory() {
    try {
        // Получаем сессии схваток с сервера
        const response = await fetch(`/api/users/${userId}/contractions/`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить историю схваток');
        }
        
        const data = await response.json();
        const sessions = data.contractions;
        
        // Очищаем историю
        contractionHistory.innerHTML = '';
        
        if (sessions.length === 0) {
            contractionHistory.innerHTML = '<p class="text-center text-dark-gray">История схваток будет отображаться здесь</p>';
            // Очищаем график, так как нет данных
            const ctx = document.getElementById('contractionChart');
            if (contractionChart) {
                contractionChart.destroy();
                contractionChart = null;
            }
            ctx.style.display = 'none';
            return;
        }
        
        // Инициализируем график с данными последней сессии, если она есть
        if (sessions.length > 0 && sessions[0].events && sessions[0].events.length > 0) {
            initializeContractionChart(sessions[0].events);
        }
        
        // Отображаем сессии схваток
        sessions.forEach(session => {
            // Создаем элемент для сессии
            const sessionItem = document.createElement('div');
            sessionItem.className = 'glass-card mb-6';
            
            // Форматируем дату и время
            const startDate = new Date(session.start_time);
            const formattedDate = startDate.toLocaleDateString();
            const formattedTime = startDate.toLocaleTimeString();
            
            // Рассчитываем продолжительность сессии
            let sessionDuration = '-';
            if (session.end_time) {
                const endTime = new Date(session.end_time);
                const durationMinutes = Math.round((endTime - startDate) / 60000);
                sessionDuration = `${durationMinutes} мин`;
            }
            
            // Создаем HTML для сессии
            let sessionHTML = `
                <div class="p-4">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-bold">${formattedDate}, ${formattedTime}</h3>
                        <div class="neo-badge bg-primary">${session.count} схваток</div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div>
                            <span class="font-semibold">Продолжительность:</span> ${sessionDuration}
                        </div>
                        <div>
                            <span class="font-semibold">Средний интервал:</span> ${session.average_interval ? formatDuration(Math.round(session.average_interval * 60)) : '-'}
                        </div>
                        <div>
                            <span class="font-semibold">Средняя продолжительность:</span> ${calculateAverageDuration(session.events)}
                        </div>
                    </div>
            `;
            
            // Добавляем схватки, если они есть
            if (session.events && session.events.length > 0) {
                sessionHTML += '<div class="mt-4"><h4 class="font-semibold mb-2">Схватки:</h4><div class="space-y-2">';
                
                // Сортируем события по времени
                const sortedEvents = [...session.events].sort((a, b) => {
                    return new Date(a.timestamp) - new Date(b.timestamp);
                });
                
                // Добавляем первые 5 схваток
                const displayEvents = sortedEvents.slice(0, 5);
                displayEvents.forEach(event => {
                    const eventTime = new Date(event.timestamp);
                    const eventTimeString = eventTime.toLocaleTimeString();
                    const eventDuration = event.duration ? formatDuration(event.duration) : '-';
                    
                    sessionHTML += `
                        <div class="neo-card p-2">
                            <div class="flex justify-between items-center">
                                <div>${eventTimeString}</div>
                                <div>Продолжительность: ${eventDuration}</div>
                            </div>
                        </div>
                    `;
                });
                
                // Если есть еще схватки, показываем сообщение
                if (session.events.length > 5) {
                    sessionHTML += `
                        <div class="text-center text-dark-gray mt-2">
                            + еще ${session.events.length - 5} схваток
                        </div>
                    `;
                }
                
                sessionHTML += '</div></div>';
            }
            
            sessionHTML += '</div>';
            sessionItem.innerHTML = sessionHTML;
            
            // Добавляем сессию в историю
            contractionHistory.appendChild(sessionItem);
        });
    } catch (error) {
        console.error('Ошибка при загрузке истории схваток:', error);
        contractionHistory.innerHTML = '<p class="text-center text-dark-gray">Не удалось загрузить историю схваток</p>';
    }
}

/**
 * Рассчитывает среднюю продолжительность схваток
 * @param {Array} events - Массив событий схваток
 * @returns {string} Отформатированная средняя продолжительность
 */
function calculateAverageDuration(events) {
    if (!events || events.length === 0) return '-';
    
    let totalDuration = 0;
    let validEvents = 0;
    
    events.forEach(event => {
        if (event.duration) {
            totalDuration += event.duration;
            validEvents++;
        }
    });
    
    if (validEvents === 0) return '-';
    
    const averageDuration = Math.round(totalDuration / validEvents);
    return formatDuration(averageDuration);
}

/**
 * Показывает уведомление пользователю
 * @param {string} message - Текст уведомления
 * @param {string} type - Тип уведомления ('success', 'error', 'info')
 */
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'success' ? 'bg-secondary' : type === 'error' ? 'bg-red-200' : 'bg-primary'}`;
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
            document.body.removeChild(notification);
        }, 500);
    }, 3000);
}
/**
 * Инициализирует график для визуализации схваток
 * @param {Array} events - Массив событий схваток
 */
function initializeContractionChart(events) {
    // Получаем элемент canvas для графика
    const ctx = document.getElementById('contractionChart');
    
    // Если график уже существует, уничтожаем его
    if (contractionChart) {
        contractionChart.destroy();
    }
    
    // Если нет событий, не создаем график
    if (!events || events.length < 2) {
        ctx.style.display = 'none';
        return;
    }
    
    // Сортируем события по времени
    const sortedEvents = [...events].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
    });
    
    // Подготавливаем данные для графика
    const labels = [];
    const durations = [];
    const intervals = [];
    
    sortedEvents.forEach((event, index) => {
        const eventTime = new Date(event.timestamp);
        labels.push(eventTime.toLocaleTimeString());
        
        // Добавляем продолжительность схватки
        durations.push(event.duration || 0);
        
        // Рассчитываем интервал между схватками
        if (index > 0) {
            const prevTime = new Date(sortedEvents[index - 1].timestamp);
            const intervalMinutes = (eventTime - prevTime) / 60000; // в минутах
            intervals.push(intervalMinutes);
        } else {
            intervals.push(0);
        }
    });
    
    // Создаем график
    contractionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Продолжительность (сек)',
                    data: durations,
                    backgroundColor: 'rgba(255, 214, 224, 0.7)',
                    borderColor: 'rgba(255, 214, 224, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Интервал (мин)',
                    data: intervals,
                    backgroundColor: 'rgba(226, 214, 255, 0.7)',
                    borderColor: 'rgba(226, 214, 255, 1)',
                    borderWidth: 1,
                    type: 'line'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Продолжительность (сек) / Интервал (мин)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Время'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw;
                            
                            if (label.includes('Продолжительность')) {
                                return `${label}: ${formatDuration(value)}`;
                            } else if (label.includes('Интервал')) {
                                return `${label}: ${value.toFixed(1)} мин`;
                            }
                            
                            return `${label}: ${value}`;
                        }
                    }
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Динамика схваток'
                }
            }
        }
    });
    
    ctx.style.display = 'block';
}

/**
 * Обновляет график схваток с новыми данными
 */
async function updateContractionChart() {
    if (!currentSession) return;
    
    try {
        // Получаем обновленные данные сессии
        const response = await fetch(`/api/users/${userId}/contractions/${currentSession.id}/`);
        
        if (!response.ok) {
            throw new Error('Не удалось получить данные сессии');
        }
        
        const sessionData = await response.json();
        
        // Обновляем график
        initializeContractionChart(sessionData.events);
    } catch (error) {
        console.error('Ошибка при обновлении графика:', error);
    }
}