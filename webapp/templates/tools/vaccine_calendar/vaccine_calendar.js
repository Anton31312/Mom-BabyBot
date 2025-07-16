// Глобальные переменные
const userId = document.getElementById('userId')?.value;
let currentChildId = null;
let children = [];
let vaccines = [];
let childVaccines = [];
let filterType = 'all'; // 'all', 'mandatory', 'optional'

// DOM элементы
const childSelector = document.getElementById('childSelector');
const allVaccinesBtn = document.getElementById('allVaccinesBtn');
const mandatoryVaccinesBtn = document.getElementById('mandatoryVaccinesBtn');
const optionalVaccinesBtn = document.getElementById('optionalVaccinesBtn');
const vaccineCalendar = document.getElementById('vaccineCalendar');
const vaccineModal = document.getElementById('vaccineModal');
const closeVaccineModalBtn = document.getElementById('closeVaccineModalBtn');
const vaccineForm = document.getElementById('vaccineForm');
const cancelVaccine = document.getElementById('cancelVaccine');

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем наличие ID пользователя
    if (!userId) {
        showError('Не удалось определить пользователя');
        return;
    }

    // Загружаем список детей
    loadChildren();
    
    // Загружаем список вакцин
    loadVaccines();
    
    // Обработчики для кнопок фильтрации
    allVaccinesBtn.addEventListener('click', () => {
        setActiveFilter('all');
        filterVaccines('all');
    });
    
    mandatoryVaccinesBtn.addEventListener('click', () => {
        setActiveFilter('mandatory');
        filterVaccines('mandatory');
    });
    
    optionalVaccinesBtn.addEventListener('click', () => {
        setActiveFilter('optional');
        filterVaccines('optional');
    });
    
    // Обработчик для выбора ребенка
    childSelector.addEventListener('change', () => {
        currentChildId = childSelector.value;
        if (currentChildId) {
            loadChildVaccines(currentChildId);
        } else {
            resetVaccineStatus();
        }
    });
    
    // Обработчики для модального окна
    closeVaccineModalBtn.addEventListener('click', () => {
        vaccineModal.classList.add('hidden');
    });
    
    cancelVaccine.addEventListener('click', () => {
        vaccineModal.classList.add('hidden');
    });
    
    // Обработчик для формы вакцинации
    vaccineForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const vaccineId = document.getElementById('vaccineId').value;
        const childId = document.getElementById('vaccineChildId').value;
        const date = document.getElementById('vaccineDate').value;
        const notes = document.getElementById('vaccineNotes').value;
        
        try {
            await markVaccineCompleted(childId, vaccineId, date, notes);
            vaccineModal.classList.add('hidden');
            loadChildVaccines(childId);
            showSuccess('Прививка успешно отмечена');
        } catch (error) {
            console.error('Ошибка при отметке прививки:', error);
            showError('Произошла ошибка при отметке прививки');
        }
    });
    
    // Закрытие модального окна при клике вне его области
    window.addEventListener('click', (e) => {
        if (e.target === vaccineModal) {
            vaccineModal.classList.add('hidden');
        }
    });
    
    // Обработчики для кнопок информации о вакцинах
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('vaccine-info-btn')) {
            const vaccineId = e.target.dataset.vaccineId;
            const infoElement = e.target.closest('.glass-card').querySelector('.vaccine-info');
            infoElement.classList.toggle('hidden');
        }
    });
    
    // Обработчики для чекбоксов вакцин
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('vaccine-checkbox')) {
            const vaccineId = e.target.dataset.vaccineId;
            
            if (e.target.checked) {
                openVaccineModal(vaccineId);
            }
        }
    });
});

// Функция для загрузки списка детей
async function loadChildren() {
    try {
        const response = await fetch(`/api/users/${userId}/children/`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить список детей');
        }
        
        const data = await response.json();
        children = data.children || [];
        
        // Очищаем селектор
        childSelector.innerHTML = '<option value="">Выберите ребенка</option>';
        
        if (children.length === 0) {
            childSelector.innerHTML += '<option value="" disabled>У вас пока нет добавленных детей</option>';
            return;
        }
        
        // Заполняем селектор детьми
        children.forEach(child => {
            const option = document.createElement('option');
            option.value = child.id;
            option.textContent = child.name;
            childSelector.appendChild(option);
        });
        
    } catch (error) {
        console.error('Ошибка при загрузке списка детей:', error);
        showError('Не удалось загрузить список детей');
    }
}

