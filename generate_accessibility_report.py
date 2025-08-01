#!/usr/bin/env python
"""
Скрипт для генерации отчета о доступности приложения.

Этот скрипт:
1. Сканирует все HTML шаблоны на предмет проблем доступности
2. Проверяет распространенные проблемы доступности
3. Генерирует подробный отчет с рекомендациями
"""

import os
import sys
import re
import argparse
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Проверка установки необходимых пакетов
try:
    from bs4 import BeautifulSoup
    import colorama
    from colorama import Fore, Style
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4", "colorama"])
    from bs4 import BeautifulSoup
    import colorama
    from colorama import Fore, Style

# Инициализация colorama
colorama.init()

# Настройка путей
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "webapp" / "templates"
REPORTS_DIR = BASE_DIR / "accessibility_reports"

# Создание директории для отчетов, если она не существует
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Проверки доступности
class AccessibilityChecker:
    def __init__(self):
        self.issues = []
    
    def check_file(self, file_path):
        """Проверка одного файла на проблемы доступности."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсинг HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Получение относительного пути для отчета
            rel_path = file_path.relative_to(BASE_DIR)
            
            # Запуск проверок
            self._check_images_alt(soup, rel_path)
            self._check_form_labels(soup, rel_path)
            self._check_heading_hierarchy(soup, rel_path)
            self._check_color_contrast(soup, rel_path)
            self._check_aria_attributes(soup, rel_path)
            self._check_language(soup, rel_path)
            self._check_document_title(soup, rel_path)
            self._check_links(soup, rel_path)
            self._check_tables(soup, rel_path)
            
            return len(self.issues)
        except Exception as e:
            self.issues.append({
                'file': str(rel_path),
                'type': 'error',
                'description': f"Error processing file: {str(e)}",
                'line': 0,
                'column': 0,
                'severity': 'high',
                'recommendation': 'Fix the file syntax or encoding issues.'
            })
            return 1
    
    def _check_images_alt(self, soup, file_path):
        """Проверка наличия alt атрибутов у всех изображений."""
        images = soup.find_all('img')
        for img in images:
            if not img.has_attr('alt'):
                self._add_issue(file_path, 'missing-alt', 
                               f"Image without alt attribute: {img}", 
                               self._get_line_number(img), 
                               'high',
                               'Add an alt attribute to describe the image or use alt="" for decorative images.')
    
    def _check_form_labels(self, soup, file_path):
        """Проверка наличия связанных меток у всех элементов форм."""
        inputs = soup.find_all(['input', 'select', 'textarea'])
        for input_elem in inputs:
            # Пропускаем скрытые поля ввода и кнопки
            if input_elem.has_attr('type') and input_elem['type'] in ['hidden', 'submit', 'button', 'reset']:
                continue
            
            # Проверка наличия атрибута id
            if not input_elem.has_attr('id'):
                self._add_issue(file_path, 'missing-label', 
                               f"Form control without id attribute: {input_elem}", 
                               self._get_line_number(input_elem), 
                               'medium',
                               'Add an id attribute to the input and a corresponding label element.')
                continue
            
            # Проверка наличия связанной метки
            input_id = input_elem['id']
            label = soup.find('label', attrs={'for': input_id})
            if not label:
                self._add_issue(file_path, 'missing-label', 
                               f"No label found for input with id '{input_id}'", 
                               self._get_line_number(input_elem), 
                               'medium',
                               f"Add a label element with for='{input_id}' attribute.")
    
    def _check_heading_hierarchy(self, soup, file_path):
        """Проверка правильной иерархии заголовков."""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            return
        
        # Проверка существования h1
        if not soup.find('h1'):
            self._add_issue(file_path, 'missing-h1', 
                           "No h1 heading found in the document", 
                           0, 
                           'medium',
                           'Add an h1 heading as the main title of the page.')
        
        # Проверка порядка заголовков
        current_level = 0
        for heading in headings:
            level = int(heading.name[1])
            
            # Первый заголовок должен быть h1
            if current_level == 0 and level != 1:
                self._add_issue(file_path, 'wrong-heading-order', 
                               f"First heading is {heading.name} instead of h1", 
                               self._get_line_number(heading), 
                               'medium',
                               'Start with an h1 heading as the main title of the page.')
            
            # Уровни заголовков не должны пропускаться
            elif current_level > 0 and level > current_level + 1:
                self._add_issue(file_path, 'skipped-heading-level', 
                               f"Heading level skipped from h{current_level} to {heading.name}", 
                               self._get_line_number(heading), 
                               'low',
                               f"Use h{current_level + 1} instead of {heading.name} to maintain hierarchy.")
            
            current_level = level
    
    def _check_color_contrast(self, soup, file_path):
        """Проверка потенциальных проблем с контрастностью цветов (базовая проверка)."""
        # Поиск встроенных стилей с определениями цветов
        elements_with_style = soup.find_all(style=True)
        for elem in elements_with_style:
            style = elem['style']
            if 'color' in style.lower() and 'background' in style.lower():
                self._add_issue(file_path, 'potential-contrast-issue', 
                               f"Element with inline color and background styles: {elem}", 
                               self._get_line_number(elem), 
                               'low',
                               'Ensure sufficient color contrast (4.5:1 for normal text, 3:1 for large text).')
    
    def _check_aria_attributes(self, soup, file_path):
        """Проверка правильности ARIA атрибутов."""
        # Проверка aria-* атрибутов
        elements_with_aria = soup.find_all(lambda tag: any(attr.startswith('aria-') for attr in tag.attrs))
        for elem in elements_with_aria:
            # Проверка aria-hidden="true" на фокусируемых элементах
            if elem.has_attr('aria-hidden') and elem['aria-hidden'] == 'true':
                if elem.name in ['a', 'button', 'input', 'select', 'textarea'] or elem.has_attr('tabindex'):
                    self._add_issue(file_path, 'aria-hidden-focusable', 
                                   f"Focusable element with aria-hidden='true': {elem}", 
                                   self._get_line_number(elem), 
                                   'high',
                                   'Remove aria-hidden from focusable elements or make them non-focusable.')
    
    def _check_language(self, soup, file_path):
        """Проверка наличия атрибута языка в документе."""
        html = soup.find('html')
        if html and not html.has_attr('lang'):
            self._add_issue(file_path, 'missing-lang', 
                           "HTML element missing lang attribute", 
                           self._get_line_number(html), 
                           'medium',
                           'Add a lang attribute to the html element, e.g., <html lang="en">.')
    
    def _check_document_title(self, soup, file_path):
        """Проверка наличия заголовка документа."""
        if not soup.find('title'):
            self._add_issue(file_path, 'missing-title', 
                           "Document missing title element", 
                           0, 
                           'medium',
                           'Add a descriptive title element within the head section.')
    
    def _check_links(self, soup, file_path):
        """Проверка ссылок на проблемы доступности."""
        links = soup.find_all('a')
        for link in links:
            # Проверка пустых ссылок
            if not link.get_text(strip=True) and not link.find('img'):
                self._add_issue(file_path, 'empty-link', 
                               f"Link without text content: {link}", 
                               self._get_line_number(link), 
                               'high',
                               'Add text content to the link or an image with alt text.')
            
            # Проверка общего текста ссылок
            text = link.get_text(strip=True).lower()
            if text in ['click here', 'here', 'more', 'read more', 'link']:
                self._add_issue(file_path, 'generic-link-text', 
                               f"Link with generic text: '{text}'", 
                               self._get_line_number(link), 
                               'medium',
                               'Use descriptive link text that makes sense out of context.')
    
    def _check_tables(self, soup, file_path):
        """Проверка таблиц на проблемы доступности."""
        tables = soup.find_all('table')
        for table in tables:
            # Проверка заголовков таблиц
            if not table.find('th'):
                self._add_issue(file_path, 'missing-table-headers', 
                               "Table without header cells (th)", 
                               self._get_line_number(table), 
                               'medium',
                               'Add th elements to identify table headers.')
            
            # Проверка подписи таблицы
            if not table.find('caption'):
                self._add_issue(file_path, 'missing-table-caption', 
                               "Table without caption", 
                               self._get_line_number(table), 
                               'low',
                               'Add a caption element to describe the table content.')
    
    def _get_line_number(self, element):
        """Получение приблизительного номера строки для элемента (если доступно)."""
        return 0  # Упрощенная версия
    
    def _add_issue(self, file_path, issue_type, description, line, severity, recommendation):
        """Добавление проблемы в список."""
        self.issues.append({
            'file': str(file_path),
            'type': issue_type,
            'description': description,
            'line': line,
            'severity': severity,
            'recommendation': recommendation
        })

def scan_templates(templates_dir):
    """Сканирование всех файлов шаблонов на проблемы доступности."""
    checker = AccessibilityChecker()
    template_files = []
    
    # Поиск всех HTML файлов
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                template_files.append(Path(root) / file)
    
    # Параллельная обработка файлов
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(executor.map(checker.check_file, template_files))
    
    return checker.issues, sum(results), len(template_files)

def generate_report(issues, total_issues, total_files):
    """Генерация HTML и JSON отчетов."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Сохранение JSON отчета
    json_report_path = REPORTS_DIR / f"accessibility_report_{timestamp}.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': total_files,
                'total_issues': total_issues,
                'issues_by_severity': {
                    'high': sum(1 for issue in issues if issue['severity'] == 'high'),
                    'medium': sum(1 for issue in issues if issue['severity'] == 'medium'),
                    'low': sum(1 for issue in issues if issue['severity'] == 'low')
                }
            },
            'issues': issues
        }, f, indent=2)
    
    # Сохранение HTML отчета
    html_report_path = REPORTS_DIR / f"accessibility_report_{timestamp}.html"
    
    # Группировка проблем по файлам
    issues_by_file = {}
    for issue in issues:
        file_path = issue['file']
        if file_path not in issues_by_file:
            issues_by_file[file_path] = []
        issues_by_file[file_path].append(issue)
    
    # Генерация HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Accessibility Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .file-section {{ margin-bottom: 30px; border: 1px solid #ddd; border-radius: 5px; padding: 15px; }}
            .issue {{ margin-bottom: 15px; padding: 10px; border-left: 4px solid #ccc; }}
            .high {{ border-left-color: #d9534f; }}
            .medium {{ border-left-color: #f0ad4e; }}
            .low {{ border-left-color: #5bc0de; }}
            .severity-badge {{ display: inline-block; padding: 3px 8px; border-radius: 3px; color: white; font-size: 12px; }}
            .severity-high {{ background-color: #d9534f; }}
            .severity-medium {{ background-color: #f0ad4e; }}
            .severity-low {{ background-color: #5bc0de; }}
            .recommendation {{ background-color: #dff0d8; padding: 10px; border-radius: 3px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <h1>Accessibility Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Total Files Scanned: {total_files}</p>
            <p>Total Issues Found: {total_issues}</p>
            <p>Issues by Severity:</p>
            <ul>
                <li>High: {sum(1 for issue in issues if issue['severity'] == 'high')}</li>
                <li>Medium: {sum(1 for issue in issues if issue['severity'] == 'medium')}</li>
                <li>Low: {sum(1 for issue in issues if issue['severity'] == 'low')}</li>
            </ul>
        </div>
        
        <h2>Issues by File</h2>
    """
    
    # Сортировка файлов по количеству проблем (по убыванию)
    sorted_files = sorted(issues_by_file.items(), key=lambda x: len(x[1]), reverse=True)
    
    for file_path, file_issues in sorted_files:
        html += f"""
        <div class="file-section">
            <h3>{file_path}</h3>
            <p>Issues: {len(file_issues)}</p>
        """
        
        # Сортировка проблем по серьезности
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_issues = sorted(file_issues, key=lambda x: severity_order.get(x['severity'], 3))
        
        for issue in sorted_issues:
            html += f"""
            <div class="issue {issue['severity']}">
                <div>
                    <span class="severity-badge severity-{issue['severity']}">{issue['severity'].upper()}</span>
                    <strong>{issue['type']}</strong>
                </div>
                <p>{issue['description']}</p>
                <div class="recommendation">
                    <strong>Recommendation:</strong> {issue['recommendation']}
                </div>
            </div>
            """
        
        html += """
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    with open(html_report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return json_report_path, html_report_path

def print_summary(issues, total_issues, total_files, json_report_path, html_report_path):
    """Вывод сводки сканирования доступности."""
    high_issues = sum(1 for issue in issues if issue['severity'] == 'high')
    medium_issues = sum(1 for issue in issues if issue['severity'] == 'medium')
    low_issues = sum(1 for issue in issues if issue['severity'] == 'low')
    
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}ACCESSIBILITY SCAN SUMMARY{Style.RESET_ALL}")
    print("=" * 80)
    print(f"Total Files Scanned: {total_files}")
    print(f"Total Issues Found: {total_issues}")
    print("\nIssues by Severity:")
    print(f"  {Fore.RED}High: {high_issues}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Medium: {medium_issues}{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}Low: {low_issues}{Style.RESET_ALL}")
    
    print("\nTop Issues:")
    issue_types = {}
    for issue in issues:
        issue_type = issue['type']
        if issue_type not in issue_types:
            issue_types[issue_type] = 0
        issue_types[issue_type] += 1
    
    for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {issue_type}: {count}")
    
    print("\nReports Generated:")
    print(f"  - JSON: {json_report_path}")
    print(f"  - HTML: {html_report_path}")
    print("=" * 80)

def main():
    """Основная функция для запуска проверок доступности."""
    parser = argparse.ArgumentParser(description="Generate accessibility report")
    parser.add_argument("--templates-dir", default=str(TEMPLATES_DIR), help="Directory containing HTML templates")
    args = parser.parse_args()
    
    templates_dir = Path(args.templates_dir)
    if not templates_dir.exists():
        print(f"Error: Templates directory not found: {templates_dir}")
        return 1
    
    print(f"Scanning templates in {templates_dir}...")
    issues, total_issues, total_files = scan_templates(templates_dir)
    
    if total_issues == 0:
        print(f"{Fore.GREEN}No accessibility issues found!{Style.RESET_ALL}")
        return 0
    
    json_report_path, html_report_path = generate_report(issues, total_issues, total_files)
    print_summary(issues, total_issues, total_files, json_report_path, html_report_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())