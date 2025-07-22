"""
Утилиты для тестирования веб-интерфейса на разных устройствах.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import os
from datetime import datetime


# Определение размеров экранов для разных устройств
DEVICE_SIZES = {
    "desktop": {
        "width": 1366,
        "height": 768,
        "device_type": "desktop",
        "description": "Стандартный десктоп (1366x768)"
    },
    "laptop": {
        "width": 1280,
        "height": 800,
        "device_type": "desktop",
        "description": "Ноутбук (1280x800)"
    },
    "tablet_landscape": {
        "width": 1024,
        "height": 768,
        "device_type": "tablet",
        "description": "Планшет в альбомной ориентации (1024x768)"
    },
    "tablet_portrait": {
        "width": 768,
        "height": 1024,
        "device_type": "tablet",
        "description": "Планшет в портретной ориентации (768x1024)"
    },
    "mobile_large": {
        "width": 414,
        "height": 896,
        "device_type": "mobile",
        "description": "Крупный мобильный (iPhone 11 Pro Max)"
    },
    "mobile_medium": {
        "width": 375,
        "height": 667,
        "device_type": "mobile",
        "description": "Средний мобильный (iPhone 8)"
    },
    "mobile_small": {
        "width": 320,
        "height": 568,
        "device_type": "mobile",
        "description": "Маленький мобильный (iPhone SE)"
    }
}


def take_screenshot(browser, device_name, url, output_dir):
    """
    Делает скриншот страницы для указанного устройства.
    
    Args:
        browser: Экземпляр Selenium WebDriver
        device_name (str): Название устройства
        url (str): URL страницы
        output_dir (str): Директория для сохранения скриншотов
        
    Returns:
        str: Путь к сохраненному скриншоту
    """
    # Создаем директорию, если она не существует
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Устанавливаем размер окна браузера
    device = DEVICE_SIZES[device_name]
    browser.set_window_size(device["width"], device["height"])
    
    # Открываем страницу
    browser.get(url)
    
    # Даем странице время на загрузку
    browser.implicitly_wait(5)
    
    # Формируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{device_name}_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    
    # Делаем скриншот
    browser.save_screenshot(filepath)
    
    return filepath


def test_responsive_design(url, output_dir="screenshots", devices=None, headless=True):
    """
    Тестирует отзывчивый дизайн на разных устройствах.
    
    Args:
        url (str): URL для тестирования
        output_dir (str): Директория для сохранения скриншотов
        devices (list): Список устройств для тестирования (по умолчанию все)
        headless (bool): Запускать браузер в безголовом режиме
        
    Returns:
        dict: Результаты тестирования
    """
    # Если устройства не указаны, используем все доступные
    if devices is None:
        devices = list(DEVICE_SIZES.keys())
    
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
    
    results = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "devices": {}
    }
    
    try:
        for device_name in devices:
            if device_name not in DEVICE_SIZES:
                print(f"⚠️ Неизвестное устройство: {device_name}, пропускаем")
                continue
            
            print(f"📱 Тестирование на устройстве: {device_name} ({DEVICE_SIZES[device_name]['description']})")
            
            # Делаем скриншот
            screenshot_path = take_screenshot(browser, device_name, url, output_dir)
            
            # Сохраняем результаты
            results["devices"][device_name] = {
                "size": f"{DEVICE_SIZES[device_name]['width']}x{DEVICE_SIZES[device_name]['height']}",
                "device_type": DEVICE_SIZES[device_name]['device_type'],
                "description": DEVICE_SIZES[device_name]['description'],
                "screenshot": screenshot_path
            }
            
            print(f"✅ Скриншот сохранен: {screenshot_path}")
    
    finally:
        browser.quit()
    
    # Сохраняем результаты в JSON-файл
    results_file = os.path.join(output_dir, f"responsive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Результаты тестирования сохранены в {results_file}")
    
    return results


def generate_html_report(results, output_file=None):
    """
    Генерирует HTML-отчет о тестировании отзывчивого дизайна.
    
    Args:
        results (dict): Результаты тестирования
        output_file (str): Путь для сохранения HTML-отчета
        
    Returns:
        str: Путь к сгенерированному HTML-отчету
    """
    # Если выходной файл не указан, создаем его на основе результатов
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(os.path.dirname(list(results["devices"].values())[0]["screenshot"]), 
                                  f"responsive_test_report_{timestamp}.html")
    
    # Группируем устройства по типу
    devices_by_type = {
        "desktop": [],
        "tablet": [],
        "mobile": []
    }
    
    for device_name, device_data in results["devices"].items():
        device_type = device_data["device_type"]
        devices_by_type[device_type].append({
            "name": device_name,
            "data": device_data
        })
    
    # Генерируем HTML
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет о тестировании отзывчивого дизайна - {results["url"]}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .report-header {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .device-section {{
            margin-bottom: 50px;
        }}
        .device-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        .device-card {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .device-card h3 {{
            margin-top: 0;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .device-info {{
            margin-bottom: 15px;
        }}
        .screenshot {{
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>Отчет о тестировании отзывчивого дизайна</h1>
        <p><strong>URL:</strong> {results["url"]}</p>
        <p><strong>Дата тестирования:</strong> {datetime.fromisoformat(results["timestamp"]).strftime('%d.%m.%Y %H:%M:%S')}</p>
    </div>
    
    <div class="device-section">
        <h2>Десктопные устройства</h2>
        <div class="device-grid">
            {"".join(f'''
            <div class="device-card">
                <h3>{device["name"]}</h3>
                <div class="device-info">
                    <p><strong>Размер:</strong> {device["data"]["size"]}</p>
                    <p><strong>Описание:</strong> {device["data"]["description"]}</p>
                </div>
                <img src="{os.path.basename(device["data"]["screenshot"])}" alt="Скриншот {device["name"]}" class="screenshot">
            </div>
            ''' for device in devices_by_type["desktop"])}
        </div>
    </div>
    
    <div class="device-section">
        <h2>Планшетные устройства</h2>
        <div class="device-grid">
            {"".join(f'''
            <div class="device-card">
                <h3>{device["name"]}</h3>
                <div class="device-info">
                    <p><strong>Размер:</strong> {device["data"]["size"]}</p>
                    <p><strong>Описание:</strong> {device["data"]["description"]}</p>
                </div>
                <img src="{os.path.basename(device["data"]["screenshot"])}" alt="Скриншот {device["name"]}" class="screenshot">
            </div>
            ''' for device in devices_by_type["tablet"])}
        </div>
    </div>
    
    <div class="device-section">
        <h2>Мобильные устройства</h2>
        <div class="device-grid">
            {"".join(f'''
            <div class="device-card">
                <h3>{device["name"]}</h3>
                <div class="device-info">
                    <p><strong>Размер:</strong> {device["data"]["size"]}</p>
                    <p><strong>Описание:</strong> {device["data"]["description"]}</p>
                </div>
                <img src="{os.path.basename(device["data"]["screenshot"])}" alt="Скриншот {device["name"]}" class="screenshot">
            </div>
            ''' for device in devices_by_type["mobile"])}
        </div>
    </div>
    
    <p class="timestamp">Отчет сгенерирован {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
</body>
</html>
"""
    
    # Сохраняем HTML-отчет
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Тестирование отзывчивого дизайна на разных устройствах')
    parser.add_argument('url', help='URL для тестирования')
    parser.add_argument('-o', '--output-dir', default='screenshots', help='Директория для сохранения скриншотов')
    parser.add_argument('-d', '--devices', nargs='+', help='Список устройств для тестирования')
    parser.add_argument('--no-headless', action='store_true', help='Запускать браузер в видимом режиме')
    parser.add_argument('--html', action='store_true', help='Генерировать HTML-отчет')
    parser.add_argument('--html-output', help='Путь к файлу для сохранения HTML-отчета')
    
    args = parser.parse_args()
    
    # Запускаем тестирование
    results = test_responsive_design(
        args.url, 
        args.output_dir, 
        args.devices, 
        not args.no_headless
    )
    
    # Генерируем HTML-отчет, если указан флаг --html
    if args.html:
        html_path = generate_html_report(results, args.html_output)
        print(f"✅ HTML-отчет сохранен в {html_path}")