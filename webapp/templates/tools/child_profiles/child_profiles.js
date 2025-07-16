// Глобальные переменные
let userId = null;
let currentChildId = null;
let children = [];
let measurements = [];
let growthChart = null;

// DOM элементы
const childrenListElement = document.getElementById('childrenList');
const addChildBtn = document.getElementById('addChildBtn');
const addChildModal = document.getElementById('addChildModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const addChildForm = document.getElementById('addChildForm');
const cancelAddChild = document.getElementById('cancelAddChild');
const addMeasurementModal = document.getElementById('addMeasurementModal');
const closeMeasurementModalBtn = document.getElementById('closeMeasurementModalBtn');
const addMeasurementForm = document.getElementById('addMeasurementForm');
const cancelAddMeasurement = document.getElementById('cancelAddMeasurement');
const measurementChildId = document.getElementById('measurementChildId');

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Получаем ID пользователя из localStorage или из URL
    userId = localStorage.getItem('userId') || getUrlParameter('user_id');
    
    if (!userId) {
        // Если ID пользователя не найден, показываем сообщение об ошибке
        childrenListElement.innerHTML = '<p class="text-center text-red-500">Ошибка: ID пользователя не найден</p>';
        addChildBtn.disabled = true;
        return;
    }
    
    // Загружаем список детей
    loadChildren();
    
    // Обработчики событий для модальных окон
    addChildBtn.addEventListener('click', () => {
        addChildModal.classList.remove('hidden');
    });
    
    closeModalBtn.addEventListener('click', () => {
        addChildModal.classList.add('hidden');
    });
    
    cancelAddChild.addEventListener('click', () => {
        addChildModal.classList.add('hidden');
    });
    
    closeMeasurementModalBtn.addEventListener('click', () => {
        addMeasurementModal.classList.add('hidden');
    });
    
    cancelAddMeasurement.addEventListener('click', () => {
        addMeasurementModal.classList.add('hidden');
    });
    
    // Обработчик отправки формы добавления ребенка
    addChildForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('childName').value;
        const birthDate = document.getElementById('childBirthDate').value;
        
        try {
            await createChild(name, birthDate);
            addChildModal.classList.add('hidden');
            addChildForm.reset();
            loadChildren();
        } catch (error) {
            console.error('Ошибка при создании профиля ребенка:', error);
            alert('Произошла ошибка при создании профиля ребенка');
        }
    });
    
    // Обработчик отправки формы добавления измерения
    addMeasurementForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const childId = measurementChildId.value;
        const date = document.getElementById('measurementDate').value;
        const height = document.getElementById('measurementHeight').value;
        const weight = document.getElementById('measurementWeight').value;
        const headCircumference = document.getElementById('measurementHeadCircumference').value;
        
        try {
            await createMeasurement(childId, date, height, weight, headCircumference);
            addMeasurementModal.classList.add('hidden');
            addMeasurementForm.reset();
            
            if (currentChildId === childId) {
                loadChildDetails(childId);
            }
        } catch (error) {
            console.error('Ошибка при создании измерения:', error);
            alert('Произошла ошибка при создании измерения');
        }
    });
    
    // Закрытие модальных окон при клике вне их области
    window.addEventListener('click', (e) => {
        if (e.target === addChildModal) {
            addChildModal.classList.add('hidden');
        }
        if (e.target === addMeasurementModal) {
            addMeasurementModal.classList.add('hidden');
        }
    });
});

// Функция для получения параметра из URL
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Функция для форматирования даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

// Функция для загрузки списка детей
async function loadChildren() {
    try {
        const response = await fetch(`/api/users/${userId}/children/`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить список детей');
        }
        
        const data = await response.json();
        children = data.children || [];
        
        // Очищаем список
        childrenListElement.innerHTML = '';
        
        if (children.length === 0) {
            childrenListElement.innerHTML = '<p class="text-center text-dark-gray">У вас пока нет добавленных детей</p>';
            return;
        }
        
        // Отображаем список детей
        children.forEach(child => {
            const childElement = document.createElement('div');
            childElement.innerHTML = document.getElementById('childProfileTemplate').innerHTML;
            childElement.querySelector('.child-profile').id = `child-${child.id}`;
            childElement.querySelector('.child-name').textContent = child.name;
            childElement.querySelector('.child-age').textContent = child.age_display;
            childElement.querySelector('.child-birth-date').textContent = formatDate(child.birth_date);
            
            // Добавляем обработчики событий для кнопок
            childElement.querySelector('.view-profile-btn').addEventListener('click', () => {
                loadChildDetails(child.id);
            });
            
            childElement.querySelector('.add-measurement-btn').addEventListener('click', () => {
                openAddMeasurementModal(child.id);
            });
            
            childrenListElement.appendChild(childElement.firstElementChild);
        });
    } catch (error) {
        console.error('Ошибка при загрузке списка детей:', error);
        childrenListElement.innerHTML = '<p class="text-center text-red-500">Ошибка при загрузке списка детей</p>';
    }
}

