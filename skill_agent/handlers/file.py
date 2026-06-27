# skill_agent/handlers/file.py
import json, re
import os
from skill_agent.state import WORK_DIR
try:
    from skill_agent.git_skills.file_creator import create_or_edit_file
except ImportError:
    create_or_edit_file = None

def handle_file(cmd, cmd_line, ask_ai_fn):
    if "create file" not in cmd and "создай файл" not in cmd:
        return False

    prompt = f"""Верни СТРОГО JSON: {{"target": "путь/к/файлу.php", "params": "задача"}}. Запрос: {cmd_line}"""
    try:
        raw = ask_ai_fn(prompt).replace("```json","").replace("```","").strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            intent = json.loads(match.group(0))
            target = intent.get("target", "")
            params = intent.get("params", "")
            
            # Подставляем WORK_DIR если файл относительный
            if WORK_DIR and WORK_DIR != "." and not os.path.isabs(target) and not target.startswith(WORK_DIR):
                target = os.path.join(WORK_DIR, target)

            print(f"📝 Создаю/редактирую: {target}")
            if create_or_edit_file:
                success, msg = create_or_edit_file(target, params)
                print(msg)
            else:
                print("❌ Модуль создания файлов не загружен!")
            return True
    except Exception as e:
        print(f"⚠️ Ошибка разбора: {e}")

    return False