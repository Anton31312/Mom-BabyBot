/**
 * Утилиты JavaScript для стеклянного стиля (Glassmorphism)
 */

// Функциональность вкладок в стеклянном стиле
document.addEventListener('DOMContentLoaded', function() {
  const tabGroups = document.querySelectorAll('.glass-tabs');
  
  tabGroups.forEach(tabGroup => {
    const tabs = tabGroup.querySelectorAll('.glass-tab');
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

// Эффект параллакса для стеклянных карточек
document.addEventListener('DOMContentLoaded', function() {
  const glassCards = document.querySelectorAll('.glass-card[data-parallax="true"]');
  
  glassCards.forEach(card => {
    card.addEventListener('mousemove', function(e) {
      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const moveX = (x - centerX) / 20;
      const moveY = (y - centerY) / 20;
      
      this.style.transform = `perspective(1000px) rotateX(${-moveY}deg) rotateY(${moveX}deg)`;
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
    });
  });
});

// Программное создание элементов в стеклянном стиле
const Glassmorphism = {
  createButton: function(text, options = {}) {
    const button = document.createElement('button');
    button.className = 'glass-button';
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
    card.className = 'glass-card';
    
    if (typeof content === 'string') {
      card.innerHTML = content;
    } else if (content instanceof HTMLElement) {
      card.appendChild(content);
    }
    
    if (options.className) {
      card.className += ' ' + options.className;
    }
    
    if (options.parallax) {
      card.setAttribute('data-parallax', 'true');
    }
    
    return card;
  },
  
  createContainer: function(content, options = {}) {
    const container = document.createElement('div');
    container.className = 'glass-container';
    
    if (typeof content === 'string') {
      container.innerHTML = content;
    } else if (content instanceof HTMLElement) {
      container.appendChild(content);
    }
    
    if (options.className) {
      container.className += ' ' + options.className;
    }
    
    return container;
  }
};// Расширенная функциональность стеклянного стиля

// Функциональность выпадающих списков
document.addEventListener('DOMContentLoaded', function() {
  const dropdowns = document.querySelectorAll('.glass-dropdown');
  
  dropdowns.forEach(dropdown => {
    const toggle = dropdown.querySelector('.glass-dropdown-toggle');
    
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
  const progressBars = document.querySelectorAll('.glass-progress-bar');
  
  progressBars.forEach(bar => {
    const targetWidth = bar.style.width;
    bar.style.width = '0';
    
    setTimeout(() => {
      bar.style.width = targetWidth;
    }, 300);
  });
});

// Расширенный эффект параллакса
document.addEventListener('DOMContentLoaded', function() {
  const glassCards = document.querySelectorAll('.glass-card[data-parallax="true"]');
  
  glassCards.forEach(card => {
    card.addEventListener('mousemove', function(e) {
      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const moveX = (x - centerX) / 20;
      const moveY = (y - centerY) / 20;
      
      this.style.transform = `perspective(1000px) rotateX(${-moveY}deg) rotateY(${moveX}deg)`;
      
      // Добавление эффекта отражения света
      const percentX = x / rect.width * 100;
      const percentY = y / rect.height * 100;
      this.style.backgroundImage = `radial-gradient(circle at ${percentX}% ${percentY}%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 50%)`;
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
      this.style.backgroundImage = 'none';
    });
  });
});

// Расширение объекта Glassmorphism новыми компонентами
Object.assign(Glassmorphism, {
  createAvatar: function(options = {}) {
    const avatar = document.createElement('div');
    avatar.className = 'glass-avatar';
    
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
      avatar.innerHTML = `<div class="flex items-center justify-center w-full h-full bg-glass-primary text-dark-gray font-semibold">
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
    badge.className = 'glass-badge';
    badge.textContent = text;
    
    if (options.variant) {
      badge.classList.add(`glass-${options.variant}`);
    }
    
    if (options.className) {
      badge.className += ' ' + options.className;
    }
    
    return badge;
  },
  
  createProgress: function(value, options = {}) {
    const progress = document.createElement('div');
    progress.className = 'glass-progress';
    
    const progressBar = document.createElement('div');
    progressBar.className = 'glass-progress-bar';
    
    if (options.variant) {
      progressBar.classList.add(`glass-${options.variant}`);
    } else {
      progressBar.classList.add('glass-primary');
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
    alert.className = 'glass-alert';
    
    if (options.variant) {
      alert.classList.add(`glass-${options.variant}`);
    }
    
    if (options.iconSvg) {
      const iconDiv = document.createElement('div');
      iconDiv.className = 'glass-alert-icon';
      iconDiv.innerHTML = options.iconSvg;
      alert.appendChild(iconDiv);
    }
    
    const content = document.createElement('div');
    content.className = 'glass-alert-content';
    
    if (options.title) {
      const title = document.createElement('div');
      title.className = 'glass-alert-title';
      title.textContent = options.title;
      content.appendChild(title);
    }
    
    if (options.content) {
      const message = document.createElement('div');
      message.className = 'glass-alert-message';
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