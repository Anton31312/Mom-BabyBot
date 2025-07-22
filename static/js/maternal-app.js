/**
 * Основной JavaScript для приложения Mom&BabyBot
 * Включает интеграцию с Telegram ботом для отправки уведомлений
 */

// Инициализация Telegram Web App
document.addEventListener('DOMContentLoaded', function () {
  // Инициализация Telegram WebApp
  const tg = window.Telegram.WebApp;
  tg.expand();

  // Установка темы на основе цветовой схемы Telegram
  if (tg.colorScheme === 'dark') {
    document.body.classList.add('dark-theme');
  }

  // Инициализация навигации
  initNavigation();

  // Инициализация компонентов
  initComponents();

  // Инициализация индикатора активных таймеров
  initActiveTimersIndicator();
  
  // Инициализация индикатора онлайн/офлайн статуса
  initOnlineStatusIndicator();
});

// Функциональность навигации
function initNavigation() {
  const navToggle = document.getElementById('nav-toggle');
  const mobileNav = document.getElementById('mobile-nav');

  if (navToggle && mobileNav) {
    navToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      mobileNav.classList.toggle('hidden');

      // Добавление класса анимации
      if (!mobileNav.classList.contains('hidden')) {
        setTimeout(() => {
          mobileNav.classList.add('fade-in');
        }, 10);
      } else {
        mobileNav.classList.remove('fade-in');
      }
    });

    // Закрытие мобильной навигации при клике вне её области
    document.addEventListener('click', function (e) {
      if (!mobileNav.classList.contains('hidden') &&
        !mobileNav.contains(e.target) &&
        e.target !== navToggle &&
        !navToggle.contains(e.target)) {
        mobileNav.classList.add('hidden');
        mobileNav.classList.remove('fade-in');
      }
    });
  }

  // Обработка переключения профиля ребенка
  const profileSwitcher = document.getElementById('profile-switcher');
  if (profileSwitcher) {
    profileSwitcher.addEventListener('change', function () {
      const selectedProfileId = this.value;
      // Обновление интерфейса на основе выбранного профиля
      updateUIForProfile(selectedProfileId);
    });
  }

  // Добавление активного класса для текущей страницы
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('nav a');

  navLinks.forEach(link => {
    const linkPath = link.getAttribute('href');
    if (linkPath && currentPath.includes(linkPath) && linkPath !== '/') {
      link.classList.add('font-semibold', 'text-black');
    } else if (linkPath === '/' && currentPath === '/') {
      link.classList.add('font-semibold', 'text-black');
    }
  });
}

// Инициализация компонентов интерфейса
function initComponents() {
  // Инициализация вкладок
  const tabGroups = document.querySelectorAll('[data-tab-group]');
  tabGroups.forEach(group => {
    if (group.classList.contains('neo-tabs')) {
      // Неоморфные вкладки обрабатываются в neomorphism.js
    } else if (group.classList.contains('glass-tabs')) {
      // Стеклянные вкладки обрабатываются в glassmorphism.js
    } else {
      // Поведение вкладок по умолчанию
      const tabs = group.querySelectorAll('[data-tab-target]');
      const tabContents = document.querySelectorAll(`[data-tab-group="${group.dataset.tabGroup}"] .tab-content`);

      tabs.forEach(tab => {
        tab.addEventListener('click', function () {
          tabs.forEach(t => t.classList.remove('active'));
          this.classList.add('active');

          tabContents.forEach(content => {
            content.style.display = 'none';
          });

          const tabContentId = this.dataset.tabTarget;
          const tabContent = document.getElementById(tabContentId);
          if (tabContent) {
            tabContent.style.display = 'block';
          }
        });
      });

      // Активация первой вкладки по умолчанию
      if (tabs.length > 0) {
        tabs[0].click();
      }
    }
  });
}

// Обновление интерфейса на основе выбранного профиля ребенка
function updateUIForProfile(profileId) {
  // Эта функция будет реализована при добавлении профилей детей
  console.log(`Переключение на профиль: ${profileId}`);

  // Пример: Обновление содержимого на основе выбранного профиля
  const profileSpecificElements = document.querySelectorAll(`[data-profile-id]`);
  profileSpecificElements.forEach(element => {
    if (element.dataset.profileId === profileId) {
      element.classList.remove('hidden');
    } else {
      element.classList.add('hidden');
    }
  });
}

