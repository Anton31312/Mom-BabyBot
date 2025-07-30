// Глобальные переменные
const userId = document.getElementById('userId')?.value;
const childId = document.getElementById('childId')?.value;
let feedingHistory = [];
let feedingChart = null;

// Timer variables
let currentSession = null;
let leftTimerInterval = null;
let rightTimerInterval = null;
let leftStartTime = null;
let rightStartTime = null;
let leftAccumulatedTime = 0;
let rightAccumulatedTime = 0;
let sessionStartTime = null;

// DOM элементы
const breastFeedingForm = document.getElementById('breastFeedingForm');
const bottleFeedingForm = document.getElementById('bottleFeedingForm');
const feedingHistoryElement = document.getElementById('feedingHistory');
const todayFeedingCountElement = document.getElementById('todayFeedingCount');
const todayFeedingDurationElement = document.getElementById('todayFeedingDuration');
const todayFeedingAmountElement = document.getElementById('todayFeedingAmount');
const weeklyFeedingAvgElement = document.getElementById('weeklyFeedingAvg');
const weeklyDurationAvgElement = document.getElementById('weeklyDurationAvg');
const weeklyAmountAvgElement = document.getElementById('weeklyAmountAvg');

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем наличие ID пользователя и ребенка
    if (!userId || !childId) {
        showError('Не удалось определить пользователя или ребенка');
        return;
    }

    // Загружаем историю кормлений
    loadFeedingHistory();
    
    // Загружаем статистику кормлений
    loadFeedingStatistics();
    
    // Обработчики для вкладок
    document.querySelectorAll('.glass-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabGroup = tab.closest('[data-tab-group]').dataset.tabGroup;
            const targetId = tab.dataset.tabTarget;
            
            // Удаляем активный класс у всех вкладок этой группы
            document.querySelectorAll(`[data-tab-group="${tabGroup}"] .glass-tab`).forEach(t => {
                t.classList.remove('active');
            });
            
            // Добавляем активный класс текущей вкладке
            tab.classList.add('active');
            
            // Скрываем все контенты этой группы
            document.querySelectorAll(`[data-tab-group="${tabGroup}"].tab-content`).forEach(content => {
                content.style.display = 'none';
            });
            
            // Показываем нужный контент
            document.getElementById(targetId).style.display = 'block';
        });
    });
    
    // Обработчик для формы грудного вскармливания
    breastFeedingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const date = document.getElementById('breastFeedingDate').value;
        const duration = document.getElementById('breastFeedingDuration').value;
        const breast = document.querySelector('input[name="breast"]:checked').value;
        const notes = document.getElementById('breastFeedingNotes').value;
        
        try {
            await createFeedingSession({
                timestamp: date,
                type: 'breast',
                duration: parseInt(duration),
                breast: breast,
                notes: notes
            });
            
            // Очищаем форму
            document.getElementById('breastFeedingNotes').value = '';
            
            // Обновляем историю и статистику
            loadFeedingHistory();
            loadFeedingStatistics();
            
            showSuccess('Запись о грудном вскармливании успешно сохранена');
        } catch (error) {
            console.error('Ошибка при сохранении записи о грудном вскармливании:', error);
            showError('Произошла ошибка при сохранении записи о грудном вскармливании');
        }
    });
    
    // Обработчик для формы кормления из бутылочки
    bottleFeedingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const date = document.getElementById('bottleFeedingDate').value;
        const amount = document.getElementById('bottleFeedingAmount').value;
        const milkType = document.querySelector('input[name="milkType"]:checked').value;
        const notes = document.getElementById('bottleFeedingNotes').value;
        
        try {
            await createFeedingSession({
                timestamp: date,
                type: 'bottle',
                amount: parseFloat(amount),
                milk_type: milkType,
                notes: notes
            });
            
            // Очищаем форму
            document.getElementById('bottleFeedingNotes').value = '';
            
            // Обновляем историю и статистику
            loadFeedingHistory();
            loadFeedingStatistics();
            
            showSuccess('Запись о кормлении из бутылочки успешно сохранена');
        } catch (error) {
            console.error('Ошибка при сохранении записи о кормлении из бутылочки:', error);
            showError('Произошла ошибка при сохранении записи о кормлении из бутылочки');
        }
    });
    
    // Устанавливаем текущую дату и время в поля даты
    const now = new Date();
    const dateTimeString = now.toISOString().slice(0, 16);
    document.getElementById('breastFeedingDate').value = dateTimeString;
    document.getElementById('bottleFeedingDate').value = dateTimeString;
    
    // Инициализируем таймеры
    initializeTimers();
    
    // Проверяем активную сессию при загрузке
    checkActiveSession();
});

