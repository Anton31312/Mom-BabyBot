// Глобальные переменные
const userId = document.getElementById('userId')?.value;
const childId = document.getElementById('childId')?.value;
let feedingHistory = [];
let feedingChart = null;

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
        
        // Обновляем статистику на странице
        todayFeedingCountElement.textContent = data.today_count || 0;
        todayFeedingDurationElement.textContent = `${data.today_duration || 0} мин`;
        todayFeedingAmountElement.textContent = `${data.today_amount || 0} мл`;
        
        weeklyFeedingAvgElement.textContent = data.weekly_avg_count || 0;
        weeklyDurationAvgElement.textContent = `${data.weekly_avg_duration || 0} мин`;
        weeklyAmountAvgElement.textContent = `${data.weekly_avg_amount || 0} мл`;
        
        // Создаем график
        createFeedingChart(data);
        
    } catch (error) {
        console.error('Ошибка при загрузке статистики кормлений:', error);
        document.getElementById('feedingStats').innerHTML = '<p class="text-center text-red-500">Не удалось загрузить статистику кормлений</p>';
    }
}

// Функция для создания графика кормлений
function createFeedingChart(data) {
    // Если нет данных для графика, не создаем его
    if (!data.daily_stats || data.daily_stats.length === 0) {
        return;
    }
    
    // Подготавливаем данные для графика
    const chartContainer = document.getElementById('feedingChart');
    if (!chartContainer) {
        // Создаем контейнер для графика, если его нет
        const container = document.createElement('div');
        container.id = 'feedingChart';
        container.className = 'h-64 bg-white rounded-lg p-4 mt-6';
        container.innerHTML = '<canvas id="feedingChartCanvas"></canvas>';
        document.getElementById('feedingStats').parentNode.appendChild(container);
    }
    
    const ctx = document.getElementById('feedingChartCanvas')?.getContext('2d');
    if (!ctx) return;
    
    // Если график уже существует, уничтожаем его
    if (feedingChart) {
        feedingChart.destroy();
    }
    
    // Подготавливаем данные
    const labels = data.daily_stats.map(day => day.date);
    const breastData = data.daily_stats.map(day => day.breast_duration || 0);
    const bottleData = data.daily_stats.map(day => day.bottle_amount || 0);
    
    // Создаем график
    feedingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Грудное вскармливание (мин)',
                    data: breastData,
                    backgroundColor: 'rgba(255, 214, 224, 0.7)',
                    borderColor: 'rgba(255, 214, 224, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Кормление из бутылочки (мл)',
                    data: bottleData,
                    backgroundColor: 'rgba(201, 240, 225, 0.7)',
                    borderColor: 'rgba(201, 240, 225, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Минуты'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Миллилитры'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
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