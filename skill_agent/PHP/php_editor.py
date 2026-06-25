# php_editor.py
# Универсальный редактор PHP-файлов. Не зависит от фреймворка.

import re
import os
import subprocess

def find_method_bounds(content, method_name):
    """Находит start/end индексы метода по имени (учитывает вложенные скобки)"""
    pattern = rf'(?:public|private|protected|static)\s+function\s+{re.escape(method_name)}\s*\('
    match = re.search(pattern, content)
    if not match:
        return None

    start = match.start()
    brace_start = content.find('{', match.end())
    if brace_start == -1:
        return None

    depth = 1
    i = brace_start + 1
    while i < len(content) and depth > 0:
        if content[i] == '{': depth += 1
        elif content[i] == '}': depth -= 1
        i += 1

    return start, i

def edit_method(filepath, method_name, new_code):
    """Заменяет метод. Возвращает (success: bool, message: str)"""
    if not os.path.exists(filepath):
        return False, "❌ Файл не найден"

    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    bounds = find_method_bounds(original, method_name)
    if not bounds:
        return False, f"❌ Метод '{method_name}' не найден"

    start, end = bounds
    new_content = original[:start] + new_code + original[end:]

    with open(filepath + '.bak', 'w', encoding='utf-8') as f:
        f.write(original)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    res = subprocess.run(['php', '-l', filepath], capture_output=True, text=True)
    if 'No syntax errors detected' in res.stdout:
        return True, f"✅ Метод '{method_name}' обновлён"
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(original)
        return False, "❌ Синтаксис сломан. Откат выполнен."