// Функция для создания сессии кормления
async function createFeedingSession(data) {
    const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    if (!response.ok) {
        throw new Error('Не удалось создать запись о кормлении');
    }
    
    return await response.json();
}

// Функция для загрузки истории кормлений
async function loadFeedingHistory() {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить историю кормлений');
        }
        
        const data = await response.json();
        feedingHistory = data.feeding_sessions || [];
        
        // Очищаем историю
        feedingHistoryElement.innerHTML = '';
        
        if (feedingHistory.length === 0) {
            feedingHistoryElement.innerHTML = '<p class="text-center text-dark-gray">История кормлений пуста</p>';
            return;
        }
        
        // Сортируем сессии по дате (новые сверху)
        feedingHistory.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // Отображаем последние 10 сессий
        const recentSessions = feedingHistory.slice(0, 10);
        
        recentSessions.forEach(session => {
            const sessionElement = document.createElement('div');
            sessionElement.className = 'glass-card p-4 mb-4';
            
            const typeLabel = session.type === 'breast' ? 'Грудное вскармливание' : 'Кормление из бутылочки';
            const timestamp = formatDateTime(session.timestamp);
            
            let details = '';
            if (session.type === 'breast') {
                const breastLabel = {
                    'left': 'Левая грудь',
                    'right': 'Правая грудь',
                    'both': 'Обе груди'
                }[session.breast] || session.breast;
                
                details = `
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                            <span class="text-dark-gray">Грудь:</span>
                            <span>${breastLabel}</span>
                        </div>
                        <div>
                            <span class="text-dark-gray">Продолжительность:</span>
                            <span>${session.duration} мин</span>
                        </div>
                    </div>
                `;
            } else {
                const milkTypeLabel = session.milk_type === 'formula' ? 'Смесь' : 'Сцеженное молоко';
                
                details = `
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div>
                            <span class="text-dark-gray">Тип молока:</span>
                            <span>${milkTypeLabel}</span>
                        </div>
                        <div>
                            <span class="text-dark-gray">Количество:</span>
                            <span>${session.amount} мл</span>
                        </div>
                    </div>
                `;
            }
            
            const notes = session.notes ? `
                <div class="mt-2 text-sm">
                    <span class="text-dark-gray">Заметки:</span>
                    <span>${session.notes}</span>
                </div>
            ` : '';
            
            sessionElement.innerHTML = `
                <div class="flex justify-between items-center mb-2">
                    <span class="font-semibold">${typeLabel}</span>
                    <span class="text-sm text-dark-gray">${timestamp}</span>
                </div>
                ${details}
                ${notes}
            `;
            
            feedingHistoryElement.appendChild(sessionElement);
        });
        
    } catch (error) {
        console.error('Ошибка при загрузке истории кормлений:', error);
        feedingHistoryElement.innerHTML = '<p class="text-center text-red-500">Не удалось загрузить историю кормлений</p>';
    }
}

