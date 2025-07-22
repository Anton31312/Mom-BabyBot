#!/usr/bin/env python
"""
Скрипт для запуска комплексного UI-тестирования веб-интерфейса материнского ухода.
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Добавляем корень проекта в путь Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_all_ui_tests(server_url, output_dir, run_unit_tests=True, run_responsive_tests=True, run_accessibility_tests=True):
    """
    Запускает все UI-тесты и генерирует отчеты.
    
    Args:
        server_url (str): URL тестового сервера
        output_dir (str): Директория для сохранения отчетов
        run_unit_tests (bool): Запускать модульные UI-тесты
        run_responsive_tests (bool): Запускать тесты отзывчивого дизайна
        run_accessibility_tests (bool): Запускать тесты доступности
    """
    # Создаем директорию для отчетов, если она не существует
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "timestamp": timestamp,
        "server_url": server_url,
        "tests_run": {
            "unit_tests": run_unit_tests,
            "responsive_tests": run_responsive_tests,
            "accessibility_tests": run_accessibility_tests
        },
        "results": {}
    }
    
    # 1. Запускаем модульные UI-тесты
    if run_unit_tests:
        print("\n🚀 Запуск модульных UI-тестов...")
        unit_test_output = os.path.join(output_dir, f"unit_test_results_{timestamp}.txt")
        
        try:
            with open(unit_test_output, 'w') as f:
                process = subprocess.run(
                    ["python", "run_ui_tests.py"],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            results["results"]["unit_tests"] = {
                "success": process.returncode == 0,
                "output_file": unit_test_output
            }
            
            print(f"✅ Результаты модульных UI-тестов сохранены в {unit_test_output}")
            print(f"{'✅ Все тесты пройдены успешно' if process.returncode == 0 else '⚠️ Некоторые тесты не пройдены'}")
        
        except Exception as e:
            print(f"❌ Ошибка при запуске модульных UI-тестов: {e}")
            results["results"]["unit_tests"] = {
                "success": False,
                "error": str(e)
            }
    
    # 2. Запускаем тесты отзывчивого дизайна
    if run_responsive_tests:
        print("\n🚀 Запуск тестов отзывчивого дизайна...")
        responsive_output_dir = os.path.join(output_dir, f"responsive_tests_{timestamp}")
        
        try:
            # Импортируем функцию для тестирования отзывчивого дизайна
            from webapp.tests.device_testing import test_responsive_design, generate_html_report
            
            # Запускаем тестирование
            responsive_results = test_responsive_design(
                server_url,
                responsive_output_dir
            )
            
            # Генерируем HTML-отчет
            html_report = generate_html_report(
                responsive_results,
                os.path.join(responsive_output_dir, "responsive_report.html")
            )
            
            results["results"]["responsive_tests"] = {
                "success": True,
                "output_dir": responsive_output_dir,
                "html_report": html_report
            }
            
            print(f"✅ Результаты тестов отзывчивого дизайна сохранены в {responsive_output_dir}")
            print(f"✅ HTML-отчет сохранен в {html_report}")
        
        except Exception as e:
            print(f"❌ Ошибка при запуске тестов отзывчивого дизайна: {e}")
            results["results"]["responsive_tests"] = {
                "success": False,
                "error": str(e)
            }
    
    # 3. Запускаем тесты доступности
    if run_accessibility_tests:
        print("\n🚀 Запуск тестов доступности...")
        accessibility_output = os.path.join(output_dir, f"accessibility_report_{timestamp}.json")
        accessibility_html = os.path.join(output_dir, f"accessibility_report_{timestamp}.html")
        
        try:
            process = subprocess.run(
                [
                    "python", "generate_accessibility_report.py",
                    server_url,
                    "--output", accessibility_output,
                    "--html"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            results["results"]["accessibility_tests"] = {
                "success": process.returncode == 0,
                "output_file": accessibility_output,
                "html_report": accessibility_html,
                "command_output": process.stdout
            }
            
            print(f"✅ Отчет о доступности сохранен в {accessibility_output}")
            print(f"✅ HTML-отчет о доступности сохранен в {accessibility_html}")
        
        except Exception as e:
            print(f"❌ Ошибка при запуске тестов доступности: {e}")
            results["results"]["accessibility_tests"] = {
                "success": False,
                "error": str(e)
            }
    
    # Сохраняем общий отчет
    summary_file = os.path.join(output_dir, f"ui_testing_summary_{timestamp}.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Отчет о комплексном UI-тестировании\n")
        f.write(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write(f"URL: {server_url}\n\n")
        
        f.write("Результаты тестирования:\n")
        
        if run_unit_tests:
            unit_result = results["results"].get("unit_tests", {})
            f.write(f"1. Модульные UI-тесты: {'✅ Успешно' if unit_result.get('success', False) else '❌ Неудачно'}\n")
            if "output_file" in unit_result:
                f.write(f"   Отчет: {unit_result['output_file']}\n")
        
        if run_responsive_tests:
            responsive_result = results["results"].get("responsive_tests", {})
            f.write(f"2. Тесты отзывчивого дизайна: {'✅ Успешно' if responsive_result.get('success', False) else '❌ Неудачно'}\n")
            if "output_dir" in responsive_result:
                f.write(f"   Директория с результатами: {responsive_result['output_dir']}\n")
            if "html_report" in responsive_result:
                f.write(f"   HTML-отчет: {responsive_result['html_report']}\n")
        
        if run_accessibility_tests:
            accessibility_result = results["results"].get("accessibility_tests", {})
            f.write(f"3. Тесты доступности: {'✅ Успешно' if accessibility_result.get('success', False) else '❌ Неудачно'}\n")
            if "output_file" in accessibility_result:
                f.write(f"   JSON-отчет: {accessibility_result['output_file']}\n")
            if "html_report" in accessibility_result:
                f.write(f"   HTML-отчет: {accessibility_result['html_report']}\n")
    
    print(f"\n📊 Общий отчет о тестировании сохранен в {summary_file}")
    
    # Определяем общий результат тестирования
    all_success = all(
        results["results"].get(test, {}).get("success", False)
        for test in ["unit_tests", "responsive_tests", "accessibility_tests"]
        if results["tests_run"].get(test, False)
    )
    
    if all_success:
        print("\n🎉 Все тесты пройдены успешно!")
    else:
        print("\n⚠️ Некоторые тесты не пройдены. Проверьте отчеты для получения подробной информации.")
    
    return all_success


def main():
    """Основная функция скрипта."""
    parser = argparse.ArgumentParser(description='Запуск комплексного UI-тестирования')
    parser.add_argument('--server-url', default='http://localhost:8000', help='URL тестового сервера')
    parser.add_argument('--output-dir', default='ui_test_reports', help='Директория для сохранения отчетов')
    parser.add_argument('--skip-unit-tests', action='store_true', help='Пропустить модульные UI-тесты')
    parser.add_argument('--skip-responsive-tests', action='store_true', help='Пропустить тесты отзывчивого дизайна')
    parser.add_argument('--skip-accessibility-tests', action='store_true', help='Пропустить тесты доступности')
    
    args = parser.parse_args()
    
    success = run_all_ui_tests(
        args.server_url,
        args.output_dir,
        not args.skip_unit_tests,
        not args.skip_responsive_tests,
        not args.skip_accessibility_tests
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()