// Функция для создания профиля ребенка
async function createChild(name, birthDate) {
    const response = await fetch(`/api/users/${userId}/children/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name,
            birth_date: birthDate
        })
    });
    
    if (!response.ok) {
        throw new Error('Не удалось создать профиль ребенка');
    }
    
    return await response.json();
}

// Функция для открытия модального окна добавления измерения
function openAddMeasurementModal(childId) {
    measurementChildId.value = childId;
    document.getElementById('measurementDate').valueAsDate = new Date();
    addMeasurementModal.classList.remove('hidden');
}

// Функция для создания измерения
async function createMeasurement(childId, date, height, weight, headCircumference) {
    const response = await fetch(`/api/users/${userId}/children/${childId}/measurements/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            date: date,
            height: parseFloat(height),
            weight: parseFloat(weight),
            head_circumference: headCircumference ? parseFloat(headCircumference) : null
        })
    });
    
    if (!response.ok) {
        throw new Error('Не удалось создать измерение');
    }
    
    return await response.json();
}

// Функция для загрузки деталей ребенка
async function loadChildDetails(childId) {
    try {
        // Сохраняем текущий ID ребенка
        currentChildId = childId;
        
        // Получаем данные ребенка
        const childResponse = await fetch(`/api/users/${userId}/children/${childId}/`);
        
        if (!childResponse.ok) {
            throw new Error('Не удалось загрузить данные ребенка');
        }
        
        const child = await childResponse.json();
        
        // Получаем измерения
        const measurementsResponse = await fetch(`/api/users/${userId}/children/${childId}/measurements/`);
        
        if (!measurementsResponse.ok) {
            throw new Error('Не удалось загрузить измерения');
        }
        
        const measurementsData = await measurementsResponse.json();
        measurements = measurementsData.measurements || [];
        
        // Создаем элемент с деталями ребенка
        const detailElement = document.createElement('div');
        detailElement.innerHTML = document.getElementById('childDetailTemplate').innerHTML;
        
        // Заполняем данные
        detailElement.querySelector('.child-detail-name').textContent = child.name;
        detailElement.querySelector('.child-detail-age').textContent = child.age_display;
        detailElement.querySelector('.child-detail-birth-date').textContent = formatDate(child.birth_date);
        
        // Добавляем обработчик для кнопки добавления измерения
        detailElement.querySelector('.add-measurement-btn').addEventListener('click', () => {
            openAddMeasurementModal(childId);
        });
        
        // Отображаем измерения
        const measurementsList = detailElement.querySelector('.measurements-list');
        
        if (measurements.length === 0) {
            measurementsList.innerHTML = '<p class="text-center text-dark-gray">Измерения отсутствуют</p>';
        } else {
            measurementsList.innerHTML = '';
            
            // Сортируем измерения по дате (новые сверху)
            measurements.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            measurements.forEach(measurement => {
                const measurementElement = document.createElement('div');
                measurementElement.className = 'glass-card p-4';
                
                measurementElement.innerHTML = `
                    <div class="flex justify-between items-center mb-2">
                        <span class="font-semibold">Измерение от ${formatDate(measurement.date)}</span>
                    </div>
                    <div class="grid grid-cols-3 gap-2 text-sm">
                        <div>
                            <span class="text-dark-gray">Рост:</span>
                            <span>${measurement.height} см</span>
                        </div>
                        <div>
                            <span class="text-dark-gray">Вес:</span>
                            <span>${measurement.weight} кг</span>
                        </div>
                        <div>
                            <span class="text-dark-gray">Окружность головы:</span>
                            <span>${measurement.head_circumference || '-'} см</span>
                        </div>
                    </div>
                `;
                
                measurementsList.appendChild(measurementElement);
            });
        }
        
        // Создаем график роста
        createGrowthChart(detailElement.querySelector('.growth-chart'), measurements);
        
        // Обновляем вехи развития в зависимости от возраста
        updateMilestones(detailElement.querySelector('.milestones-list'), child.age_in_months);
        
        // Заменяем содержимое страницы
        const mainContent = document.querySelector('main');
        mainContent.innerHTML = '';
        
        // Добавляем кнопку "Назад к списку"
        const backButton = document.createElement('button');
        backButton.className = 'neo-button mb-6';
        backButton.innerHTML = `
            <svg class="w-4 h-4 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            Назад к списку
        `;
        backButton.addEventListener('click', () => {
            location.reload();
        });
        
        mainContent.appendChild(backButton);
        
        // Добавляем детали ребенка
        while (detailElement.firstChild) {
            mainContent.appendChild(detailElement.firstChild);
        }
        
    } catch (error) {
        console.error('Ошибка при загрузке деталей ребенка:', error);
        alert('Произошла ошибка при загрузке деталей ребенка');
    }
}

