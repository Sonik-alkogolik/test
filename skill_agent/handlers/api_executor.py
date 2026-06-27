# skill_agent/handlers/api_executor.py
# Auto-generated: универсальной работы с API: погода
# Triggers: универсальной, api, погода, работы
# Created: 2026-06-25 18:38:25
# DO NOT EDIT MANUALLY

import re

def handle_api_executor(cmd, cmd_line, ask_ai_fn):
    if any(t in cmd_line.lower() for t in ["универсальной", "api", "погода", "работы"]):
        print("Обработано")
        return True
    else:
        print("Не обработано")
        return False