// Функция для загрузки статистики кормлений
async function loadFeedingStatistics() {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/statistics/`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить статистику кормлений');
        }
        
        const data = await response.json();
        
        // Обновляем общую статистику за сегодня
        updateElementText('todayFeedingCount', data.today_count || 0);
        updateElementText('todayBreastCount', data.today_breast_count || 0);
        updateElementText('todayBottleCount', data.today_bottle_count || 0);
        updateElementText('todayFeedingDuration', `${data.today_duration || 0} мин`);
        updateElementText('todayFeedingAmount', `${data.today_amount || 0} мл`);
        
        // Обновляем средние значения за неделю
        updateElementText('weeklyFeedingAvg', data.weekly_avg_count || 0);
        updateElementText('weeklyDurationAvg', `${data.weekly_avg_duration || 0} мин`);
        updateElementText('weeklyAmountAvg', `${data.weekly_avg_amount || 0} мл`);
        updateElementText('weeklyAvgSessionDuration', `${data.weekly_avg_session_duration || 0} мин`);
        
        // Обновляем рекорды недели
        updateElementText('weeklyLongestSession', `${data.weekly_longest_session || 0} мин`);
        updateElementText('weeklyShortestSession', `${data.weekly_shortest_session || 0} мин`);
        updateElementText('weeklyTotalCount', data.weekly_total_count || 0);
        
        // Обновляем детальную статистику по грудям за сегодня
        updateElementText('todayLeftBreastDuration', `${data.today_left_breast_duration || 0} мин`);
        updateElementText('todayLeftBreastPercentage', `${data.today_left_breast_percentage || 0}%`);
        updateElementText('todayRightBreastDuration', `${data.today_right_breast_duration || 0} мин`);
        updateElementText('todayRightBreastPercentage', `${data.today_right_breast_percentage || 0}%`);
        
        // Обновляем прогресс-бары за сегодня
        updateProgressBar('todayLeftBreastBar', data.today_left_breast_percentage || 0);
        updateProgressBar('todayRightBreastBar', data.today_right_breast_percentage || 0);
        
        // Обновляем детальную статистику по грудям за неделю
        updateElementText('weeklyLeftBreastDuration', `${data.weekly_left_breast_duration || 0} мин`);
        updateElementText('weeklyLeftBreastPercentage', `${data.weekly_left_breast_percentage || 0}%`);
        updateElementText('weeklyRightBreastDuration', `${data.weekly_right_breast_duration || 0} мин`);
        updateElementText('weeklyRightBreastPercentage', `${data.weekly_right_breast_percentage || 0}%`);
        
        // Обновляем прогресс-бары за неделю
        updateProgressBar('weeklyLeftBreastBar', data.weekly_left_breast_percentage || 0);
        updateProgressBar('weeklyRightBreastBar', data.weekly_right_breast_percentage || 0);
        
        // Обновляем средние значения по грудям
        updateElementText('weeklyAvgLeftBreastDuration', `${data.weekly_avg_left_breast_duration || 0} мин`);
        updateElementText('weeklyAvgRightBreastDuration', `${data.weekly_avg_right_breast_duration || 0} мин`);
        
        // Создаем график
        createFeedingChart(data);
        
    } catch (error) {
        console.error('Ошибка при загрузке статистики кормлений:', error);
        document.getElementById('feedingStats').innerHTML = '<p class="text-center text-red-500">Не удалось загрузить статистику кормлений</p>';
    }
}

// Вспомогательная функция для обновления текста элемента
function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

// Вспомогательная функция для обновления прогресс-бара
function updateProgressBar(elementId, percentage) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.width = `${Math.min(percentage, 100)}%`;
    }
}

// Функция для создания графика кормлений
function createFeedingChart(data) {
    // Если нет данных для графика, не создаем его
    if (!data.daily_stats || data.daily_stats.length === 0) {
        const chartContainer = document.getElementById('feedingChart');
        if (chartContainer) {
            chartContainer.innerHTML = '<p class="text-center text-gray-500 py-8">Нет данных для отображения графика</p>';
        }
        return;
    }
    
    const ctx = document.getElementById('feedingChartCanvas')?.getContext('2d');
    if (!ctx) return;
    
    // Если график уже существует, уничтожаем его
    if (feedingChart) {
        feedingChart.destroy();
    }
    
    // Подготавливаем данные для расширенного графика
    const labels = data.daily_stats.map(day => day.date);
    const leftBreastData = data.daily_stats.map(day => Math.round((day.left_breast_duration || 0) * 10) / 10);
    const rightBreastData = data.daily_stats.map(day => Math.round((day.right_breast_duration || 0) * 10) / 10);
    const bottleData = data.daily_stats.map(day => day.bottle_amount || 0);
    
    // Создаем расширенный график с детализацией по грудям
    feedingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Левая грудь (мин)',
                    data: leftBreastData,
                    backgroundColor: 'rgba(236, 72, 153, 0.7)', // Pink color for left breast
                    borderColor: 'rgba(236, 72, 153, 1)',
                    borderWidth: 1,
                    yAxisID: 'y',
                    stack: 'breast'
                },
                {
                    label: 'Правая грудь (мин)',
                    data: rightBreastData,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)', // Blue color for right breast
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1,
                    yAxisID: 'y',
                    stack: 'breast'
                },
                {
                    label: 'Кормление из бутылочки (мл)',
                    data: bottleData,
                    backgroundColor: 'rgba(34, 197, 94, 0.7)', // Green color for bottle
                    borderColor: 'rgba(34, 197, 94, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1',
                    stack: 'bottle'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Дата'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Минуты'
                    },
                    beginAtZero: true
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Миллилитры'
                    },
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Статистика кормлений по дням'
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: function(context) {
                            return `Дата: ${context[0].label}`;
                        },
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            
                            if (label.includes('мин')) {
                                return `${label}: ${value} мин`;
                            } else if (label.includes('мл')) {
                                return `${label}: ${value} мл`;
                            }
                            return `${label}: ${value}`;
                        },
                        afterBody: function(context) {
                            // Добавляем общую информацию
                            const dataIndex = context[0].dataIndex;
                            const dayData = data.daily_stats[dataIndex];
                            
                            const totalBreastTime = (dayData.left_breast_duration || 0) + (dayData.right_breast_duration || 0);
                            const totalFeedings = dayData.count || 0;
                            
                            return [
                                '',
                                `Всего кормлений: ${totalFeedings}`,
                                `Общее время ГВ: ${Math.round(totalBreastTime * 10) / 10} мин`
                            ];
                        }
                    }
                }
            }
        }
    });
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

// Функция для отображения сообщения об успехе
function showSuccess(message) {
    const alertElement = document.createElement('div');
    alertElement.className = 'fixed bottom-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded';
    alertElement.role = 'alert';
    alertElement.innerHTML = message;
    
    document.body.appendChild(alertElement);
    
    setTimeout(() => {
        alertElement.remove();
    }, 3000);
}

// Функция для отображения сообщения об ошибке
function showError(message) {
    const alertElement = document.createElement('div');
    alertElement.className = 'fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded';
    alertElement.role = 'alert';
    alertElement.innerHTML = message;
    
    document.body.appendChild(alertElement);
    
    setTimeout(() => {
        alertElement.remove();
    }, 3000);
}
// ===== TIMER FUNCTIONALITY =====

// Initialize timer interfaceы
function initializeTimers() {
    // Get timer DOM elements
    const leftStartBtn = document.getElementById('leftStartBtn');
    const leftPauseBtn = document.getElementById('leftPauseBtn');
    const rightStartBtn = document.getElementById('rightStartBtn');
    const rightPauseBtn = document.getElementById('rightPauseBtn');
    const switchToLeftBtn = document.getElementById('switchToLeftBtn');
    const switchToRightBtn = document.getElementById('switchToRightBtn');
    const stopSessionBtn = document.getElementById('stopSessionBtn');

    // Event listeners for left breast timer
    leftStartBtn?.addEventListener('click', () => startTimer('left'));
    leftPauseBtn?.addEventListener('click', () => pauseTimer('left'));

    // Event listeners for right breast timer
    rightStartBtn?.addEventListener('click', () => startTimer('right'));
    rightPauseBtn?.addEventListener('click', () => pauseTimer('right'));

    // Event listeners for switch buttons
    switchToLeftBtn?.addEventListener('click', () => switchBreast('left'));
    switchToRightBtn?.addEventListener('click', () => switchBreast('right'));

    // Event listener for stop session button
    stopSessionBtn?.addEventListener('click', stopSession);

    // Initialize timer displays
    updateTimerDisplay('left', 0);
    updateTimerDisplay('right', 0);
}

// Check for active feeding session on page load
async function checkActiveSession() {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/active/`);
        
        if (!response.ok) {
            return; // No active session
        }
        
        const data = await response.json();
        
        if (data.has_active_session && data.session_data) {
            currentSession = data.session_data;
            restoreActiveSession(data.session_data);
        }
    } catch (error) {
        console.error('Ошибка при проверке активной сессии:', error);
    }
}

