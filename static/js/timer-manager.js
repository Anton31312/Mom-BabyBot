/**
 * Менеджер таймеров
 * 
 * Централизованное управление всеми таймерами в приложении
 */

class TimerManager {
    constructor() {
        this.activeTimers = new Map();
        this.timerCallbacks = new Map();
        this.storageKey = 'mom_baby_bot_timers';
        
        // Восстанавливаем таймеры из localStorage при загрузке
        this.restoreTimers();
        
        // Сохраняем таймеры при закрытии страницы
        window.addEventListener('beforeunload', () => {
            this.saveTimers();
        });
    }
    
    /**
     * Запускает новый таймер
     * @param {string} timerId - Уникальный ID таймера
     * @param {string} type - Тип таймера (sleep, feeding, contraction, kick)
     * @param {Object} metadata - Дополнительные данные таймера
     */
    startTimer(timerId, type, metadata = {}) {
        const timer = {
            timerId,
            type,
            startTime: Date.now(),
            metadata,
            isActive: true
        };
        
        this.activeTimers.set(timerId, timer);
        this.saveTimers();
        
        // Отправляем событие о запуске таймера
        this.dispatchTimerEvent('timerStarted', timer);
        
        console.log(`Таймер запущен: ${timerId} (${type})`);
    }
    
    /**
     * Останавливает таймер
     * @param {string} timerId - ID таймера для остановки
     */
    stopTimer(timerId) {
        const timer = this.activeTimers.get(timerId);
        if (timer) {
            timer.isActive = false;
            timer.endTime = Date.now();
            
            this.activeTimers.delete(timerId);
            this.saveTimers();
            
            // Отправляем событие об остановке таймера
            this.dispatchTimerEvent('timerStopped', timer);
            
            console.log(`Таймер остановлен: ${timerId}`);
        }
    }
    
    /**
     * Приостанавливает таймер
     * @param {string} timerId - ID таймера
     */
    pauseTimer(timerId) {
        const timer = this.activeTimers.get(timerId);
        if (timer && timer.isActive) {
            timer.isPaused = true;
            timer.pausedAt = Date.now();
            this.saveTimers();
            
            this.dispatchTimerEvent('timerPaused', timer);
        }
    }
    
    /**
     * Возобновляет приостановленный таймер
     * @param {string} timerId - ID таймера
     */
    resumeTimer(timerId) {
        const timer = this.activeTimers.get(timerId);
        if (timer && timer.isPaused) {
            const pauseDuration = Date.now() - timer.pausedAt;
            timer.startTime += pauseDuration;
            timer.isPaused = false;
            delete timer.pausedAt;
            this.saveTimers();
            
            this.dispatchTimerEvent('timerResumed', timer);
        }
    }
    
    /**
     * Получает информацию о таймере
     * @param {string} timerId - ID таймера
     * @returns {Object|null} Информация о таймере
     */
    getTimer(timerId) {
        return this.activeTimers.get(timerId) || null;
    }
    
    /**
     * Получает все активные таймеры
     * @returns {Array} Массив активных таймеров
     */
    getAllActiveTimers() {
        return Array.from(this.activeTimers.values());
    }
    
    /**
     * Получает активные таймеры по типу
     * @param {string} type - Тип таймера
     * @returns {Array} Массив таймеров указанного типа
     */
    getTimersByType(type) {
        return Array.from(this.activeTimers.values()).filter(timer => timer.type === type);
    }
    
    /**
     * Вычисляет прошедшее время для таймера
     * @param {string|number} startTime - Время начала (timestamp или ID таймера)
     * @returns {number} Прошедшее время в секундах
     */
    static getElapsedSeconds(startTime) {
        const start = typeof startTime === 'string' ? 
            this.activeTimers.get(startTime)?.startTime : startTime;
        
        if (!start) return 0;
        
        return Math.floor((Date.now() - start) / 1000);
    }
    
    /**
     * Форматирует время в формат ЧЧ:ММ:СС
     * @param {number} seconds - Время в секундах
     * @returns {string} Отформатированное время
     */
    static formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return [
                hours.toString().padStart(2, '0'),
                minutes.toString().padStart(2, '0'),
                secs.toString().padStart(2, '0')
            ].join(':');
        } else {
            return [
                minutes.toString().padStart(2, '0'),
                secs.toString().padStart(2, '0')
            ].join(':');
        }
    }
    
    /**
     * Сохраняет таймеры в localStorage
     */
    saveTimers() {
        try {
            const timersData = Array.from(this.activeTimers.entries());
            localStorage.setItem(this.storageKey, JSON.stringify(timersData));
        } catch (error) {
            console.error('Ошибка сохранения таймеров:', error);
        }
    }
    
    /**
     * Восстанавливает таймеры из localStorage
     */
    restoreTimers() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved) {
                const timersData = JSON.parse(saved);
                this.activeTimers = new Map(timersData);
                
                // Проверяем, что таймеры еще актуальны (не старше 24 часов)
                const now = Date.now();
                const maxAge = 24 * 60 * 60 * 1000; // 24 часа
                
                for (const [timerId, timer] of this.activeTimers) {
                    if (now - timer.startTime > maxAge) {
                        this.activeTimers.delete(timerId);
                    }
                }
                
                console.log(`Восстановлено ${this.activeTimers.size} активных таймеров`);
            }
        } catch (error) {
            console.error('Ошибка восстановления таймеров:', error);
            this.activeTimers.clear();
        }
    }
    
    /**
     * Отправляет событие таймера
     * @param {string} eventType - Тип события
     * @param {Object} timer - Данные таймера
     */
    dispatchTimerEvent(eventType, timer) {
        const event = new CustomEvent(`timerManager:${eventType}`, {
            detail: timer
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Очищает все таймеры
     */
    clearAllTimers() {
        this.activeTimers.clear();
        this.saveTimers();
        console.log('Все таймеры очищены');
    }
    
    /**
     * Получает статистику таймеров
     * @returns {Object} Статистика
     */
    getStatistics() {
        const timers = Array.from(this.activeTimers.values());
        const stats = {
            total: timers.length,
            byType: {},
            totalRuntime: 0
        };
        
        timers.forEach(timer => {
            // Подсчет по типам
            if (!stats.byType[timer.type]) {
                stats.byType[timer.type] = 0;
            }
            stats.byType[timer.type]++;
            
            // Общее время работы
            const runtime = Date.now() - timer.startTime;
            stats.totalRuntime += runtime;
        });
        
        return stats;
    }
}

// Создаем глобальный экземпляр менеджера таймеров
window.timerManager = new TimerManager();

// Экспортируем класс для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimerManager;
}