#!/usr/bin/env python
"""
Скрипт для генерации отчета о доступности веб-интерфейса материнского ухода.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import django
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Добавляем корень проекта в путь Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')

# Инициализируем Django
django.setup()

from webapp.tests.accessibility_utils import generate_accessibility_report
from webapp.tests.generate_html_report import generate_html_report


def run_accessibility_check(url, output_file=None, headless=True):
    """
    Запускает проверку доступности для указанного URL.
    
    Args:
        url (str): URL для проверки
        output_file (str, optional): Путь к файлу для сохранения отчета
        headless (bool): Запускать браузер в безголовом режиме
    
    Returns:
        dict: Отчет о доступности
    """
    print(f"🔍 Проверка доступности для {url}")
    
    # Настройка Chrome WebDriver
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Создаем экземпляр WebDriver
    try:
        browser = webdriver.Chrome(options=chrome_options)
    except Exception:
        # Если Chrome не доступен, пробуем Firefox
        firefox_options = webdriver.FirefoxOptions()
        if headless:
            firefox_options.add_argument("--headless")
        browser = webdriver.Firefox(options=firefox_options)
    
    try:
        # Открываем страницу
        browser.get(url)
        
        # Генерируем отчет
        report = generate_accessibility_report(browser)
        
        # Добавляем метаданные
        report['metadata'] = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'user_agent': browser.execute_script("return navigator.userAgent;")
        }
        
        # Сохраняем отчет в файл, если указан
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ Отчет сохранен в {output_file}")
        
        # Выводим краткую сводку
        print("\n📊 Краткая сводка:")
        print(f"- Семантическая структура: {'✅ Хорошо' if all(report['semantic_structure'].values()) else '⚠️ Требует улучшения'}")
        print(f"- Доступность форм: {'✅ Хорошо' if report['form_accessibility']['inputs_without_labels'] == 0 else '⚠️ Требует улучшения'}")
        print(f"- Навигация с клавиатуры: {'✅ Хорошо' if report['keyboard_navigation']['tab_index_positive'] == 0 else '⚠️ Требует улучшения'}")
        print(f"- Проблемы с контрастностью: {len(report['contrast_issues'])}")
        
        return report
    
    finally:
        browser.quit()


def main():
    """Основная функция скрипта."""
    parser = argparse.ArgumentParser(description='Генерация отчета о доступности веб-интерфейса')
    parser.add_argument('url', help='URL для проверки')
    parser.add_argument('-o', '--output', help='Путь к файлу для сохранения JSON-отчета')
    parser.add_argument('--html', action='store_true', help='Генерировать HTML-отчет')
    parser.add_argument('--html-output', help='Путь к файлу для сохранения HTML-отчета')
    parser.add_argument('--no-headless', action='store_true', help='Запускать браузер в видимом режиме')
    
    args = parser.parse_args()
    
    # Если выходной файл не указан, создаем имя по умолчанию
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'accessibility_report_{timestamp}.json'
    
    # Запускаем проверку доступности
    run_accessibility_check(args.url, args.output, not args.no_headless)
    
    # Генерируем HTML-отчет, если указан флаг --html
    if args.html:
        html_output = args.html_output
        if not html_output:
            # Если путь для HTML-отчета не указан, создаем его на основе JSON-отчета
            html_output = os.path.splitext(args.output)[0] + '.html'
        
        # Генерируем HTML-отчет
        html_path = generate_html_report(args.output, html_output)
        print(f"✅ HTML-отчет сохранен в {html_path}")


if __name__ == "__main__":
    main()