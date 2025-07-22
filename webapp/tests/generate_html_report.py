"""
Генератор HTML-отчетов о доступности веб-интерфейса материнского ухода.
"""

import json
import os
from datetime import datetime


def generate_html_report(json_report_path, output_path=None):
    """
    Генерирует HTML-отчет на основе JSON-отчета о доступности.

    Args:
        json_report_path (str): Путь к JSON-файлу с отчетом
        output_path (str, optional): Путь для сохранения HTML-отчета

    Returns:
        str: Путь к сгенерированному HTML-отчету
    """
    # Загружаем JSON-отчет
    with open(json_report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    # Если выходной путь не указан, создаем его на основе входного
    if not output_path:
        base_name = os.path.splitext(json_report_path)[0]
        output_path = f"{base_name}.html"

    # Генерируем HTML
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет о доступности - {report['metadata']['url']}</title>
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
        .report-section {{
            margin-bottom: 30px;
            padding: 20px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .success {{
            color: #28a745;
        }}
        .warning {{
            color: #ffc107;
        }}
        .danger {{
            color: #dc3545;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
        .progress-bar {{
            height: 20px;
            background-color: #e9ecef;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        .progress {{
            height: 100%;
            border-radius: 5px;
            background-color: #4caf50;
        }}
        .summary-box {{
            display: inline-block;
            width: 30%;
            margin: 1%;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .summary-box h3 {{
            margin-top: 0;
        }}
        .good {{
            background-color: #d4edda;
        }}
        .needs-improvement {{
            background-color: #fff3cd;
        }}
        .bad {{
            background-color: #f8d7da;
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>Отчет о доступности веб-интерфейса</h1>
        <p><strong>URL:</strong> {report['metadata']['url']}</p>
        <p><strong>Дата проверки:</strong> {datetime.fromisoformat(report['metadata']['timestamp']).strftime('%d.%m.%Y %H:%M:%S')}</p>
        <p><strong>User Agent:</strong> {report['metadata']['user_agent']}</p>
    </div>
    
    <div class="report-section">
        <h2>Сводка</h2>
        <div class="summary-box {'good' if all(report['semantic_structure'].values()) else 'needs-improvement'}">
            <h3>Семантическая структура</h3>
            <p class="{'success' if all(report['semantic_structure'].values()) else 'warning'}">
                {'✓ Хорошо' if all(report['semantic_structure'].values()) else '⚠ Требует улучшения'}
            </p>
        </div>
        <div class="summary-box {'good' if report['form_accessibility']['inputs_without_labels'] == 0 else 'needs-improvement'}">
            <h3>Доступность форм</h3>
            <p class="{'success' if report['form_accessibility']['inputs_without_labels'] == 0 else 'warning'}">
                {'✓ Хорошо' if report['form_accessibility']['inputs_without_labels'] == 0 else '⚠ Требует улучшения'}
            </p>
        </div>
        <div class="summary-box {'good' if report['keyboard_navigation']['tab_index_positive'] == 0 else 'needs-improvement'}">
            <h3>Навигация с клавиатуры</h3>
            <p class="{'success' if report['keyboard_navigation']['tab_index_positive'] == 0 else 'warning'}">
                {'✓ Хорошо' if report['keyboard_navigation']['tab_index_positive'] == 0 else '⚠ Требует улучшения'}
            </p>
        </div>
        <div class="summary-box {'good' if len(report['contrast_issues']) == 0 else ('needs-improvement' if len(report['contrast_issues']) < 5 else 'bad')}">
            <h3>Контрастность</h3>
            <p class="{'success' if len(report['contrast_issues']) == 0 else ('warning' if len(report['contrast_issues']) < 5 else 'danger')}">
                {'✓ Хорошо' if len(report['contrast_issues']) == 0 else f'⚠ Найдено проблем: {len(report["contrast_issues"])}'}
            </p>
        </div>
    </div>
    
    <div class="report-section">
        <h2>Семантическая структура</h2>
        <table>
            <tr>
                <th>Элемент</th>
                <th>Статус</th>
            </tr>
            <tr>
                <td>Header</td>
                <td class="{'success' if report['semantic_structure']['has_header'] else 'danger'}">
                    {'✓ Присутствует' if report['semantic_structure']['has_header'] else '✗ Отсутствует'}
                </td>
            </tr>
            <tr>
                <td>Navigation</td>
                <td class="{'success' if report['semantic_structure']['has_nav'] else 'danger'}">
                    {'✓ Присутствует' if report['semantic_structure']['has_nav'] else '✗ Отсутствует'}
                </td>
            </tr>
            <tr>
                <td>Main</td>
                <td class="{'success' if report['semantic_structure']['has_main'] else 'danger'}">
                    {'✓ Присутствует' if report['semantic_structure']['has_main'] else '✗ Отсутствует'}
                </td>
            </tr>
            <tr>
                <td>Footer</td>
                <td class="{'success' if report['semantic_structure']['has_footer'] else 'danger'}">
                    {'✓ Присутствует' if report['semantic_structure']['has_footer'] else '✗ Отсутствует'}
                </td>
            </tr>
            <tr>
                <td>Headings</td>
                <td class="{'success' if report['semantic_structure']['has_headings'] else 'danger'}">
                    {'✓ Присутствуют' if report['semantic_structure']['has_headings'] else '✗ Отсутствуют'}
                </td>
            </tr>
            <tr>
                <td>Landmarks</td>
                <td class="{'success' if report['semantic_structure']['has_landmarks'] else 'danger'}">
                    {'✓ Присутствуют' if report['semantic_structure']['has_landmarks'] else '✗ Отсутствуют'}
                </td>
            </tr>
        </table>
    </div>
    
    <div class="report-section">
        <h2>Доступность форм</h2>
        <p>Всего полей ввода: {report['form_accessibility']['inputs_total']}</p>
        
        <h3>Поля с метками</h3>
        <div class="progress-bar">
            <div class="progress" style="width: {100 * report['form_accessibility']['inputs_with_labels'] / max(1, report['form_accessibility']['inputs_total'])}%;"></div>
        </div>
        <p>{report['form_accessibility']['inputs_with_labels']} из {report['form_accessibility']['inputs_total']} ({100 * report['form_accessibility']['inputs_with_labels'] / max(1, report['form_accessibility']['inputs_total']):.1f}%)</p>
        
        <h3>Поля с ARIA-атрибутами</h3>
        <div class="progress-bar">
            <div class="progress" style="width: {100 * report['form_accessibility']['inputs_with_aria'] / max(1, report['form_accessibility']['inputs_total'])}%;"></div>
        </div>
        <p>{report['form_accessibility']['inputs_with_aria']} из {report['form_accessibility']['inputs_total']} ({100 * report['form_accessibility']['inputs_with_aria'] / max(1, report['form_accessibility']['inputs_total']):.1f}%)</p>
        
        <h3>Поля без меток и ARIA-атрибутов</h3>
        <div class="progress-bar">
            <div class="progress" style="width: {100 * report['form_accessibility']['inputs_without_labels'] / max(1, report['form_accessibility']['inputs_total'])}%; background-color: {'#dc3545' if report['form_accessibility']['inputs_without_labels'] > 0 else '#4caf50'};"></div>
        </div>
        <p class="{'danger' if report['form_accessibility']['inputs_without_labels'] > 0 else 'success'}">
            {report['form_accessibility']['inputs_without_labels']} из {report['form_accessibility']['inputs_total']} ({100 * report['form_accessibility']['inputs_without_labels'] / max(1, report['form_accessibility']['inputs_total']):.1f}%)
        </p>
    </div>
    
    <div class="report-section">
        <h2>Навигация с клавиатуры</h2>
        <p>Всего фокусируемых элементов: {report['keyboard_navigation']['focusable_elements']}</p>
        
        <h3>Элементы с отрицательным tabindex</h3>
        <p class="{'warning' if report['keyboard_navigation']['tab_index_negative'] > 0 else 'success'}">
            {report['keyboard_navigation']['tab_index_negative']} элементов
            {' (эти элементы не будут доступны при навигации с клавиатуры)' if report['keyboard_navigation']['tab_index_negative'] > 0 else ''}
        </p>
        
        <h3>Элементы с положительным tabindex</h3>
        <p class="{'warning' if report['keyboard_navigation']['tab_index_positive'] > 0 else 'success'}">
            {report['keyboard_navigation']['tab_index_positive']} элементов
            {' (эти элементы нарушают естественный порядок навигации)' if report['keyboard_navigation']['tab_index_positive'] > 0 else ''}
        </p>
    </div>
    
    <div class="report-section">
        <h2>Проблемы с контрастностью</h2>
        {f"<p class='success'>Проблем с контрастностью не обнаружено.</p>" if len(report['contrast_issues']) == 0 else ""}
        {f"<p>Обнаружено {len(report['contrast_issues'])} проблем с контрастностью:</p>" if len(report['contrast_issues']) > 0 else ""}
        
        {"<table><tr><th>Элемент</th><th>Текст</th><th>Коэффициент контрастности</th><th>Статус</th></tr>" + "".join(
            "<tr><td>" + issue['element'] + "</td><td>" + issue['text'] + "</td><td>" + f"{issue['contrast_ratio']:.2f}" + "</td><td class='" + ("danger" if issue['contrast_ratio'] < 3 else "warning") + "'>" + ("Очень низкий" if issue['contrast_ratio'] < 3 else "Недостаточный") + "</td></tr>"
            for issue in report['contrast_issues']
        ) + "</table>" if len(report['contrast_issues']) > 0 else ""}
    </div>
    
    <div class="report-footer">
        <p>Отчет сгенерирован {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
    </div>
</body>
</html>
"""

    # Сохраняем HTML-отчет
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Использование: python generate_html_report.py <путь_к_json_отчету> [путь_для_сохранения_html]")
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    html_path = generate_html_report(json_path, output_path)
    print(f"HTML-отчет сохранен в {html_path}")
