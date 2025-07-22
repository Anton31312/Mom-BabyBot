/**
 * Модуль оптимизации статических файлов для приложения Mom&BabyBot
 * Обеспечивает оптимизацию загрузки CSS и JavaScript файлов
 */

class StaticOptimizer {
  constructor() {
    this.loadedResources = new Set();
    this.resourceQueue = [];
    this.criticalCSS = '';
    this.inlineScripts = '';
    
    // Инициализация
    this.init();
  }
  
  /**
   * Инициализация оптимизатора статических файлов
   */
  init() {
    // Добавляем обработчик события загрузки страницы
    window.addEventListener('load', this.onPageLoad.bind(this));
    
    // Извлекаем критический CSS
    this.extractCriticalCSS();
    
    // Оптимизируем загрузку скриптов
    this.optimizeScriptLoading();
  }
  
  /**
   * Обработчик события загрузки страницы
   */
  onPageLoad() {
    // Загружаем отложенные ресурсы
    this.loadDeferredResources();
    
    // Предзагружаем ресурсы для следующих страниц
    this.prefetchNextPageResources();
  }
  
  /**
   * Извлечение критического CSS
   */
  extractCriticalCSS() {
    // Получаем все стили, примененные к видимым элементам
    const criticalStyles = new Set();
    
    // Функция для обхода DOM и извлечения стилей
    const extractStyles = (element) => {
      // Получаем примененные стили
      const styles = window.getComputedStyle(element);
      
      // Добавляем важные стили в набор
      const importantProperties = [
        'display', 'position', 'top', 'right', 'bottom', 'left',
        'width', 'height', 'margin', 'padding', 'border',
        'color', 'background', 'font-family', 'font-size',
        'text-align', 'line-height', 'flex', 'grid'
      ];
      
      importantProperties.forEach(prop => {
        const value = styles.getPropertyValue(prop);
        if (value) {
          criticalStyles.add(`${prop}: ${value};`);
        }
      });
      
      // Рекурсивно обходим дочерние элементы
      Array.from(element.children).forEach(child => {
        // Проверяем, находится ли элемент в области видимости
        const rect = child.getBoundingClientRect();
        const isVisible = rect.top < window.innerHeight && rect.bottom >= 0;
        
        if (isVisible) {
          extractStyles(child);
        }
      });
    };
    
    // Запускаем извлечение стилей после загрузки DOM
    document.addEventListener('DOMContentLoaded', () => {
      // Извлекаем стили только для видимой части страницы
      extractStyles(document.body);
      
      // Формируем критический CSS
      this.criticalCSS = Array.from(criticalStyles).join('\n');
      
      // Вставляем критический CSS в head
      const styleElement = document.createElement('style');
      styleElement.textContent = this.criticalCSS;
      document.head.appendChild(styleElement);
    });
  }
  
  /**
   * Оптимизация загрузки скриптов
   */
  optimizeScriptLoading() {
    // Получаем все скрипты на странице
    const scripts = document.querySelectorAll('script[src]');
    
    // Определяем критические скрипты
    const criticalScripts = Array.from(scripts).filter(script => {
      return script.hasAttribute('data-critical') || 
             script.src.includes('maternal-app.js') ||
             script.src.includes('neomorphism.js');
    });
    
    // Определяем некритические скрипты
    const nonCriticalScripts = Array.from(scripts).filter(script => {
      return !criticalScripts.includes(script);
    });
    
    // Загружаем некритические скрипты с задержкой
    nonCriticalScripts.forEach(script => {
      // Сохраняем атрибуты скрипта
      const src = script.src;
      const async = script.async;
      const defer = script.defer;
      
      // Удаляем оригинальный скрипт
      script.parentNode.removeChild(script);
      
      // Добавляем скрипт в очередь для отложенной загрузки
      this.resourceQueue.push({
        type: 'script',
        src: src,
        async: async,
        defer: defer
      });
    });
  }
  
  /**
   * Загрузка отложенных ресурсов
   */
  loadDeferredResources() {
    // Проверяем поддержку requestIdleCallback
    const requestIdleCallback = window.requestIdleCallback || 
                               ((callback) => setTimeout(callback, 1));
    
    // Загружаем ресурсы в период простоя
    requestIdleCallback(() => {
      this.loadNextResource();
    });
  }
  