// Restore active session state
function restoreActiveSession(sessionData) {
    // Set accumulated times
    leftAccumulatedTime = sessionData.left_breast_duration || 0;
    rightAccumulatedTime = sessionData.right_breast_duration || 0;
    
    // Update displays
    updateTimerDisplay('left', leftAccumulatedTime);
    updateTimerDisplay('right', rightAccumulatedTime);
    updateTotalTime();
    
    // Show active session info
    showActiveSessionInfo(sessionData);
    
    // Restore active timers
    if (sessionData.left_timer_active) {
        leftStartTime = new Date(sessionData.left_timer_start);
        startTimerInterval('left');
        updateTimerButtons('left', true);
        updateTimerState('left', 'active');
    }
    
    if (sessionData.right_timer_active) {
        rightStartTime = new Date(sessionData.right_timer_start);
        startTimerInterval('right');
        updateTimerButtons('right', true);
        updateTimerState('right', 'active');
    }
    
    // Show session controls
    showSessionControls();
    updateSwitchButtons();
}

// Start timer for specified breast
async function startTimer(breast) {
    try {
        // If no current session, create one
        if (!currentSession) {
            const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/timer/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ breast: breast })
            });
            
            if (!response.ok) {
                throw new Error('Не удалось запустить таймер');
            }
            
            const data = await response.json();
            currentSession = data.session_data;
            sessionStartTime = new Date();
            showActiveSessionInfo(currentSession);
        } else {
            // Start timer for existing session
            const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/timer/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    breast: breast,
                    session_id: currentSession.id 
                })
            });
            
            if (!response.ok) {
                throw new Error('Не удалось запустить таймер');
            }
            
            const data = await response.json();
            currentSession = data.session_data;
        }
        
        // Start local timer
        if (breast === 'left') {
            leftStartTime = new Date();
            startTimerInterval('left');
        } else {
            rightStartTime = new Date();
            startTimerInterval('right');
        }
        
        // Update UI
        updateTimerButtons(breast, true);
        updateTimerState(breast, 'active');
        showSessionControls();
        updateSwitchButtons();
        
        showSuccess(`Таймер для ${breast === 'left' ? 'левой' : 'правой'} груди запущен`);
        
    } catch (error) {
        console.error('Ошибка при запуске таймера:', error);
        showError('Произошла ошибка при запуске таймера');
    }
}

