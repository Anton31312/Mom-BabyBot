/**
 * Tooltips.js - Система подсказок для интерфейса Mom&BabyBot
 * 
 * Этот скрипт добавляет всплывающие подсказки к элементам интерфейса,
 * помеченным атрибутом data-tooltip.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация подсказок
    initTooltips();
    
    // Добавление обработчика для динамически добавленных элементов
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                initTooltips();
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
});

/**
 * Инициализирует подсказки для всех элементов с атрибутом data-tooltip
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        if (element.getAttribute('data-tooltip-initialized') === 'true') {
            return;
        }
        
        element.setAttribute('data-tooltip-initialized', 'true');
        
        // Создаем элемент подсказки
        const tooltipContent = element.getAttribute('data-tooltip');
        const tooltipPosition = element.getAttribute('data-tooltip-position') || 'top';
        
        element.addEventListener('mouseenter', function(e) {
            showTooltip(element, tooltipContent, tooltipPosition);
        });
        
        element.addEventListener('mouseleave', function(e) {
            hideTooltip();
        });
        
        // Для мобильных устройств
        element.addEventListener('touchstart', function(e) {
            e.preventDefault();
            showTooltip(element, tooltipContent, tooltipPosition);
            
            // Скрываем подсказку при касании в другом месте
            const hideOnTouch = function(e) {
                if (!element.contains(e.target)) {
                    hideTooltip();
                    document.removeEventListener('touchstart', hideOnTouch);
                }
            };
            
            setTimeout(() => {
                document.addEventListener('touchstart', hideOnTouch);
            }, 10);
        });
    });
}

/**
 * Показывает подсказку для указанного элемента
 */
function showTooltip(element, content, position) {
    // Удаляем существующую подсказку, если есть
    hideTooltip();
    
    // Создаем элемент подсказки
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip glassmorphic-card';
    tooltip.id = 'active-tooltip';
    tooltip.innerHTML = content;
    
    // Добавляем подсказку в DOM
    document.body.appendChild(tooltip);
    
    // Позиционируем подсказку
    positionTooltip(tooltip, element, position);
    
    // Анимация появления
    setTimeout(() => {
        tooltip.classList.add('tooltip-visible');
    }, 10);
}

/**
 * Скрывает активную подсказку
 */
function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.classList.remove('tooltip-visible');
        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
            }
        }, 200);
    }
}

/**
 * Позиционирует подсказку относительно элемента
 */
function positionTooltip(tooltip, element, position) {
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let top, left;
    
    switch (position) {
        case 'top':
            top = rect.top - tooltipRect.height - 10;
            left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
            break;
        case 'bottom':
            top = rect.bottom + 10;
            left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
            break;
        case 'left':
            top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
            left = rect.left - tooltipRect.width - 10;
            break;
        case 'right':
            top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
            left = rect.right + 10;
            break;
    }
    
    // Проверяем, не выходит ли подсказка за пределы экрана
    if (left < 10) left = 10;
    if (left + tooltipRect.width > window.innerWidth - 10) {
        left = window.innerWidth - tooltipRect.width - 10;
    }
    
    if (top < 10) {
        // Если подсказка выходит за верхний край, показываем её снизу
        if (position === 'top') {
            top = rect.bottom + 10;
        } else {
            top = 10;
        }
    }
    
    if (top + tooltipRect.height > window.innerHeight - 10) {
        // Если подсказка выходит за нижний край, показываем её сверху
        if (position === 'bottom') {
            top = rect.top - tooltipRect.height - 10;
        } else {
            top = window.innerHeight - tooltipRect.height - 10;
        }
    }
    
    tooltip.style.top = `${top + window.scrollY}px`;
    tooltip.style.left = `${left + window.scrollX}px`;
    
    // Добавляем стрелку
    tooltip.setAttribute('data-position', position);
}