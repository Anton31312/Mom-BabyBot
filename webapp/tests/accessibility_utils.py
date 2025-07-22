"""
Утилиты для тестирования доступности веб-интерфейса материнского ухода.
"""

import re
from selenium.webdriver.remote.webelement import WebElement


def parse_color(color_string):
    """
    Преобразует строку цвета CSS в кортеж (r, g, b, a).
    
    Поддерживает форматы:
    - rgb(r, g, b)
    - rgba(r, g, b, a)
    - #RRGGBB
    - #RRGGBBAA
    
    Args:
        color_string (str): Строка с CSS-цветом
        
    Returns:
        tuple: Кортеж (r, g, b, a), где r, g, b в диапазоне 0-255, a в диапазоне 0-1
    """
    # Обработка rgb/rgba формата
    rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_string)
    if rgb_match:
        return (int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3)), 1.0)
    
    rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', color_string)
    if rgba_match:
        return (int(rgba_match.group(1)), int(rgba_match.group(2)), int(rgba_match.group(3)), float(rgba_match.group(4)))
    
    # Обработка hex формата
    hex_match = re.match(r'#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})?', color_string)
    if hex_match:
        r = int(hex_match.group(1), 16)
        g = int(hex_match.group(2), 16)
        b = int(hex_match.group(3), 16)
        a = 1.0
        if hex_match.group(4):
            a = int(hex_match.group(4), 16) / 255
        return (r, g, b, a)
    
    # Обработка сокращенного hex формата
    short_hex_match = re.match(r'#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])', color_string)
    if short_hex_match:
        r = int(short_hex_match.group(1) + short_hex_match.group(1), 16)
        g = int(short_hex_match.group(2) + short_hex_match.group(2), 16)
        b = int(short_hex_match.group(3) + short_hex_match.group(3), 16)
        return (r, g, b, 1.0)
    
    # Если формат не распознан, возвращаем черный цвет
    return (0, 0, 0, 1.0)


def calculate_luminance(r, g, b):
    """
    Вычисляет относительную яркость цвета по формуле WCAG.
    
    Args:
        r (int): Красный компонент (0-255)
        g (int): Зеленый компонент (0-255)
        b (int): Синий компонент (0-255)
        
    Returns:
        float: Относительная яркость в диапазоне 0-1
    """
    # Нормализация значений RGB в диапазон 0-1
    r_srgb = r / 255
    g_srgb = g / 255
    b_srgb = b / 255
    
    # Преобразование в линейное RGB
    r_linear = r_srgb / 12.92 if r_srgb <= 0.03928 else ((r_srgb + 0.055) / 1.055) ** 2.4
    g_linear = g_srgb / 12.92 if g_srgb <= 0.03928 else ((g_srgb + 0.055) / 1.055) ** 2.4
    b_linear = b_srgb / 12.92 if b_srgb <= 0.03928 else ((b_srgb + 0.055) / 1.055) ** 2.4
    
    # Вычисление относительной яркости
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear


def calculate_contrast_ratio(color1, color2):
    """
    Вычисляет коэффициент контрастности между двумя цветами по формуле WCAG.
    
    Args:
        color1 (tuple): Первый цвет в формате (r, g, b, a)
        color2 (tuple): Второй цвет в формате (r, g, b, a)
        
    Returns:
        float: Коэффициент контрастности (от 1 до 21)
    """
    # Вычисляем яркость для каждого цвета
    l1 = calculate_luminance(color1[0], color1[1], color1[2])
    l2 = calculate_luminance(color2[0], color2[1], color2[2])
    
    # Определяем светлый и темный цвета
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    # Вычисляем коэффициент контрастности
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast_ratio(element, min_ratio=4.5):
    """
    Проверяет, соответствует ли контрастность элемента минимальному требуемому соотношению.
    
    Args:
        element (WebElement): Элемент для проверки
        min_ratio (float): Минимальное требуемое соотношение контрастности
        
    Returns:
        tuple: (bool, float) - соответствует ли требованиям и фактический коэффициент
    """
    # Получаем цвета текста и фона
    text_color = element.value_of_css_property("color")
    background_color = element.value_of_css_property("background-color")
    
    # Преобразуем строки цветов в кортежи (r, g, b, a)
    text_rgba = parse_color(text_color)
    bg_rgba = parse_color(background_color)
    
    # Вычисляем коэффициент контрастности
    ratio = calculate_contrast_ratio(text_rgba, bg_rgba)
    
    # Проверяем, соответствует ли требованиям
    return (ratio >= min_ratio, ratio)


