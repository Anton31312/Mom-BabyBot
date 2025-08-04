/**
 * Счетчик шевелений плода
 * 
 * Этот скрипт обеспечивает функциональность счетчика шевелений, включая:
 * - Запуск и остановку сессии подсчета шевелений
 * - Запись отдельных шевелений
 * - Отображение статистики и истории шевелений
 * - Синхронизацию с сервером
 */

// Глобальные переменные
let currentSession = null;
let timerInterval = null;
let elapsedTime = 0;
let kickCount = 0;
let userId = 1; // По умолчанию, в реальном приложении должно быть получено из сессии
let kickChart = null; // Для хранения экземпляра графика

// DOM элементы
const timerDisplay = document.getElementById('timer');
const startButton = document.getElementById('startButton');
const kickButton = document.getElementById('kickButton');
const stopButton = document.getElementById('stopButton');
const kickCountDisplay = document.getElementById('kickCount');
const avgKicksPerHour = document.getElementById('avgKicksPerHour');
const lastKickTime = document.getElementById('lastKickTime');
const kickHistory = document.getElementById('kickHistory');

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Получаем ID пользователя из скрытого поля
    const userIdElement = document.getElementById('userId');
    if (userIdElement) {
        userId = userIdElement.value;
    }
    
    // Настройка обработчиков событий
    startButton.addEventListener('click', startSession);
    kickButton.addEventListener('click', recordKick);
    stopButton.addEventListener('click', stopSession);
    
    // Загрузка истории шевелений
    loadKickHistory();
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
    elapsedTime++;
    timerDisplay.textContent = formatTime(elapsedTime);
    
    // Обновляем среднее количество шевелений в час
    if (elapsedTime > 0) {
        const kicksPerHour = Math.round((kickCount / elapsedTime) * 3600);
        avgKicksPerHour.textContent = kicksPerHour;
    }
}

/**
 * Начинает новую сессию подсчета шевелений
 */
async function startSession() {
    try {
        // Создаем новую сессию на сервере
        const response = await fetch(`/api/users/${userId}/kicks/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error('Не удалось создать сессию шевелений');
        }
        
        currentSession = await response.json();
        
        // Обновляем UI
        startButton.disabled = true;
        kickButton.disabled = false;
        stopButton.disabled = false;
        
        // Сбрасываем счетчики
        elapsedTime = 0;
        kickCount = 0;
        
        // Запускаем таймер
        timerDisplay.textContent = formatTime(elapsedTime);
        timerInterval = setInterval(updateTimer, 1000);
        
        // Обновляем отображение
        kickCountDisplay.textContent = '0';
        avgKicksPerHour.textContent = '0';
        lastKickTime.textContent = '-';
        
        // Показываем уведомление
        showNotification('Сессия подсчета шевелений начата', 'success');
    } catch (error) {
        console.error('Ошибка при начале сессии:', error);
        showNotification('Ошибка при начале сессии', 'error');
    }
}

/**
 * Записывает шевеление
 */
async function recordKick() {
    if (!currentSession) return;
    
    try {
        // Отправляем событие шевеления на сервер
        const response = await fetch(`/api/users/${userId}/kicks/${currentSession.id}/events/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                intensity: 'normal' // По умолчанию нормальная интенсивность
            })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось записать шевеление');
        }
        
        // Увеличиваем счетчик
        kickCount++;
        kickCountDisplay.textContent = kickCount;
        
        // Обновляем время последнего шевеления
        const now = new Date();
        lastKickTime.textContent = now.toLocaleTimeString('ru-RU');
        
        // Добавляем визуальный эффект
        kickButton.classList.add('kick-animation');
        setTimeout(() => {
            kickButton.classList.remove('kick-animation');
        }, 200);
        
        // Обновляем график
        updateKickChart();
        
        // Показываем уведомление
        showNotification(`Шевеление записано (${kickCount})`, 'success');
    } catch (error) {
        console.error('Ошибка при записи шевеления:', error);
        showNotification('Ошибка при записи шевеления', 'error');
    }
}

/**
 * Завершает текущую сессию подсчета шевелений
 */
