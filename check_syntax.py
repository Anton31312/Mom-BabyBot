#!/usr/bin/env python
"""
Проверка синтаксиса Python файлов
"""
import os
import sys
import ast
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s')
logger = logging.getLogger(__name__)

def check_file_syntax(file_path):
    """Проверка синтаксиса одного файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Парсим файл для проверки синтаксиса
        ast.parse(content)
        logger.info(f"✅ {file_path} - синтаксис корректен")
        return True
        
    except SyntaxError as e:
        logger.error(f"❌ {file_path} - синтаксическая ошибка: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ {file_path} - ошибка чтения: {e}")
        return False

def find_python_files(directory):
    """Поиск всех Python файлов в директории"""
    python_files = []
    
    for root, dirs, files in os.walk(directory):
        # Исключаем виртуальные окружения и кэш
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    logger.info("🔍 Проверка синтаксиса Python файлов...")
    
    # Получаем текущую директорию
    current_dir = os.getcwd()
    logger.info(f"Проверяем директорию: {current_dir}")
    
    # Находим все Python файлы
    python_files = find_python_files(current_dir)
    logger.info(f"Найдено {len(python_files)} Python файлов")
    
    # Проверяем каждый файл
    passed = 0
    failed = 0
    
    for file_path in python_files:
        if check_file_syntax(file_path):
            passed += 1
        else:
            failed += 1
    
    # Выводим итоговый результат
    logger.info(f"\n📊 Результат проверки:")
    logger.info(f"✅ Прошли проверку: {passed}")
    logger.info(f"❌ Не прошли проверку: {failed}")
    logger.info(f"📁 Всего файлов: {len(python_files)}")
    
    if failed == 0:
        logger.info("🎉 Все файлы прошли проверку синтаксиса!")
        return 0
    else:
        logger.error(f"❌ {failed} файлов имеют синтаксические ошибки")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 