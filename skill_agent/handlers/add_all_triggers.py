# skill_agent/handlers/add_all_triggers.py
# Auto-generated: который добавляет триггеры для всех скиллов сразу
# Triggers: скрипт, триггер, скиллы
# Created: 2026-06-25 19:39:54
# DO NOT EDIT MANUALLY

import sqlite3 as sql
import re

def handle_add_all_triggers(cmd, cmd_line, ask_ai_fn):
    if any(t in cmd_line.lower() for t in ["скрипт", "триггер", "скиллы"]):
        try:
            # Извлеки название скилла из cmd_line
            skill_name = re.search(r'\b\w+\b', cmd_line).group(0)
            
            # Выполни действие с БД (sqlite3) или с файловой системой
            conn = sql.connect('your_database.db')
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO triggers (skill_name, action) VALUES (?, ?)", (skill_name, 'some_action'))
            conn.commit()
            
            # Выведи результат через print()
            print(f"Trigger for skill '{skill_name}' added successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()
            
        return True
    else:
        return False