async function stopSession() {
    if (!currentSession) return;
    
    try {
        // Завершаем сессию на сервере
        const response = await fetch(`/api/users/${userId}/kicks/${currentSession.id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                end_session: true
            })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось завершить сессию шевелений');
        }
        
        // Останавливаем таймер
        clearInterval(timerInterval);
        
        // Обновляем UI
        startButton.disabled = false;
        kickButton.disabled = true;
        stopButton.disabled = true;
        
        // Обновляем историю шевелений
        loadKickHistory();
        
        // Показываем уведомление с результатами
        const sessionDuration = Math.round(elapsedTime / 60);
        showNotification(`Сессия завершена: ${kickCount} шевелений за ${sessionDuration} мин`, 'success');
        
        // Сбрасываем текущую сессию
        currentSession = null;
    } catch (error) {
        console.error('Ошибка при завершении сессии:', error);
        showNotification('Ошибка при завершении сессии', 'error');
    }
}

/**
 * Загружает историю шевелений с сервера
 */
async function loadKickHistory() {
    try {
        // Получаем сессии шевелений с сервера
        const response = await fetch(`/api/users/${userId}/kicks/`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить историю шевелений');
        }
        
        const data = await response.json();
        const sessions = data.kick_sessions || [];
        
        // Очищаем историю
        kickHistory.innerHTML = '';
        
        if (sessions.length === 0) {
            kickHistory.innerHTML = '<p class="text-center text-dark-gray">История шевелений будет отображаться здесь</p>';
            return;
        }
        
        // Инициализируем график с данными последней сессии, если она есть
        if (sessions.length > 0 && sessions[0].events && sessions[0].events.length > 0) {
            initializeKickChart(sessions[0].events);
        }
        
        // Отображаем сессии шевелений
        sessions.forEach(session => {
            // Создаем элемент для сессии
            const sessionItem = document.createElement('div');
            sessionItem.className = 'glass-card mb-6';
            
            // Форматируем дату и время
            const startDate = new Date(session.start_time);
            const formattedDate = startDate.toLocaleDateString('ru-RU');
            const formattedTime = startDate.toLocaleTimeString('ru-RU');
            
            // Рассчитываем продолжительность сессии
            let sessionDuration = '-';
            if (session.end_time) {
                const endTime = new Date(session.end_time);
                const durationMinutes = Math.round((endTime - startDate) / 60000);
                sessionDuration = `${durationMinutes} мин`;
            }
            
            // Рассчитываем среднее количество шевелений в час
            let avgPerHour = '-';
            if (session.end_time && session.count > 0) {
                const endTime = new Date(session.end_time);
                const durationHours = (endTime - startDate) / 3600000;
                avgPerHour = Math.round(session.count / durationHours);
            }
            
            // Создаем HTML для сессии
            let sessionHTML = `
                <div class="p-4">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-bold">${formattedDate}, ${formattedTime}</h3>
                        <div class="neo-badge bg-primary">${session.count} шевелений</div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div>
                            <span class="font-semibold">Продолжительность:</span> ${sessionDuration}
                        </div>
                        <div>
                            <span class="font-semibold">Среднее в час:</span> ${avgPerHour}
                        </div>
                        <div>
                            <span class="font-semibold">Статус:</span> ${session.end_time ? 'Завершена' : 'В процессе'}
                        </div>
                    </div>
            `;
            
            // Добавляем шевеления, если они есть
            if (session.events && session.events.length > 0) {
                sessionHTML += '<div class="mt-4"><h4 class="font-semibold mb-2">Последние шевеления:</h4><div class="grid grid-cols-2 md:grid-cols-4 gap-2">';
                
                // Сортируем события по времени (последние сначала)
                const sortedEvents = [...session.events].sort((a, b) => {
                    return new Date(b.timestamp) - new Date(a.timestamp);
                });
                
                // Добавляем первые 8 шевелений
                const displayEvents = sortedEvents.slice(0, 8);
                displayEvents.forEach(event => {
                    const eventTime = new Date(event.timestamp);
                    const eventTimeString = eventTime.toLocaleTimeString('ru-RU');
                    
                    sessionHTML += `
                        <div class="neo-card p-2 text-center">
                            <div class="text-sm">${eventTimeString}</div>
                            <div class="text-xs text-dark-gray">${event.intensity || 'Обычное'}</div>
                        </div>
                    `;
                });
                
                // Если есть еще шевеления, показываем сообщение
                if (session.events.length > 8) {
                    sessionHTML += `
                        <div class="neo-card p-2 text-center text-dark-gray">
                            <div class="text-sm">+ еще</div>
                            <div class="text-xs">${session.events.length - 8}</div>
                        </div>
                    `;
                }
                
                sessionHTML += '</div></div>';
            }
            
            sessionHTML += '</div>';
            sessionItem.innerHTML = sessionHTML;
            
            // Добавляем сессию в историю
            kickHistory.appendChild(sessionItem);
        });
    } catch (error) {
        console.error('Ошибка при загрузке истории шевелений:', error);
        kickHistory.innerHTML = '<p class="text-center text-dark-gray">Не удалось загрузить историю шевелений</p>';
    }
}

/**
 * Инициализирует график для визуализации шевелений
 * @param {Array} events - Массив событий шевелений
 */
function initializeKickChart(events) {
    // Получаем элемент canvas для графика
    const ctx = document.getElementById('kickChart');
    if (!ctx) return;
    
    // Если график уже существует, уничтожаем его
    if (kickChart) {
        kickChart.destroy();
    }
    
    // Если нет событий, не создаем график
    if (!events || events.length === 0) {
        ctx.style.display = 'none';
        return;
    }
    
    // Группируем шевеления по часам
    const hourlyData = {};
    
    events.forEach(event => {
        const eventTime = new Date(event.timestamp);
        const hour = eventTime.getHours();
        
        if (!hourlyData[hour]) {
            hourlyData[hour] = 0;
        }
        hourlyData[hour]++;
    });
    
    // Подготавливаем данные для графика
    const labels = [];
    const data = [];
    
    for (let hour = 0; hour < 24; hour++) {
        labels.push(`${hour.toString().padStart(2, '0')}:00`);
        data.push(hourlyData[hour] || 0);
    }
    
    // Создаем график
    kickChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Количество шевелений',
                data: data,
                backgroundColor: 'rgba(255, 214, 224, 0.7)',
                borderColor: 'rgba(255, 214, 224, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Количество шевелений'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Время (часы)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Активность шевелений по часам'
                }
            }
        }
    });
    
    ctx.style.display = 'block';
}

/**
 * Обновляет график шевелений с новыми данными
 */
async function updateKickChart() {
    if (!currentSession) return;
    
    try {
        // Получаем обновленные данные сессии
        const response = await fetch(`/api/users/${userId}/kicks/${currentSession.id}/`);
        
        if (!response.ok) {
            throw new Error('Не удалось получить данные сессии');
        }
        
        const sessionData = await response.json();
        
        // Обновляем график
        initializeKickChart(sessionData.events);
    } catch (error) {
        console.error('Ошибка при обновлении графика:', error);
    }
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

// CSS для анимации кнопки шевеления
const style = document.createElement('style');
style.textContent = `
    .kick-animation {
        transform: scale(1.1);
        transition: transform 0.2s ease;
    }
`;
document.head.appendChild(style);