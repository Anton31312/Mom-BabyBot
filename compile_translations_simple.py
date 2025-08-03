#!/usr/bin/env python3
"""
Простая компиляция переводов без использования GNU gettext
"""

import os
import struct
import array
from pathlib import Path

def make_mo(po_path, mo_path):
    """
    Создает .mo файл из .po файла
    """
    # Читаем .po файл
    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Парсим .po файл
    messages = {}
    msgid = None
    msgstr = None
    in_msgid = False
    in_msgstr = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('msgid '):
            if msgid is not None and msgstr is not None:
                if msgid and msgstr:  # Пропускаем пустые строки
                    messages[msgid] = msgstr
            msgid = line[7:-1]  # Убираем 'msgid "' и '"'
            msgstr = None
            in_msgid = True
            in_msgstr = False
            
        elif line.startswith('msgstr '):
            msgstr = line[8:-1]  # Убираем 'msgstr "' и '"'
            in_msgid = False
            in_msgstr = True
            
        elif line.startswith('"') and line.endswith('"'):
            content = line[1:-1]  # Убираем кавычки
            if in_msgid and msgid is not None:
                msgid += content
            elif in_msgstr and msgstr is not None:
                msgstr += content
    
    # Добавляем последнее сообщение
    if msgid is not None and msgstr is not None:
        if msgid and msgstr:
            messages[msgid] = msgstr
    
    # Создаем .mo файл
    keys = sorted(messages.keys())
    koffsets = []
    voffsets = []
    kencoded = []
    vencoded = []
    
    for k in keys:
        kencoded.append(k.encode('utf-8'))
        vencoded.append(messages[k].encode('utf-8'))
    
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart
    for k in kencoded:
        valuestart += len(k)
    
    koffsets = []
    voffsets = []
    
    # Вычисляем смещения для ключей
    offset = keystart
    for k in kencoded:
        koffsets.append((len(k), offset))
        offset += len(k)
    
    # Вычисляем смещения для значений
    offset = valuestart
    for v in vencoded:
        voffsets.append((len(v), offset))
        offset += len(v)
    
    # Записываем .mo файл
    with open(mo_path, 'wb') as f:
        # Заголовок
        f.write(struct.pack('<I', 0x950412de))  # Magic number
        f.write(struct.pack('<I', 0))           # Version
        f.write(struct.pack('<I', len(keys)))   # Number of entries
        f.write(struct.pack('<I', 7 * 4))       # Offset of key table
        f.write(struct.pack('<I', 7 * 4 + 8 * len(keys)))  # Offset of value table
        f.write(struct.pack('<I', 0))           # Hash table size
        f.write(struct.pack('<I', 0))           # Hash table offset
        
        # Таблица ключей
        for length, offset in koffsets:
            f.write(struct.pack('<I', length))
            f.write(struct.pack('<I', offset))
        
        # Таблица значений
        for length, offset in voffsets:
            f.write(struct.pack('<I', length))
            f.write(struct.pack('<I', offset))
        
        # Ключи
        for k in kencoded:
            f.write(k)
        
        # Значения
        for v in vencoded:
            f.write(v)

def main():
    """Компилируем все .po файлы в .mo"""
    base_dir = Path(__file__).parent
    locale_dir = base_dir / 'locale'
    
    if not locale_dir.exists():
        print("Папка locale не найдена")
        return
    
    for lang_dir in locale_dir.iterdir():
        if lang_dir.is_dir():
            lc_messages_dir = lang_dir / 'LC_MESSAGES'
            if lc_messages_dir.exists():
                po_file = lc_messages_dir / 'django.po'
                mo_file = lc_messages_dir / 'django.mo'
                
                if po_file.exists():
                    print(f"Компилируем {po_file} -> {mo_file}")
                    try:
                        make_mo(po_file, mo_file)
                        print(f"✅ Успешно создан {mo_file}")
                    except Exception as e:
                        print(f"❌ Ошибка при создании {mo_file}: {e}")

if __name__ == '__main__':
    main()