// Функция для загрузки списка вакцин
async function loadVaccines() {
    try {
        const response = await fetch('/api/vaccines/');
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить список вакцин');
        }
        
        const data = await response.json();
        vaccines = data.vaccines || [];
        
        // Отображаем вакцины
        renderVaccineCalendar();
        
    } catch (error) {
        console.error('Ошибка при загрузке списка вакцин:', error);
        showError('Не удалось загрузить список вакцин');
    }
}

// Функция для загрузки прививок ребенка
async function loadChildVaccines(childId) {
    try {
        const response = await fetch(`/api/users/${userId}/children/${childId}/vaccines/`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить прививки ребенка');
        }
        
        const data = await response.json();
        childVaccines = data.child_vaccines || [];
        
        // Обновляем статус прививок
        updateVaccineStatus();
        
    } catch (error) {
        console.error('Ошибка при загрузке прививок ребенка:', error);
        showError('Не удалось загрузить прививки ребенка');
    }
}

// Функция для отметки прививки как выполненной
async function markVaccineCompleted(childId, vaccineId, date, notes) {
    // Проверяем, существует ли уже запись о прививке
    const existingVaccine = childVaccines.find(v => v.vaccine_id == vaccineId);
    
    if (existingVaccine) {
        // Обновляем существующую запись
        const response = await fetch(`/api/users/${userId}/children/${childId}/vaccines/${existingVaccine.id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: date,
                is_completed: true,
                notes: notes
            })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось обновить запись о прививке');
        }
        
        return await response.json();
    } else {
        // Создаем новую запись
        const response = await fetch(`/api/users/${userId}/children/${childId}/vaccines/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vaccine_id: vaccineId,
                date: date,
                is_completed: true,
                notes: notes
            })
        });
        
        if (!response.ok) {
            throw new Error('Не удалось создать запись о прививке');
        }
        
        return await response.json();
    }
}

// Функция для отображения календаря прививок
function renderVaccineCalendar() {
    // Группируем вакцины по рекомендуемому возрасту
    const vaccinesByAge = groupVaccinesByAge(vaccines);
    
    // Очищаем календарь
    vaccineCalendar.innerHTML = '';
    
    // Если нет вакцин, показываем сообщение
    if (vaccines.length === 0) {
        vaccineCalendar.innerHTML = '<p class="text-center text-dark-gray">Список вакцин пуст</p>';
        return;
    }
    
    // Отображаем вакцины по возрастным группам
    Object.keys(vaccinesByAge).sort(compareAgeGroups).forEach(ageGroup => {
        const ageVaccines = vaccinesByAge[ageGroup];
        
        const ageGroupElement = document.createElement('div');
        ageGroupElement.className = 'vaccine-age-group';
        
        ageGroupElement.innerHTML = `
            <h2 class="text-xl font-bold mb-4">${ageGroup}</h2>
            <div class="space-y-4 vaccine-list">
                ${ageVaccines.map(vaccine => createVaccineCard(vaccine)).join('')}
            </div>
        `;
        
        vaccineCalendar.appendChild(ageGroupElement);
    });
    
    // Применяем текущий фильтр
    filterVaccines(filterType);
}

// Функция для создания карточки вакцины
function createVaccineCard(vaccine) {
    const mandatoryText = vaccine.is_mandatory ? 'Обязательная' : 'Рекомендуемая';
    
    return `
        <div class="glass-card p-4 vaccine-card ${vaccine.is_mandatory ? 'mandatory' : 'optional'}">
            <div class="flex justify-between items-center">
                <div>
                    <h3 class="text-lg font-semibold">${vaccine.name}</h3>
                    <p class="text-dark-gray">${mandatoryText}</p>
                </div>
                <div class="flex items-center">
                    <span class="mr-2">Сделано:</span>
                    <input type="checkbox" class="vaccine-checkbox" data-vaccine-id="${vaccine.id}">
                </div>
            </div>
            <div class="mt-2">
                <button class="text-primary hover:underline vaccine-info-btn" data-vaccine-id="${vaccine.id}">Подробнее</button>
            </div>
            <div class="vaccine-info hidden mt-4 p-4 bg-light-gray rounded-lg">
                <p class="mb-2">${vaccine.description || 'Описание отсутствует'}</p>
                <p>Рекомендуемый возраст: ${vaccine.recommended_age}</p>
            </div>
        </div>
    `;
}

// Функция для группировки вакцин по возрасту
function groupVaccinesByAge(vaccines) {
    const groups = {};
    
    vaccines.forEach(vaccine => {
        const ageGroup = vaccine.recommended_age;
        
        if (!groups[ageGroup]) {
            groups[ageGroup] = [];
        }
        
        groups[ageGroup].push(vaccine);
    });
    
    return groups;
}

