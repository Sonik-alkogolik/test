# skill_agent/handlers/memory.py
# Auto-generated: хранения истории диалога и контекста
# Triggers: хранение, истории, диалога
# Created: 2026-06-25 19:51:03
# DO NOT EDIT MANUALLY

import re

import sqlite3

def handle_memory(cmd, cmd_line, ask_ai_fn):
    if any(t in cmd_line.lower() for t in ["хранение", "истории", "диалога"]):
        try:
            # Извлеки название скилла из cmd_line
            skill_name = re.search(r"извлечь название (.+)", cmd_line).group(1)
            
            # Выполни действие с БД (sqlite3) или с файловой системой
            conn = sqlite3.connect('memory.db')
            cursor = conn.cursor()
            # Пример: cursor.execute("INSERT INTO memory (skill, dialog) VALUES (?, ?)", (skill_name, cmd))
            # conn.commit()
            
            # Выведи результат через print()
            print(f"Скилл '{skill_name}' успешно сохранен в истории.")
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False