  /**
   * Загрузка следующего ресурса из очереди
   */
  loadNextResource() {
    // Если очередь пуста, выходим
    if (this.resourceQueue.length === 0) {
      return;
    }
    
    // Получаем следующий ресурс
    const resource = this.resourceQueue.shift();
    
    // Проверяем, был ли ресурс уже загружен
    if (this.loadedResources.has(resource.src)) {
      // Переходим к следующему ресурсу
      this.loadNextResource();
      return;
    }
    
    // Загружаем ресурс в зависимости от его типа
    if (resource.type === 'script') {
      // Создаем элемент script
      const script = document.createElement('script');
      script.src = resource.src;
      if (resource.async) script.async = true;
      if (resource.defer) script.defer = true;
      
      // Добавляем обработчик загрузки
      script.onload = () => {
        // Отмечаем ресурс как загруженный
        this.loadedResources.add(resource.src);
        
        // Загружаем следующий ресурс
        this.loadNextResource();
      };
      
      // Добавляем обработчик ошибки
      script.onerror = () => {
        console.error(`Ошибка загрузки скрипта: ${resource.src}`);
        
        // Загружаем следующий ресурс
        this.loadNextResource();
      };
      
      // Добавляем скрипт в документ
      document.body.appendChild(script);
    } else if (resource.type === 'style') {
      // Создаем элемент link
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = resource.src;
      
      // Добавляем обработчик загрузки
      link.onload = () => {
        // Отмечаем ресурс как загруженный
        this.loadedResources.add(resource.src);
        
        // Загружаем следующий ресурс
        this.loadNextResource();
      };
      
      // Добавляем обработчик ошибки
      link.onerror = () => {
        console.error(`Ошибка загрузки стиля: ${resource.src}`);
        
        // Загружаем следующий ресурс
        this.loadNextResource();
      };
      
      // Добавляем стиль в документ
      document.head.appendChild(link);
    } else {
      // Неизвестный тип ресурса, переходим к следующему
      this.loadNextResource();
    }
  }
  
  /**
   * Предзагрузка ресурсов для следующих страниц
   */
  prefetchNextPageResources() {
    // Получаем все ссылки на странице
    const links = document.querySelectorAll('a[href^="/"]');
    
    // Создаем набор уникальных URL
    const uniqueUrls = new Set();
    
    // Добавляем URL в набор
    links.forEach(link => {
      const href = link.getAttribute('href');
      if (href && !href.includes('#')) {
        uniqueUrls.add(href);
      }
    });
    
    // Предзагружаем ресурсы для каждого URL
    uniqueUrls.forEach(url => {
      // Проверяем, был ли URL уже предзагружен
      if (this.loadedResources.has(`prefetch:${url}`)) {
        return;
      }
      
      // Создаем элемент link для предзагрузки
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      
      // Добавляем обработчик загрузки
      link.onload = () => {
        // Отмечаем URL как предзагруженный
        this.loadedResources.add(`prefetch:${url}`);
      };
      
      // Добавляем элемент в документ
      document.head.appendChild(link);
    });
  }
  
  /**
   * Добавление ресурса в очередь загрузки
   * @param {string} src - URL ресурса
   * @param {string} type - Тип ресурса (script или style)
   * @param {Object} options - Дополнительные опции
   */
  addResourceToQueue(src, type, options = {}) {
    // Проверяем, был ли ресурс уже добавлен в очередь
    const isInQueue = this.resourceQueue.some(resource => resource.src === src);
    
    if (!isInQueue && !this.loadedResources.has(src)) {
      // Добавляем ресурс в очередь
      this.resourceQueue.push({
        type: type,
        src: src,
        ...options
      });
    }
  }
  
  /**
   * Загрузка ресурса немедленно
   * @param {string} src - URL ресурса
   * @param {string} type - Тип ресурса (script или style)
   * @param {Object} options - Дополнительные опции
   * @returns {Promise} - Promise, который разрешается после загрузки ресурса
   */
  loadResourceImmediately(src, type, options = {}) {
    // Проверяем, был ли ресурс уже загружен
    if (this.loadedResources.has(src)) {
      return Promise.resolve();
    }
    
    return new Promise((resolve, reject) => {
      if (type === 'script') {
        // Создаем элемент script
        const script = document.createElement('script');
        script.src = src;
        if (options.async) script.async = true;
        if (options.defer) script.defer = true;
        
        // Добавляем обработчик загрузки
        script.onload = () => {
          // Отмечаем ресурс как загруженный
          this.loadedResources.add(src);
          resolve();
        };
        
        // Добавляем обработчик ошибки
        script.onerror = () => {
          reject(new Error(`Ошибка загрузки скрипта: ${src}`));
        };
        
        // Добавляем скрипт в документ
        document.body.appendChild(script);
      } else if (type === 'style') {
        // Создаем элемент link
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = src;
        
        // Добавляем обработчик загрузки
        link.onload = () => {
          // Отмечаем ресурс как загруженный
          this.loadedResources.add(src);
          resolve();
        };
        
        // Добавляем обработчик ошибки
        link.onerror = () => {
          reject(new Error(`Ошибка загрузки стиля: ${src}`));
        };
        
        // Добавляем стиль в документ
        document.head.appendChild(link);
      } else {
        reject(new Error(`Неизвестный тип ресурса: ${type}`));
      }
    });
  }
}

// Создаем глобальный экземпляр оптимизатора статических файлов
window.staticOptimizer = new StaticOptimizer();