// Функция для сравнения возрастных групп (для сортировки)
function compareAgeGroups(a, b) {
    // Извлекаем числа из строк возраста
    const getAgeInMonths = (ageString) => {
        if (ageString.includes('часа')) return 0;
        if (ageString.includes('день')) return 0;
        
        const months = ageString.match(/(\d+)\s*месяц/);
        if (months) return parseInt(months[1]);
        
        const years = ageString.match(/(\d+)\s*год|(\d+)\s*лет/);
        if (years) return parseInt(years[1] || years[2]) * 12;
        
        return 999; // Если не удалось определить возраст, ставим в конец
    };
    
    return getAgeInMonths(a) - getAgeInMonths(b);
}

// Функция для обновления статуса прививок
function updateVaccineStatus() {
    // Сбрасываем все чекбоксы
    document.querySelectorAll('.vaccine-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Если нет выбранного ребенка или нет прививок, выходим
    if (!currentChildId || childVaccines.length === 0) {
        return;
    }
    
    // Отмечаем сделанные прививки
    childVaccines.forEach(childVaccine => {
        if (childVaccine.is_completed) {
            const checkbox = document.querySelector(`.vaccine-checkbox[data-vaccine-id="${childVaccine.vaccine_id}"]`);
            if (checkbox) {
                checkbox.checked = true;
                checkbox.disabled = true; // Блокируем изменение
                
                // Добавляем информацию о дате прививки
                const vaccineCard = checkbox.closest('.glass-card');
                if (vaccineCard) {
                    const dateInfo = document.createElement('div');
                    dateInfo.className = 'mt-2 text-sm text-dark-gray';
                    dateInfo.textContent = `Сделано: ${formatDate(childVaccine.date)}`;
                    
                    // Добавляем после кнопки "Подробнее"
                    const infoBtn = vaccineCard.querySelector('.vaccine-info-btn');
                    infoBtn.parentNode.insertBefore(dateInfo, infoBtn.nextSibling);
                }
            }
        }
    });
}

// Функция для сброса статуса прививок
function resetVaccineStatus() {
    document.querySelectorAll('.vaccine-checkbox').forEach(checkbox => {
        checkbox.checked = false;
        checkbox.disabled = false;
    });
    
    // Удаляем информацию о датах прививок
    document.querySelectorAll('.vaccine-card .text-sm.text-dark-gray').forEach(element => {
        if (element.textContent.startsWith('Сделано:')) {
            element.remove();
        }
    });
}

// Функция для открытия модального окна отметки прививки
function openVaccineModal(vaccineId) {
    // Находим вакцину
    const vaccine = vaccines.find(v => v.id == vaccineId);
    if (!vaccine) return;
    
    // Находим ребенка
    const child = children.find(c => c.id == currentChildId);
    if (!child) return;
    
    // Заполняем форму
    document.getElementById('vaccineId').value = vaccineId;
    document.getElementById('vaccineChildId').value = currentChildId;
    document.getElementById('vaccineName').textContent = vaccine.name;
    document.getElementById('vaccineChildName').textContent = child.name;
    document.getElementById('vaccineDate').valueAsDate = new Date();
    document.getElementById('vaccineNotes').value = '';
    
    // Показываем модальное окно
    vaccineModal.classList.remove('hidden');
}

// Функция для фильтрации вакцин
function filterVaccines(type) {
    filterType = type;
    
    const vaccineCards = document.querySelectorAll('.vaccine-card');
    
    vaccineCards.forEach(card => {
        if (type === 'all' || 
            (type === 'mandatory' && card.classList.contains('mandatory')) || 
            (type === 'optional' && card.classList.contains('optional'))) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
    
    // Скрываем пустые возрастные группы
    document.querySelectorAll('.vaccine-age-group').forEach(group => {
        const visibleCards = group.querySelectorAll('.vaccine-card[style="display: block"]');
        if (visibleCards.length === 0) {
            group.style.display = 'none';
        } else {
            group.style.display = 'block';
        }
    });
}

// Функция для установки активного фильтра
function setActiveFilter(type) {
    allVaccinesBtn.classList.remove('active');
    mandatoryVaccinesBtn.classList.remove('active');
    optionalVaccinesBtn.classList.remove('active');
    
    if (type === 'all') {
        allVaccinesBtn.classList.add('active');
    } else if (type === 'mandatory') {
        mandatoryVaccinesBtn.classList.add('active');
    } else if (type === 'optional') {
        optionalVaccinesBtn.classList.add('active');
    }
}

// Функция для форматирования даты
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
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