// Pause timer for specified breast
async function pauseTimer(breast) {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/${currentSession.id}/timer/pause/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ breast: breast })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось приостановить таймер');
        }
        
        const data = await response.json();
        currentSession = data.session_data;
        
        // Stop local timer
        if (breast === 'left') {
            clearInterval(leftTimerInterval);
            leftTimerInterval = null;
            leftAccumulatedTime = currentSession.left_breast_duration || 0;
        } else {
            clearInterval(rightTimerInterval);
            rightTimerInterval = null;
            rightAccumulatedTime = currentSession.right_breast_duration || 0;
        }
        
        // Update UI
        updateTimerButtons(breast, false);
        updateTimerState(breast, 'paused');
        updateTimerDisplay(breast, breast === 'left' ? leftAccumulatedTime : rightAccumulatedTime);
        updateTotalTime();
        updateSwitchButtons();
        
        showSuccess(`Таймер для ${breast === 'left' ? 'левой' : 'правой'} груди приостановлен`);
        
    } catch (error) {
        console.error('Ошибка при приостановке таймера:', error);
        showError('Произошла ошибка при приостановке таймера');
    }
}

// Switch between breasts
async function switchBreast(toBreast) {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/${currentSession.id}/timer/switch/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ to_breast: toBreast })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось переключить грудь');
        }
        
        const data = await response.json();
        currentSession = data.session_data;
        
        // Update local timers
        const fromBreast = toBreast === 'left' ? 'right' : 'left';
        
        // Stop the current timer
        if (fromBreast === 'left') {
            clearInterval(leftTimerInterval);
            leftTimerInterval = null;
            leftAccumulatedTime = currentSession.left_breast_duration || 0;
        } else {
            clearInterval(rightTimerInterval);
            rightTimerInterval = null;
            rightAccumulatedTime = currentSession.right_breast_duration || 0;
        }
        
        // Start the new timer
        if (toBreast === 'left') {
            leftStartTime = new Date();
            startTimerInterval('left');
        } else {
            rightStartTime = new Date();
            startTimerInterval('right');
        }
        
        // Update UI
        updateTimerButtons(fromBreast, false);
        updateTimerButtons(toBreast, true);
        updateTimerState(fromBreast, 'paused');
        updateTimerState(toBreast, 'active');
        updateTimerDisplay(fromBreast, fromBreast === 'left' ? leftAccumulatedTime : rightAccumulatedTime);
        updateSwitchButtons();
        
        showSuccess(`Переключение на ${toBreast === 'left' ? 'левую' : 'правую'} грудь`);
        
    } catch (error) {
        console.error('Ошибка при переключении груди:', error);
        showError('Произошла ошибка при переключении груди');
    }
}

