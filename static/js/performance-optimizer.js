/**
 * Модуль оптимизации производительности для приложения Mom&BabyBot
 * Обеспечивает оптимизацию загрузки страниц, кэширования данных и работы с DOM
 */

class PerformanceOptimizer {
  constructor() {
    this.resourceHints = {
      preconnect: [],
      prefetch: [],
      preload: []
    };
    this.lazyLoadObserver = null;
    this.debouncedEvents = new Map();
    this.throttledEvents = new Map();
    this.intersectionObservers = new Map();
    
    // Инициализация
    this.init();
  }
  
  /**
   * Инициализация оптимизатора производительности
   */
  init() {
    // Добавляем обработчик события загрузки страницы
    window.addEventListener('load', this.onPageLoad.bind(this));
    
    // Инициализируем ленивую загрузку изображений
    this.initLazyLoading();
    
    // Оптимизируем обработчики событий
    this.optimizeEventListeners();
    
    // Добавляем подсказки ресурсов
    this.addResourceHints();
  }
  
  /**
   * Обработчик события загрузки страницы
   */
  onPageLoad() {
    // Отложенная загрузка несрочных скриптов
    this.deferNonCriticalScripts();
    
    // Предварительная загрузка страниц при наведении
    this.initPrefetchOnHover();
    
    // Оптимизация шрифтов
    this.optimizeFonts();
    
    // Оптимизация изображений
    this.optimizeImages();
    
    // Измерение производительности
    this.measurePerformance();
  }
  
  /**
   * Добавление подсказок ресурсов (resource hints)
   */
  addResourceHints() {
    // Preconnect для основных доменов
    this.addPreconnect(window.location.origin);
    
    // Preload для критических ресурсов
    this.addPreload('/static/css/maternal-theme.css', 'style');
    this.addPreload('/static/css/neomorphism.css', 'style');
    this.addPreload('/static/css/style.css', 'style');
    this.addPreload('/static/js/maternal-app.js', 'script');
    
    // Применяем подсказки ресурсов
    this.applyResourceHints();
  }
  
  /**
   * Добавление preconnect для домена
   * @param {string} url - URL домена
   */
  addPreconnect(url) {
    this.resourceHints.preconnect.push(url);
  }
  
  /**
   * Добавление prefetch для URL
   * @param {string} url - URL для предварительной загрузки
   */
  addPrefetch(url) {
    this.resourceHints.prefetch.push(url);
  }
  
  /**
   * Добавление preload для ресурса
   * @param {string} url - URL ресурса
   * @param {string} as - Тип ресурса (script, style, font, image)
   */
  addPreload(url, as) {
    this.resourceHints.preload.push({ url, as });
  }
  
  /**
   * Применение подсказок ресурсов
   */
  applyResourceHints() {
    // Добавляем preconnect
    this.resourceHints.preconnect.forEach(url => {
      const link = document.createElement('link');
      link.rel = 'preconnect';
      link.href = url;
      document.head.appendChild(link);
    });
    
    // Добавляем prefetch
    this.resourceHints.prefetch.forEach(url => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      document.head.appendChild(link);
    });
    