// Функция для создания графика роста
function createGrowthChart(container, measurements) {
    // Если нет измерений, показываем сообщение
    if (measurements.length === 0) {
        container.innerHTML = '<p class="text-center text-dark-gray">Недостаточно данных для построения графика</p>';
        return;
    }
    
    // Если меньше двух измерений, показываем сообщение
    if (measurements.length < 2) {
        container.innerHTML = '<p class="text-center text-dark-gray">Для построения графика необходимо минимум два измерения</p>';
        return;
    }
    
    // Подготавливаем данные для графика
    const sortedMeasurements = [...measurements].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    const labels = sortedMeasurements.map(m => formatDate(m.date));
    const heightData = sortedMeasurements.map(m => m.height);
    const weightData = sortedMeasurements.map(m => m.weight);
    const headData = sortedMeasurements.filter(m => m.head_circumference).map(m => m.head_circumference);
    
    // Создаем canvas для графика
    container.innerHTML = '<canvas id="growthChartCanvas"></canvas>';
    const ctx = document.getElementById('growthChartCanvas').getContext('2d');
    
    // Создаем график
    growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Рост (см)',
                    data: heightData,
                    borderColor: 'rgba(255, 214, 224, 1)',
                    backgroundColor: 'rgba(255, 214, 224, 0.2)',
                    borderWidth: 2,
                    tension: 0.3,
                    yAxisID: 'y'
                },
                {
                    label: 'Вес (кг)',
                    data: weightData,
                    borderColor: 'rgba(201, 240, 225, 1)',
                    backgroundColor: 'rgba(201, 240, 225, 0.2)',
                    borderWidth: 2,
                    tension: 0.3,
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
                        text: 'Рост (см)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Вес (кг)'
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
    
    // Если есть данные по окружности головы, добавляем их на график
    if (headData.length > 0) {
        growthChart.data.datasets.push({
            label: 'Окружность головы (см)',
            data: headData,
            borderColor: 'rgba(226, 214, 255, 1)',
            backgroundColor: 'rgba(226, 214, 255, 0.2)',
            borderWidth: 2,
            tension: 0.3,
            yAxisID: 'y'
        });
        
        growthChart.update();
    }
}

// Функция для обновления вех развития в зависимости от возраста
function updateMilestones(container, ageInMonths) {
    // Если возраст не определен, показываем все вехи
    if (!ageInMonths) {
        return;
    }
    
    // Получаем все блоки вех развития
    const milestoneBlocks = container.querySelectorAll('.glass-card');
    
    // Определяем, какие блоки показывать в зависимости от возраста
    milestoneBlocks.forEach((block, index) => {
        const title = block.querySelector('h3').textContent;
        
        if (title === '0-3 месяца' && ageInMonths > 3) {
            // Если ребенку больше 3 месяцев, помечаем блок как пройденный
            block.classList.add('opacity-70');
            block.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
                checkbox.checked = true;
                checkbox.disabled = true;
            });
        } else if (title === '4-6 месяцев' && ageInMonths > 6) {
            // Если ребенку больше 6 месяцев, помечаем блок как пройденный
            block.classList.add('opacity-70');
            block.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
                checkbox.checked = true;
                checkbox.disabled = true;
            });
        } else if (title === '4-6 месяцев' && ageInMonths < 4) {
            // Если ребенку меньше 4 месяцев, делаем блок неактивным
            block.classList.add('opacity-50');
            block.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
                checkbox.disabled = true;
            });
        }
    });
    
    // Добавляем обработчики для чекбоксов
    container.querySelectorAll('input[type="checkbox"]:not([disabled])').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            // Здесь можно добавить логику сохранения состояния чекбоксов
            // Например, отправку на сервер или сохранение в localStorage
            localStorage.setItem(`milestone-${currentChildId}-${checkbox.parentElement.textContent.trim()}`, checkbox.checked);
        });
        
        // Восстанавливаем состояние чекбоксов из localStorage
        const savedState = localStorage.getItem(`milestone-${currentChildId}-${checkbox.parentElement.textContent.trim()}`);
        if (savedState === 'true') {
            checkbox.checked = true;
        }
    });
}