// Stop feeding session
async function stopSession() {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/feeding/${currentSession.id}/timer/stop/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Не удалось завершить сессию');
        }
        
        const data = await response.json();
        
        // Clear all timers
        clearInterval(leftTimerInterval);
        clearInterval(rightTimerInterval);
        leftTimerInterval = null;
        rightTimerInterval = null;
        
        // Reset state
        currentSession = null;
        leftAccumulatedTime = 0;
        rightAccumulatedTime = 0;
        sessionStartTime = null;
        
        // Update UI
        resetTimerInterface();
        hideActiveSessionInfo();
        hideSessionControls();
        
        // Refresh history and statistics
        loadFeedingHistory();
        loadFeedingStatistics();
        
        showSuccess('Сессия кормления завершена');
        
    } catch (error) {
        console.error('Ошибка при завершении сессии:', error);
        showError('Произошла ошибка при завершении сессии');
    }
}

// Start timer interval for specified breast
function startTimerInterval(breast) {
    const interval = setInterval(() => {
        const startTime = breast === 'left' ? leftStartTime : rightStartTime;
        const accumulated = breast === 'left' ? leftAccumulatedTime : rightAccumulatedTime;
        const elapsed = Math.floor((new Date() - startTime) / 1000);
        const total = accumulated + elapsed;
        
        updateTimerDisplay(breast, total);
        updateTotalTime();
    }, 1000);
    
    if (breast === 'left') {
        leftTimerInterval = interval;
    } else {
        rightTimerInterval = interval;
    }
}

// Update timer display
function updateTimerDisplay(breast, seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    const timeString = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    
    const timerElement = document.getElementById(`${breast}Timer`);
    const totalElement = document.getElementById(`${breast}TotalTime`);
    
    if (timerElement) {
        timerElement.textContent = timeString;
    }
    
    if (totalElement) {
        const totalMinutes = Math.floor(seconds / 60);
        const totalRemainingSeconds = seconds % 60;
        totalElement.textContent = `${totalMinutes.toString().padStart(2, '0')}:${totalRemainingSeconds.toString().padStart(2, '0')}`;
    }
}