def check_semantic_structure(browser):
    """
    Проверяет семантическую структуру страницы.
    
    Args:
        browser: Экземпляр Selenium WebDriver
        
    Returns:
        dict: Словарь с результатами проверки
    """
    results = {
        'has_header': len(browser.find_elements_by_tag_name('header')) > 0,
        'has_nav': len(browser.find_elements_by_tag_name('nav')) > 0,
        'has_main': len(browser.find_elements_by_tag_name('main')) > 0,
        'has_footer': len(browser.find_elements_by_tag_name('footer')) > 0,
        'has_headings': len(browser.find_elements_by_css_selector('h1, h2, h3, h4, h5, h6')) > 0,
        'has_landmarks': len(browser.find_elements_by_css_selector('main, nav, aside, article, section')) > 0
    }
    
    return results


def check_form_accessibility(browser):
    """
    Проверяет доступность форм на странице.
    
    Args:
        browser: Экземпляр Selenium WebDriver
        
    Returns:
        dict: Словарь с результатами проверки
    """
    results = {
        'inputs_with_labels': 0,
        'inputs_without_labels': 0,
        'inputs_with_aria': 0,
        'inputs_total': 0
    }
    
    # Находим все поля ввода
    inputs = browser.find_elements_by_css_selector('input:not([type="hidden"]), select, textarea')
    results['inputs_total'] = len(inputs)
    
    for input_field in inputs:
        input_id = input_field.get_attribute('id')
        has_label = False
        has_aria = False
        
        # Проверяем наличие связанной метки
        if input_id:
            labels = browser.find_elements_by_css_selector(f'label[for="{input_id}"]')
            if labels:
                has_label = True
                results['inputs_with_labels'] += 1
        
        # Проверяем наличие ARIA-атрибутов
        if input_field.get_attribute('aria-label') or input_field.get_attribute('aria-labelledby'):
            has_aria = True
            results['inputs_with_aria'] += 1
        
        if not has_label and not has_aria:
            results['inputs_without_labels'] += 1
    
    return results


def check_keyboard_navigation(browser):
    """
    Проверяет возможность навигации с клавиатуры.
    
    Args:
        browser: Экземпляр Selenium WebDriver
        
    Returns:
        dict: Словарь с результатами проверки
    """
    results = {
        'focusable_elements': 0,
        'tab_index_negative': 0,
        'tab_index_positive': 0
    }
    
    # Находим все потенциально фокусируемые элементы
    focusable_elements = browser.find_elements_by_css_selector(
        'a, button, input, select, textarea, [tabindex]'
    )
    results['focusable_elements'] = len(focusable_elements)
    
    for element in focusable_elements:
        tab_index = element.get_attribute('tabindex')
        if tab_index:
            tab_index = int(tab_index)
            if tab_index < 0:
                results['tab_index_negative'] += 1
            elif tab_index > 0:
                results['tab_index_positive'] += 1
    
    return results


def generate_accessibility_report(browser):
    """
    Генерирует отчет о доступности страницы.
    
    Args:
        browser: Экземпляр Selenium WebDriver
        
    Returns:
        dict: Словарь с результатами проверки
    """
    report = {
        'semantic_structure': check_semantic_structure(browser),
        'form_accessibility': check_form_accessibility(browser),
        'keyboard_navigation': check_keyboard_navigation(browser),
        'contrast_issues': []
    }
    
    # Проверяем контрастность для основных текстовых элементов
    text_elements = browser.find_elements_by_css_selector('p, h1, h2, h3, h4, h5, h6, a, button, label, input, select, textarea')
    
    for element in text_elements:
        try:
            passes, ratio = check_contrast_ratio(element)
            if not passes:
                report['contrast_issues'].append({
                    'element': element.tag_name,
                    'text': element.text[:50] + ('...' if len(element.text) > 50 else ''),
                    'contrast_ratio': ratio
                })
        except Exception:
            # Пропускаем элементы, для которых не удалось проверить контрастность
            pass
    
    return report