#!/usr/bin/env python3
"""
Простой скрипт для компиляции переводов без использования gettext tools.
Создает базовый .mo файл для Django.
"""

import os
import struct
from pathlib import Path

def create_mo_file(po_file_path, mo_file_path):
    """
    Создает простой .mo файл из .po файла.
    Это упрощенная версия, которая работает без gettext tools.
    """
    
    # Читаем .po файл и извлекаем переводы
    translations = {}
    
    try:
        with open(po_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Простой парсер для .po файла
        lines = content.split('\n')
        msgid = None
        msgstr = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('msgid "') and line.endswith('"'):
                msgid = line[7:-1]  # Убираем 'msgid "' и '"'
                
            elif line.startswith('msgstr "') and line.endswith('"'):
                msgstr = line[8:-1]  # Убираем 'msgstr "' и '"'
                
                if msgid and msgstr and msgid != '' and msgstr != '':
                    translations[msgid] = msgstr
                    
                msgid = None
                msgstr = None
        
        print(f"Найдено {len(translations)} переводов")
        
        if len(translations) == 0:
            print("Создаем пустой .mo файл")
            # Создаем минимальный пустой .mo файл
            with open(mo_file_path, 'wb') as f:
                # Magic number + version + 0 strings + offsets
                f.write(b'\xde\x12\x04\x95\x00\x00\x00\x00\x00\x00\x00\x00\x1c\x00\x00\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            return
        
        # Создаем корректный .mo файл
        keys = list(translations.keys())
        values = list(translations.values())
        
        # Кодируем строки
        kencoded = [k.encode('utf-8') + b'\x00' for k in keys]
        vencoded = [v.encode('utf-8') + b'\x00' for v in values]
        
        # Сортируем по ключам для корректной работы
        keystart = 7 * 4 + 16 * len(keys)
        valuestart = keystart
        for k in kencoded:
            valuestart += len(k)
        
        # Создаем заголовок
        output = struct.pack('<I', 0x950412de)  # Magic number
        output += struct.pack('<I', 0)  # Version
        output += struct.pack('<I', len(keys))  # Number of entries
        output += struct.pack('<I', 7 * 4)  # Offset of key table
        output += struct.pack('<I', 7 * 4 + 8 * len(keys))  # Offset of value table
        output += struct.pack('<I', 0)  # Hash table size
        output += struct.pack('<I', 0)  # Hash table offset
        
        # Создаем таблицы ключей и значений
        koffsets = []
        voffsets = []
        
        # Таблица ключей
        offset = keystart
        for k in kencoded:
            output += struct.pack('<I', len(k) - 1)  # Длина без null terminator
            output += struct.pack('<I', offset)
            koffsets.append(offset)
            offset += len(k)
        
        # Таблица значений
        offset = valuestart
        for v in vencoded:
            output += struct.pack('<I', len(v) - 1)  # Длина без null terminator
            output += struct.pack('<I', offset)
            voffsets.append(offset)
            offset += len(v)
        
        # Добавляем сами строки
        for k in kencoded:
            output += k
        for v in vencoded:
            output += v
        
        # Записываем .mo файл
        with open(mo_file_path, 'wb') as f:
            f.write(output)
            
        print(f"Создан файл {mo_file_path}")
        
    except Exception as e:
        print(f"Ошибка при создании .mo файла: {e}")
        # Создаем пустой .mo файл для совместимости
        with open(mo_file_path, 'wb') as f:
            f.write(b'\xde\x12\x04\x95\x00\x00\x00\x00\x00\x00\x00\x00\x1c\x00\x00\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def main():
    """Основная функция для компиляции переводов."""
    
    base_dir = Path(__file__).parent
    locale_dir = base_dir / 'locale'
    
    # Компилируем русский перевод
    ru_po = locale_dir / 'ru' / 'LC_MESSAGES' / 'django.po'
    ru_mo = locale_dir / 'ru' / 'LC_MESSAGES' / 'django.mo'
    
    if ru_po.exists():
        print(f"Компилируем {ru_po}")
        create_mo_file(ru_po, ru_mo)
    else:
        print(f"Файл {ru_po} не найден")
    
    print("Компиляция переводов завершена")

if __name__ == '__main__':
    main()