// Вспомогательная функция для форматирования дат
function formatDate(date) {
  if (!date) return '';

  const d = new Date(date);
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

// Вспомогательная функция для расчета возраста по дате рождения
function calculateAge(birthDate) {
  if (!birthDate) return '';

  const birth = new Date(birthDate);
  const now = new Date();

  let years = now.getFullYear() - birth.getFullYear();
  let months = now.getMonth() - birth.getMonth();

  if (months < 0) {
    years--;
    months += 12;
  }

  const days = now.getDate() - birth.getDate();

  if (days < 0) {
    months--;
    // Добавление дней в последнем месяце
    const lastMonth = new Date(now.getFullYear(), now.getMonth(), 0);
    days += lastMonth.getDate();
  }

  if (years > 0) {
    return `${years} г. ${months} мес.`;
  } else if (months > 0) {
    return `${months} мес. ${days} дн.`;
  } else {
    return `${days} дн.`;
  }
}
// Инициализация индикатора активных таймеров
function initActiveTimersIndicator() {
  const indicator = document.getElementById('active-timers-indicator');
  const countElement = document.getElementById('active-timers-count');

  if (!indicator || !countElement) return;

  // Обработка событий от TimerManager
  document.addEventListener('timerManager:activeTimersUpdated', (event) => {
    const timers = event.detail.timers;
    updateActiveTimersIndicator(timers);
  });

  document.addEventListener('timerManager:timerStarted', (event) => {
    const timers = window.timerManager.getAllActiveTimers();
    updateActiveTimersIndicator(timers);
  });

  document.addEventListener('timerManager:timerStopped', (event) => {
    const timers = window.timerManager.getAllActiveTimers();
    updateActiveTimersIndicator(timers);
  });

  // Обновление индикатора при инициализации
  const timers = window.timerManager.getAllActiveTimers();
  updateActiveTimersIndicator(timers);

  // Клик по индикатору открывает модальное окно со списком активных таймеров
  indicator.addEventListener('click', () => {
    showActiveTimersModal();
  });
}

// Обновление индикатора активных таймеров
function updateActiveTimersIndicator(timers) {
  const indicator = document.getElementById('active-timers-indicator');
  const countElement = document.getElementById('active-timers-count');

  if (!indicator || !countElement) return;

  if (timers.length > 0) {
    indicator.classList.remove('hidden');

    const timerText = timers.length === 1 ? 'активный таймер' : 'активных таймера';
    countElement.textContent = `${timers.length} ${timerText}`;
  } else {
    indicator.classList.add('hidden');
  }
}

// Показать модальное окно со списком активных таймеров
function showActiveTimersModal() {
  const timers = window.timerManager.getAllActiveTimers();

  if (timers.length === 0) return;

  // Создаем модальное окно
  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';

  // Содержимое модального окна
  let modalContent = `
    <div class="glass-card max-w-md w-full mx-4 p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold">Активные таймеры</h3>
        <button id="close-timers-modal" class="neo-button neo-sm">✕</button>
      </div>
      <div class="space-y-4">
  `;

  // Добавляем информацию о каждом таймере
  timers.forEach(timer => {
    const elapsedSeconds = TimerManager.getElapsedSeconds(timer.startTime);
    const formattedTime = TimerManager.formatTime(elapsedSeconds);

    let timerTitle = 'Таймер';
    let timerIcon = '⏱️';
    let timerUrl = '/';

    switch (timer.type) {
      case 'sleep':
        timerTitle = timer.metadata?.sleepType === 'day' ? 'Дневной сон' : 'Ночной сон';
        timerIcon = '💤';
        timerUrl = '/tools/sleep_timer/';
        break;
      case 'feeding':
        timerTitle = 'Кормление';
        timerIcon = '🍼';
        timerUrl = '/tools/feeding_tracker/';
        break;
      case 'contraction':
        timerTitle = 'Схватки';
        timerIcon = '⏱️';
        timerUrl = '/tools/contraction_counter/';
        break;
      case 'kick':
        timerTitle = 'Шевеления';
        timerIcon = '👶';
        timerUrl = '/tools/kick_counter/';
        break;
    }

    modalContent += `
      <div class="neo-card p-4">
        <div class="flex justify-between items-center">
          <div>
            <div class="flex items-center">
              <span class="mr-2">${timerIcon}</span>
              <span class="font-medium">${timerTitle}</span>
            </div>
            <div class="text-sm text-dark-gray mt-1">
              Запущен: ${new Date(timer.startTime).toLocaleTimeString('ru-RU')}
            </div>
          </div>
          <div class="text-xl font-bold">${formattedTime}</div>
        </div>
        <div class="flex justify-between mt-4">
          <a href="${timerUrl}" class="neo-button neo-sm">Открыть</a>
          <button class="neo-button neo-sm bg-accent" data-timer-id="${timer.timerId}">Остановить</button>
        </div>
      </div>
    `;
  });

  modalContent += `
      </div>
    </div>
  `;

  modal.innerHTML = modalContent;
  document.body.appendChild(modal);

  // Обработчик для закрытия модального окна
  document.getElementById('close-timers-modal').addEventListener('click', () => {
    document.body.removeChild(modal);
  });

  // Обработчики для кнопок остановки таймеров
  modal.querySelectorAll('[data-timer-id]').forEach(button => {
    button.addEventListener('click', () => {
      const timerId = button.dataset.timerId;
      window.timerManager.stopTimer(timerId);
      document.body.removeChild(modal);
    });
  });
}

// Инициализация индикатора онлайн/офлайн статуса
function initOnlineStatusIndicator() {
  // Создаем индикатор, если его еще нет
  let statusIndicator = document.getElementById('online-status-indicator');
  
  if (!statusIndicator) {
    statusIndicator = document.createElement('div');
    statusIndicator.id = 'online-status-indicator';
    statusIndicator.className = 'fixed bottom-4 right-4 px-3 py-1 rounded-full text-sm font-medium z-50 transition-all duration-300';
    document.body.appendChild(statusIndicator);
  }
  
  // Функция обновления статуса
  const updateOnlineStatus = () => {
    if (navigator.onLine) {
      statusIndicator.textContent = 'Онлайн';
      statusIndicator.className = 'fixed bottom-4 right-4 px-3 py-1 rounded-full text-sm font-medium z-50 transition-all duration-300 bg-green-100 text-green-800';
      
      // Скрываем индикатор через 3 секунды
      setTimeout(() => {
        statusIndicator.classList.add('opacity-0');
        setTimeout(() => {
          statusIndicator.classList.add('hidden');
        }, 300);
      }, 3000);
    } else {
      statusIndicator.textContent = 'Офлайн';
      statusIndicator.className = 'fixed bottom-4 right-4 px-3 py-1 rounded-full text-sm font-medium z-50 transition-all duration-300 bg-yellow-100 text-yellow-800';
      statusIndicator.classList.remove('hidden', 'opacity-0');
    }
  };
  
  // Обработчики событий
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  
  // Инициализация статуса
  updateOnlineStatus();
}