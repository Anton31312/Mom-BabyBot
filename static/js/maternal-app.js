/**
 * Основной JavaScript для приложения Mom&BabyBot
 */

// Инициализация Telegram Web App
document.addEventListener('DOMContentLoaded', function() {
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
});

// Функциональность навигации
function initNavigation() {
  const navToggle = document.getElementById('nav-toggle');
  const mobileNav = document.getElementById('mobile-nav');
  
  if (navToggle && mobileNav) {
    navToggle.addEventListener('click', function(e) {
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
    document.addEventListener('click', function(e) {
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
    profileSwitcher.addEventListener('change', function() {
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
        tab.addEventListener('click', function() {
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