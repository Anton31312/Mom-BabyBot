/**
 * Утилиты JavaScript для неоморфизма
 */

// Функциональность переключателей в неоморфном стиле
document.addEventListener('DOMContentLoaded', function() {
  const toggles = document.querySelectorAll('.neo-toggle');
  
  toggles.forEach(toggle => {
    toggle.addEventListener('click', function() {
      this.classList.toggle('active');
      
      // Генерация пользовательского события при изменении состояния
      const isActive = this.classList.contains('active');
      const event = new CustomEvent('toggleChange', {
        detail: { isActive: isActive }
      });
      this.dispatchEvent(event);
    });
  });
});

// Функциональность вкладок в неоморфном стиле
document.addEventListener('DOMContentLoaded', function() {
  const tabGroups = document.querySelectorAll('.neo-tabs');
  
  tabGroups.forEach(tabGroup => {
    const tabs = tabGroup.querySelectorAll('.neo-tab');
    const tabContents = document.querySelectorAll(`[data-tab-group="${tabGroup.dataset.tabGroup}"] .tab-content`);
    
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', function() {
        // Удаление активного класса со всех вкладок
        tabs.forEach(t => t.classList.remove('active'));
        
        // Добавление активного класса к выбранной вкладке
        this.classList.add('active');
        
        // Скрытие всего содержимого вкладок
        tabContents.forEach(content => {
          content.style.display = 'none';
        });
        
        // Отображение соответствующего содержимого вкладки
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
  });
});

// Программное создание неоморфных элементов
const Neomorphism = {
  createButton: function(text, options = {}) {
    const button = document.createElement('button');
    button.className = 'neo-button';
    button.textContent = text;
    
    if (options.onClick) {
      button.addEventListener('click', options.onClick);
    }
    
    if (options.className) {
      button.className += ' ' + options.className;
    }
    
    return button;
  },
  
  createCard: function(content, options = {}) {
    const card = document.createElement('div');
    card.className = 'neo-card';
    
    if (typeof content === 'string') {
      card.innerHTML = content;
    } else if (content instanceof HTMLElement) {
      card.appendChild(content);
    }
    
    if (options.className) {
      card.className += ' ' + options.className;
    }
    
    if (options.padding) {
      card.style.padding = options.padding;
    } else {
      card.style.padding = '20px';
    }
    
    return card;
  },
  
  createToggle: function(options = {}) {
    const toggle = document.createElement('div');
    toggle.className = 'neo-toggle';
    
    if (options.isActive) {
      toggle.classList.add('active');
    }
    
    if (options.onChange) {
      toggle.addEventListener('toggleChange', options.onChange);
    }
    
    if (options.className) {
      toggle.className += ' ' + options.className;
    }
    
    return toggle;
  }
};// Расширенная функциональность неоморфизма

// Функциональность выпадающих списков
document.addEventListener('DOMContentLoaded', function() {
  const dropdowns = document.querySelectorAll('.neo-dropdown');
  
  dropdowns.forEach(dropdown => {
    const toggle = dropdown.querySelector('.neo-dropdown-toggle');
    
    if (toggle) {
      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        
        // Закрытие всех других выпадающих списков
        dropdowns.forEach(d => {
          if (d !== dropdown) {
            d.classList.remove('active');
          }
        });
        
        // Переключение текущего выпадающего списка
        dropdown.classList.toggle('active');
      });
    }
  });
  
  // Закрытие выпадающих списков при клике вне их области
  document.addEventListener('click', function() {
    dropdowns.forEach(dropdown => {
      dropdown.classList.remove('active');
    });
  });
});

// Анимация индикаторов прогресса
document.addEventListener('DOMContentLoaded', function() {
  const progressBars = document.querySelectorAll('.neo-progress-bar');
  
  progressBars.forEach(bar => {
    const targetWidth = bar.style.width;
    bar.style.width = '0';
    
    setTimeout(() => {
      bar.style.width = targetWidth;
    }, 300);
  });
});

// Расширение объекта Neomorphism новыми компонентами
Object.assign(Neomorphism, {
  createAvatar: function(options = {}) {
    const avatar = document.createElement('div');
    avatar.className = 'neo-avatar';
    
    if (options.size) {
      if (options.size === 'sm') {
        avatar.classList.add('w-8', 'h-8');
      } else if (options.size === 'lg') {
        avatar.classList.add('w-16', 'h-16');
      } else {
        avatar.classList.add('w-12', 'h-12');
      }
    } else {
      avatar.classList.add('w-12', 'h-12');
    }
    
    if (options.imageUrl) {
      const img = document.createElement('img');
      img.src = options.imageUrl;
      img.alt = options.altText || 'Avatar';
      avatar.appendChild(img);
    } else {
      avatar.innerHTML = `<div class="flex items-center justify-center w-full h-full bg-primary text-dark-gray font-semibold">
        ${options.altText ? options.altText.charAt(0) : 'U'}
      </div>`;
    }
    
    if (options.className) {
      avatar.className += ' ' + options.className;
    }
    
    return avatar;
  },
  
  createBadge: function(text, options = {}) {
    const badge = document.createElement('span');
    badge.className = 'neo-badge';
    badge.textContent = text;
    
    if (options.variant) {
      badge.classList.add(`neo-${options.variant}`);
    }
    
    if (options.className) {
      badge.className += ' ' + options.className;
    }
    
    return badge;
  },
  
  createProgress: function(value, options = {}) {
    const progress = document.createElement('div');
    progress.className = 'neo-progress';
    
    const progressBar = document.createElement('div');
    progressBar.className = 'neo-progress-bar';
    
    if (options.variant) {
      progressBar.classList.add(`neo-${options.variant}`);
    } else {
      progressBar.classList.add('neo-primary');
    }
    
    const percentage = (value / (options.max || 100)) * 100;
    progressBar.style.width = `${percentage}%`;
    
    progress.appendChild(progressBar);
    
    if (options.className) {
      progress.className += ' ' + options.className;
    }
    
    return progress;
  },
  
  createAlert: function(options = {}) {
    const alert = document.createElement('div');
    alert.className = 'neo-alert';
    
    if (options.variant) {
      alert.classList.add(`neo-${options.variant}`);
    }
    
    if (options.iconSvg) {
      const iconDiv = document.createElement('div');
      iconDiv.className = 'neo-alert-icon';
      iconDiv.innerHTML = options.iconSvg;
      alert.appendChild(iconDiv);
    }
    
    const content = document.createElement('div');
    content.className = 'neo-alert-content';
    
    if (options.title) {
      const title = document.createElement('div');
      title.className = 'neo-alert-title';
      title.textContent = options.title;
      content.appendChild(title);
    }
    
    if (options.content) {
      const message = document.createElement('div');
      message.className = 'neo-alert-message';
      message.textContent = options.content;
      content.appendChild(message);
    }
    
    alert.appendChild(content);
    
    if (options.className) {
      alert.className += ' ' + options.className;
    }
    
    return alert;
  }
});