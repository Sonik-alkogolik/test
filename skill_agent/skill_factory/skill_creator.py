# skill_agent/skill_factory/skill_creator.py
# 🚀 Единая фабрика скиллов v5.0 (чистая, без лишней логики)

import os
import re
import json
from datetime import datetime

def create_universal_skill(skill_name, description, ask_ai_fn, project_root="."):
    """
    Создаёт скилл по единому стандарту:
    1. Генерирует 10-20 триггеров через AI
    2. Создаёт файл скилла
    3. Автоматически добавляет все триггеры в БД
    4. Регистрирует скилл в системе
    """
    print(f"🏭 Создаю скилл: '{skill_name}'")
    
    # === Шаг 1: Генерация 10-20 триггеров ===
    print("🧠 Генерирую 15 триггеров...")
    triggers = generate_triggers(skill_name, description, ask_ai_fn)
    print(f"   ✅ Сгенерировано {len(triggers)} триггеров")
    
    # === Шаг 2: Создание файла скилла ===
    print("📝 Создаю файл скилла...")
    handler_code = generate_handler_code(skill_name, description, triggers, ask_ai_fn)
    handler_path = save_handler_file(skill_name, handler_code, description, triggers, project_root)
    print(f"   ✅ Файл создан: {handler_path}")
    
    # === Шаг 3: Авто-регистрация и добавление в БД ===
    print("🔌 Регистрирую скилл и добавляю триггеры...")
    update_router(skill_name, description, project_root)
    update_init(skill_name, project_root)
    add_triggers_to_db(skill_name, triggers)
    
    print(f"🎉 Скилл '{skill_name}' создан с {len(triggers)} триггерами!")
    return True


def generate_triggers(skill_name, description, ask_ai_fn):
    """Генерирует 10-20 триггеров через AI."""
    prompt = f"""Ты — эксперт по созданию триггеров для AI-агента.

Новый скилл: "{skill_name}"
Описание: "{description}"

Сгенерируй 15 релевантных триггеров (ключевых слов и фраз) для этого скилла.
Триггеры должны отражать:
- Основное действие (глаголы)
- Объекты, с которыми работает скилл
- Синонимы на русском и английском

Верни ТОЛЬКО JSON-массив строк, например:
["триггер1", "триггер2", ...]

Ответ:"""
    
    raw = ask_ai_fn(prompt).strip()
    match = re.search(r'\[[\s\S]*\]', raw)
    if match:
        try:
            triggers = json.loads(match.group(0))
            if isinstance(triggers, list):
                return [str(t).strip().lower() for t in triggers if t and isinstance(t, str)]
        except:
            pass
    
    # Fallback: простые слова из описания
    return [skill_name] + re.findall(r'\b\w{3,}\b', description.lower())[:14]


def generate_handler_code(skill_name, description, triggers, ask_ai_fn):
    """Генерирует код хендлера."""
    triggers_list = ', '.join(f'"{t}"' for t in triggers)
    
    prompt = f"""Напиши функцию `handle_{skill_name}(cmd, cmd_line, ask_ai_fn)`.

ОПИСАНИЕ: {description}
ТРИГГЕРЫ (проверять в cmd_line): {triggers_list}

ТРЕБОВАНИЯ:
1. def handle_{skill_name}(cmd, cmd_line, ask_ai_fn):
2. Проверка: if any(t in cmd_line.lower() for t in [{triggers_list}]):
3. Возвращает True если обработано, иначе False
4. Используй print() для вывода результата
5. Добавь try/except

Верни ТОЛЬКО код функции. Без пояснений. Без импортов."""
    
    return ask_ai_fn(prompt).strip()


def save_handler_file(skill_name, handler_code, description, triggers, project_root):
    """Сохраняет файл скилла."""
    handler_path = os.path.join(project_root, "skill_agent", "handlers", f"{skill_name}.py")
    os.makedirs(os.path.dirname(handler_path), exist_ok=True)
    
    needed_imports = []
    if "subprocess" in handler_code and "import subprocess" not in handler_code:
        needed_imports.append("import subprocess")
    if "os." in handler_code and "import os" not in handler_code:
        needed_imports.append("import os")
    if "requests" in handler_code and "import requests" not in handler_code:
        needed_imports.append("import requests")
    
    imports_block = "\n".join(needed_imports) + "\n\n" if needed_imports else ""
    
    full_code = f"""# skill_agent/handlers/{skill_name}.py
# Auto-generated: {description}
# Triggers: {', '.join(triggers)}
# Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{imports_block}{handler_code}
"""
    
    with open(handler_path, 'w', encoding='utf-8') as f:
        f.write(full_code)
    
    return handler_path


def update_router(skill_name, description, project_root):
    """Добавляет скилл в SKILLS_REGISTRY в router.py."""
    router_path = os.path.join(project_root, "skill_agent", "router.py")
    if not os.path.exists(router_path):
        return
    
    with open(router_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if f'"name": "{skill_name}"' in content:
        return
    
    new_entry = f'    {{"name": "{skill_name}", "description": "{description}", "params": "cmd_line: строка команды пользователя"}},\n'
    idx = content.rfind(']\n')
    if idx != -1:
        new_content = content[:idx] + new_entry + content[idx:]
        with open(router_path, 'w', encoding='utf-8') as f:
            f.write(new_content)


def update_init(skill_name, project_root):
    """Добавляет импорт в handlers/__init__.py."""
    init_path = os.path.join(project_root, "skill_agent", "handlers", "__init__.py")
    if not os.path.exists(init_path):
        return
    
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import_line = f"from .{skill_name} import handle_{skill_name}\n"
    if import_line in content:
        return
    
    with open(init_path, 'a', encoding='utf-8') as f:
        f.write(import_line)


def add_triggers_to_db(skill_name, triggers):
    """Добавляет все триггеры в БД."""
    try:
        from skill_agent.triggers import add_skill, add_trigger, init_db
        init_db()
        add_skill(skill_name, "")
        for trigger in triggers:
            add_trigger(skill_name, trigger)
        print(f"   ✅ Добавлено {len(triggers)} триггеров в БД")
    except Exception as e:
        print(f"   ⚠️ Ошибка БД: {e}")

        