    // Добавляем preload
    this.resourceHints.preload.forEach(item => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = item.url;
      link.as = item.as;
      document.head.appendChild(link);
    });
  }
  
  /**
   * Отложенная загрузка несрочных скриптов
   */
  deferNonCriticalScripts() {
    // Список несрочных скриптов
    const nonCriticalScripts = [
      '/static/js/telegram-integration.js'
    ];
    
    // Загружаем скрипты с задержкой
    setTimeout(() => {
      nonCriticalScripts.forEach(src => {
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        document.body.appendChild(script);
      });
    }, 1000);
  }
  
  /**
   * Инициализация ленивой загрузки изображений
   */
  initLazyLoading() {
    // Проверяем поддержку IntersectionObserver
    if ('IntersectionObserver' in window) {
      this.lazyLoadObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            const src = img.getAttribute('data-src');
            
            if (src) {
              img.src = src;
              img.removeAttribute('data-src');
              observer.unobserve(img);
            }
          }
        });
      });
      
      // Применяем ленивую загрузку ко всем изображениям с атрибутом data-src
      document.addEventListener('DOMContentLoaded', () => {
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => {
          this.lazyLoadObserver.observe(img);
        });
      });
    } else {
      // Запасной вариант для браузеров без поддержки IntersectionObserver
      document.addEventListener('DOMContentLoaded', () => {
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => {
          img.src = img.getAttribute('data-src');
          img.removeAttribute('data-src');
        });
      });
    }
  }
  
  /**
   * Инициализация предварительной загрузки страниц при наведении
   */
  initPrefetchOnHover() {
    document.querySelectorAll('a[href^="/"]').forEach(link => {
      link.addEventListener('mouseenter', this.handleLinkHover.bind(this));
      link.addEventListener('touchstart', this.handleLinkHover.bind(this));
    });
  }
  
  /**
   * Обработчик наведения на ссылку
   * @param {Event} event - Событие наведения
   */
  handleLinkHover(event) {
    const link = event.currentTarget;
    const href = link.getAttribute('href');
    
    // Проверяем, что ссылка еще не была предзагружена
    if (href && !this.resourceHints.prefetch.includes(href)) {
      // Добавляем prefetch для URL
      this.addPrefetch(href);
      
      // Применяем prefetch
      const prefetchLink = document.createElement('link');
      prefetchLink.rel = 'prefetch';
      prefetchLink.href = href;
      document.head.appendChild(prefetchLink);
    }
  }
  
  /**
   * Оптимизация шрифтов
   */
  optimizeFonts() {
    // Добавляем font-display: swap для всех шрифтов
    const style = document.createElement('style');
    style.textContent = `
      @font-face {
        font-display: swap;
      }
    `;
    document.head.appendChild(style);
    
    // Предзагрузка основных шрифтов
    const fontFiles = [
      '/static/fonts/Roboto-Regular.woff2',
      '/static/fonts/Roboto-Medium.woff2',
      '/static/fonts/Roboto-Bold.woff2'
    ];
    
    fontFiles.forEach(font => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = font;
      link.as = 'font';
      link.type = 'font/woff2';
      link.crossOrigin = 'anonymous';
      document.head.appendChild(link);
    });
  }
  
  /**
   * Оптимизация изображений
   */
  optimizeImages() {
    // Добавляем атрибуты width и height ко всем изображениям
    document.querySelectorAll('img:not([width]):not([height])').forEach(img => {
      // Если изображение загружено, устанавливаем его размеры
      if (img.complete) {
        img.setAttribute('width', img.naturalWidth);
        img.setAttribute('height', img.naturalHeight);
      } else {
        // Иначе ждем загрузки
        img.addEventListener('load', () => {
          img.setAttribute('width', img.naturalWidth);
          img.setAttribute('height', img.naturalHeight);
        });
      }
    });
  }
  
  /**
   * Оптимизация обработчиков событий
   */
  optimizeEventListeners() {
    // Делегирование событий
    this.setupEventDelegation();
    
    // Debounce для событий ввода
    this.setupInputDebounce();
    
    // Throttle для событий прокрутки
    this.setupScrollThrottle();
  }
  
  /**
   * Настройка делегирования событий
   */
  setupEventDelegation() {
    // Пример делегирования для кнопок
    document.addEventListener('click', event => {
      // Обработка кнопок с атрибутом data-action
      const button = event.target.closest('[data-action]');
      if (button) {
        const action = button.getAttribute('data-action');
        this.handleAction(action, button);
      }
    });
  }
  
  /**
   * Обработка действия
   * @param {string} action - Название действия
   * @param {HTMLElement} element - Элемент, вызвавший действие
   */
  handleAction(action, element) {
    // Обработка различных действий
    switch (action) {
      case 'toggle':
        const targetId = element.getAttribute('data-target');
        const target = document.getElementById(targetId);
        if (target) {
          target.classList.toggle('hidden');
        }
        break;
      
      // Другие действия...
    }
  }
  
  /**
   * Настройка debounce для событий ввода
   */
  setupInputDebounce() {
    // Применяем debounce ко всем полям ввода с атрибутом data-debounce
    document.querySelectorAll('input[data-debounce], textarea[data-debounce]').forEach(input => {
      const delay = parseInt(input.getAttribute('data-debounce')) || 300;
      
      input.addEventListener('input', event => {
        const inputId = input.id || Math.random().toString(36).substr(2, 9);
        
        // Отменяем предыдущий таймер, если он есть
        if (this.debouncedEvents.has(inputId)) {
          clearTimeout(this.debouncedEvents.get(inputId));
        }
        
        // Создаем новый таймер
        const timerId = setTimeout(() => {
          // Вызываем обработчик события
          const handler = input.getAttribute('data-handler');
          if (handler && window[handler]) {
            window[handler](event);
          }
          
          // Удаляем таймер из карты
          this.debouncedEvents.delete(inputId);
        }, delay);
        
        // Сохраняем таймер в карту
        this.debouncedEvents.set(inputId, timerId);
      });
    });
  }
  
  /**
   * Настройка throttle для событий прокрутки
   */
  setupScrollThrottle() {
    // Применяем throttle к обработчикам прокрутки
    const scrollHandlers = document.querySelectorAll('[data-scroll-handler]');
    
    scrollHandlers.forEach(element => {
      const handler = element.getAttribute('data-scroll-handler');
      const delay = parseInt(element.getAttribute('data-scroll-throttle')) || 100;
      
      if (handler && window[handler]) {
        const elementId = element.id || Math.random().toString(36).substr(2, 9);
        
        window.addEventListener('scroll', event => {
          // Если нет активного таймера, создаем новый
          if (!this.throttledEvents.has(elementId)) {
            // Вызываем обработчик события
            window[handler](event);
            
            // Создаем таймер
            const timerId = setTimeout(() => {
              this.throttledEvents.delete(elementId);
            }, delay);
            
            // Сохраняем таймер в карту
            this.throttledEvents.set(elementId, timerId);
          }
        });
      }
    });
  }
  
  /**
   * Измерение производительности
   */
  measurePerformance() {
    // Проверяем поддержку Performance API
    if ('performance' in window && 'getEntriesByType' in performance) {
      // Измеряем время загрузки страницы
      window.addEventListener('load', () => {
        setTimeout(() => {
          const pageLoadTime = performance.getEntriesByType('navigation')[0].loadEventEnd;
          console.log(`Время загрузки страницы: ${pageLoadTime.toFixed(2)} мс`);
          
          // Отправляем метрики на сервер
          this.sendPerformanceMetrics({
            pageLoadTime,
            url: window.location.pathname
          });
        }, 0);
      });
      
      // Измеряем First Contentful Paint (FCP)
      const observer = new PerformanceObserver(list => {
        const entries = list.getEntries();
        const fcp = entries[0];
        console.log(`First Contentful Paint: ${fcp.startTime.toFixed(2)} мс`);
        
        // Отправляем метрики на сервер
        this.sendPerformanceMetrics({
          fcp: fcp.startTime,
          url: window.location.pathname
        });
      });
      
      observer.observe({ type: 'paint', buffered: true });
    }
  }
  
  /**
   * Отправка метрик производительности на сервер
   * @param {Object} metrics - Метрики производительности
   */
  sendPerformanceMetrics(metrics) {
    // Отправляем метрики на сервер с использованием Beacon API
    if ('sendBeacon' in navigator) {
      const data = JSON.stringify({
        metrics,
        userAgent: navigator.userAgent,
        timestamp: Date.now()
      });
      
      navigator.sendBeacon('/api/performance-metrics', data);
    } else {
      // Запасной вариант с использованием fetch
      fetch('/api/performance-metrics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          metrics,
          userAgent: navigator.userAgent,
          timestamp: Date.now()
        }),
        keepalive: true
      }).catch(error => {
        console.error('Ошибка при отправке метрик производительности:', error);
      });
    }
  }
  
  /**
   * Создание IntersectionObserver для элемента
   * @param {string} selector - CSS-селектор элементов
   * @param {Function} callback - Функция обратного вызова
   * @param {Object} options - Опции IntersectionObserver
   */
  createIntersectionObserver(selector, callback, options = {}) {
    // Проверяем поддержку IntersectionObserver
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          callback(entry, observer);
        });
      }, options);
      
      // Сохраняем observer в карту
      this.intersectionObservers.set(selector, observer);
      
      // Наблюдаем за элементами
      document.querySelectorAll(selector).forEach(element => {
        observer.observe(element);
      });
      
      return observer;
    }
    
    return null;
  }
  
  /**
   * Остановка наблюдения за элементами
   * @param {string} selector - CSS-селектор элементов
   */
  stopObserving(selector) {
    if (this.intersectionObservers.has(selector)) {
      const observer = this.intersectionObservers.get(selector);
      observer.disconnect();
      this.intersectionObservers.delete(selector);
    }
  }
}

// Создаем глобальный экземпляр оптимизатора производительности
window.performanceOptimizer = new PerformanceOptimizer();