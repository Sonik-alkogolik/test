# skill_agent/controller/response_controller.py
import json
import re

def handle_ai_response(ai_text, skills_map):
    """
    Контроллер ответа модели.
    1. Ищет команду вида {"action": "git_add", "args": {"path": "."}}
    2. Если находит -> выполняет функцию из skills_map
    3. Если нет -> возвращает текст как чат
    """
    # 1. Чистим от markdown-обёрток
    clean = ai_text.replace("```json", "").replace("```", "").strip()

    # 2. Ищем JSON-объект с ключом "action" (безопасный поиск без вложенности)
    match = re.search(r'\{[^{}]*"action"[^{}]*\}', clean, re.DOTALL)
    if match:
        try:
            cmd = json.loads(match.group(0))
            action = cmd.get("action", "").lower()
            args = cmd.get("args", {})

            print(f"🎛️ Контроллер: вызываю скилл '{action}'")

            if action in skills_map:
                # Выполняем скилл и возвращаем результат
                return skills_map[action](**args)
            else:
                return f"⚠️ Контроллер не знает скилл '{action}'. Доступны: {', '.join(skills_map.keys())}"
        except Exception as e:
            print(f"⚠️ Ошибка выполнения команды AI: {e}")

    # 3. Если команды нет или JSON битый — возвращаем исходный текст (чат-режим)
    return ai_text