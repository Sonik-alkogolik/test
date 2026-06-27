# skill_agent/PHP/php_editor.py
# Универсальный редактор PHP-методов с отладкой

import re
import os
import subprocess

def find_method_bounds(content, method_name):
    """
    Находит start/end индексы метода.
    Возвращает (start, end) или None.
    """
    # Паттерн ищет: visibility function name(
    pattern = rf'(?:public|private|protected|static)\s+function\s+{re.escape(method_name)}\s*\('
    match = re.search(pattern, content)
    
    if not match:
        print(f"⚠️ Не нашёл сигнатуру 'function {method_name}(' в файле")
        return None

    start = match.start()
    print(f"🔍 Нашёл сигнатуру на позиции {start}")

    # Ищем открывающую скобку тела метода
    brace_start = content.find('{', match.end())
    if brace_start == -1:
        print("⚠️ Не нашёл открывающую скобку '{{' после сигнатуры")
        return None

    # Считаем вложенные скобки
    depth = 1
    i = brace_start + 1
    while i < len(content) and depth > 0:
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
        i += 1

    if depth != 0:
        print(f"⚠️ Не смог найти закрывающую скобку '}}' (depth={depth})")
        return None

    print(f"✅ Границы метода: {start} – {i}")
    return start, i

def edit_method(filepath, method_name, new_code):
    """Заменяет метод в файле. Возвращает (success: bool, message: str)"""
    if not os.path.exists(filepath):
        return False, f"❌ Файл не найден: {filepath}"

    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    print(f"📄 Читаю файл: {os.path.basename(filepath)} ({len(original)} симв.)")

    bounds = find_method_bounds(original, method_name)
    if not bounds:
        # Выведем первые 500 символов файла для диагностики
        snippet = original[:500].replace('\n', '\\n')
        print(f"📋 Фрагмент файла: {snippet}...")
        return False, f"❌ Метод '{method_name}' не найден или не распарсен"

    start, end = bounds
    new_content = original[:start] + new_code + original[end:]

    # Бэкап
    backup_path = filepath + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"💾 Бэкап: {backup_path}")

    # Запись
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✏️ Записал новый код ({len(new_code)} симв.)")

    # Проверка синтаксиса
    res = subprocess.run(['php', '-l', filepath], capture_output=True, text=True)
    if 'No syntax errors detected' in res.stdout:
        return True, f"✅ Метод '{method_name}' успешно заменён"
    else:
        print(f"❌ PHP lint error: {res.stdout.strip()}")
        # Откат
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(original)
        return False, "❌ Ошибка синтаксиса! Изменения отменены."