// Update total session time
function updateTotalTime() {
    const totalElement = document.getElementById('totalSessionTime');
    if (!totalElement || !currentSession) return;
    
    let totalSeconds = leftAccumulatedTime + rightAccumulatedTime;
    
    // Add current running timer time
    if (leftTimerInterval && leftStartTime) {
        totalSeconds += Math.floor((new Date() - leftStartTime) / 1000);
    }
    if (rightTimerInterval && rightStartTime) {
        totalSeconds += Math.floor((new Date() - rightStartTime) / 1000);
    }
    
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    totalElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Update timer buttons
function updateTimerButtons(breast, isActive) {
    const startBtn = document.getElementById(`${breast}StartBtn`);
    const pauseBtn = document.getElementById(`${breast}PauseBtn`);
    
    if (isActive) {
        startBtn.style.display = 'none';
        pauseBtn.style.display = 'block';
    } else {
        startBtn.style.display = 'block';
        pauseBtn.style.display = 'none';
    }
}

// Update timer visual state
function updateTimerState(breast, state) {
    const container = document.querySelector(`#${breast === 'left' ? 'leftTimer' : 'rightTimer'}`).closest('.timer-container');
    
    // Remove all state classes
    container.classList.remove('active', 'paused', 'inactive');
    
    // Add current state class
    container.classList.add(state);
}

// Show active session info
function showActiveSessionInfo(sessionData) {
    const infoElement = document.getElementById('activeSessionInfo');
    const startTimeElement = document.getElementById('sessionStartTime');
    
    if (infoElement && startTimeElement) {
        infoElement.style.display = 'block';
        startTimeElement.textContent = formatDateTime(sessionData.timestamp);
    }
}

// Hide active session info
function hideActiveSessionInfo() {
    const infoElement = document.getElementById('activeSessionInfo');
    if (infoElement) {
        infoElement.style.display = 'none';
    }
}

// Show session controls
function showSessionControls() {
    const stopBtn = document.getElementById('stopSessionBtn');
    if (stopBtn) {
        stopBtn.style.display = 'block';
    }
}

// Hide session controls
function hideSessionControls() {
    const stopBtn = document.getElementById('stopSessionBtn');
    const switchLeftBtn = document.getElementById('switchToLeftBtn');
    const switchRightBtn = document.getElementById('switchToRightBtn');
    
    if (stopBtn) stopBtn.style.display = 'none';
    if (switchLeftBtn) switchLeftBtn.style.display = 'none';
    if (switchRightBtn) switchRightBtn.style.display = 'none';
}

// Update switch buttons visibility
function updateSwitchButtons() {
    const switchLeftBtn = document.getElementById('switchToLeftBtn');
    const switchRightBtn = document.getElementById('switchToRightBtn');
    
    if (!currentSession) {
        if (switchLeftBtn) switchLeftBtn.style.display = 'none';
        if (switchRightBtn) switchRightBtn.style.display = 'none';
        return;
    }
    
    const leftActive = currentSession.left_timer_active;
    const rightActive = currentSession.right_timer_active;
    
    // Show switch to left if right is active
    if (switchLeftBtn) {
        switchLeftBtn.style.display = rightActive ? 'inline-block' : 'none';
    }
    
    // Show switch to right if left is active
    if (switchRightBtn) {
        switchRightBtn.style.display = leftActive ? 'inline-block' : 'none';
    }
}

// Reset timer interface
function resetTimerInterface() {
    // Reset displays
    updateTimerDisplay('left', 0);
    updateTimerDisplay('right', 0);
    
    // Reset buttons
    updateTimerButtons('left', false);
    updateTimerButtons('right', false);
    
    // Reset states
    updateTimerState('left', 'inactive');
    updateTimerState('right', 'inactive');
    
    // Clear total time
    const totalElement = document.getElementById('totalSessionTime');
    if (totalElement) {
        totalElement.textContent = '00:00';
    }
}

// Format time for display
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}