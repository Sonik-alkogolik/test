# skill_agent/skill_factory/skill_creator.py
# 🚀 Единая фабрика скиллов v5.0 (Динамические категории + Авто-восстановление)

import os
import re
import json
import sqlite3
import traceback
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "triggers", "triggers.db"))

# ================= БД КАТЕГОРИЙ =================
def _init_categories_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY, name TEXT UNIQUE, description TEXT
    )""")
    cur = conn.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        defaults = [
            ("core", "базовые (git, file, system, trigger_manager)"),
            ("devops", "инфраструктура (docker, kubernetes, server, deploy)"),
            ("development", "разработка (api, code, test, refactor, php, laravel)"),
            ("ai", "AI/ML (skill_creator, model, prompt, learning)"),
            ("utils", "вспомогательные (helpers, validators, formatters)"),
            ("custom", "пользовательские (если не подходит выше)")
        ]
        conn.executemany("INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)", defaults)
        conn.commit()
    conn.close()

def _get_categories():
    _init_categories_db()
    conn = sqlite3.connect(DB_PATH)
    cats = [{"name": r[1], "desc": r[2]} for r in conn.execute("SELECT name, description FROM categories").fetchall()]
    conn.close()
    return cats

def _ensure_category(name, desc):
    _init_categories_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)", (name.lower(), desc))
    conn.commit()
    conn.close()

def _scan_existing_dirs(project_root):
    """Сканирует реальные папки в skill_agent/"""
    base = os.path.join(project_root, "skill_agent")
    if not os.path.exists(base): return ["handlers"]
    exclude = {'triggers', 'skill_factory', 'self_improve', 'project_analyzer', '__pycache__', 'controller'}
    return [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and d not in exclude]

# ================= ОСНОВНАЯ ЛОГИКА =================
def create_universal_skill(skill_name, description, ask_ai_fn, project_root="."):
    try:
        print(f"🏭 Создаю скилл: '{skill_name}'")
        
        print("🧠 Генерирую 15 триггеров...")
        triggers = generate_triggers(skill_name, description, ask_ai_fn)
        print(f"   ✅ Сгенерировано {len(triggers)} триггеров")
        
        print("🧠 Определяю категорию...")
        category, cat_desc = determine_category(skill_name, description, ask_ai_fn, project_root)
        _ensure_category(category, cat_desc)
        print(f"   ✅ Категория: '{category}'")
        
        print("📝 Создаю файл скилла...")
        handler_code = generate_handler_code(skill_name, description, triggers, ask_ai_fn)
        handler_path = save_handler_file(skill_name, handler_code, description, triggers, project_root, category)
        print(f"   ✅ Файл создан: {handler_path}")
        
        print("🔌 Регистрирую скилл и добавляю триггеры...")
        update_router(skill_name, description, project_root)
        update_init(skill_name, category, project_root)
        add_triggers_to_db(skill_name, triggers)
        
        print(f"🎉 Скилл '{skill_name}' создан в категории '{category}' с {len(triggers)} триггерами!")
        return True
    except Exception as e:
        print(f"❌ Ошибка фабрики: {e}")
        traceback.print_exc()
        return False

def determine_category(skill_name, description, ask_ai_fn, project_root="."):
    dirs = _scan_existing_dirs(project_root)
    prompt = f"""Выбери ОДНУ папку из списка для скилла '{skill_name}'.
Список папок: {', '.join(dirs)}
Верни ТОЛЬКО название папки из списка. Если ни одна не подходит, верни 'development'.
Ответ:"""
    raw = ask_ai_fn(prompt).strip().lower()
    match = re.search(r'(' + '|'.join(map(re.escape, dirs)) + r')', raw)
    chosen = match.group(1) if match else "development"
    return chosen, f"папка {chosen}"

def generate_triggers(skill_name, description, ask_ai_fn):
    prompt = f"""Сгенерируй 15 релевантных триггеров для скилла.
Название: {skill_name}
Описание: {description}
Правила:
- Глаголы, объекты, синонимы (RU/EN)
- Опечатки и варианты
- Верни ТОЛЬКО JSON-массив строк: ["триггер1", "триггер2"]
Ответ:"""
    raw = ask_ai_fn(prompt).strip()
    match = re.search(r'\[[\s\S]*\]', raw)
    if match:
        try:
            triggers = json.loads(match.group(0))
            if isinstance(triggers, list):
                return [str(t).strip().lower() for t in triggers if t and isinstance(t, str)][:20]
        except: pass
    return [skill_name] + re.findall(r'\b\w{3,}\b', description.lower())[:14]

def generate_handler_code(skill_name, description, triggers, ask_ai_fn):
    t_list = ', '.join(f'"{t}"' for t in triggers)
    prompt = f"""Напиши ТОЛЬКО код функции `handle_{skill_name}(cmd, cmd_line, ask_ai_fn)`.
ОПИСАНИЕ: {description}
ТРИГГЕРЫ: {t_list}
Правила:
1. def handle_{skill_name}(cmd, cmd_line, ask_ai_fn):
2. if any(t in cmd_line.lower() for t in [{t_list}]): ...
3. return True/False
4. try/except
5. БЕЗ MARKDOWN. БЕЗ ````. БЕЗ ТЕСТОВ. ТОЛЬКО КОД.
Ответ:"""
    raw = ask_ai_fn(prompt).strip()
    # 🔧 Жёсткая чистка markdown и лишнего текста
    raw = re.sub(r'```(?:python|py)?\s*', '', raw).replace('```', '').strip()
    match = re.search(r'(def\s+handle_' + re.escape(skill_name) + r'\([\s\S]*)', raw)
    return match.group(1).strip() if match else raw

def save_handler_file(skill_name, handler_code, description, triggers, project_root, category):
    cat_path = os.path.join(project_root, "skill_agent", category)
    os.makedirs(cat_path, exist_ok=True)
    handler_path = os.path.join(cat_path, f"{skill_name}.py")
    
    imports = []
    if "subprocess" in handler_code and "import subprocess" not in handler_code: imports.append("import subprocess")
    if "os." in handler_code and "import os" not in handler_code: imports.append("import os")
    if "requests" in handler_code and "import requests" not in handler_code: imports.append("import requests")
    
    code = f"""# skill_agent/{category}/{skill_name}.py
# Auto-generated: {description} | Category: {category}
# Triggers: {', '.join(triggers)}
# Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{"\n".join(imports)}

{handler_code}
"""
    with open(handler_path, 'w', encoding='utf-8') as f:
        f.write(code)
    return handler_path

def update_router(skill_name, description, project_root):
    router_path = os.path.join(project_root, "skill_agent", "router.py")
    if not os.path.exists(router_path): return
    with open(router_path, 'r', encoding='utf-8') as f: content = f.read()
    if f'"name": "{skill_name}"' in content: return
    
    entry = f'    {{"name": "{skill_name}", "description": "{description}", "params": "cmd_line: str"}},\n'
    idx = content.rfind(']\n')
    if idx != -1:
        with open(router_path, 'w', encoding='utf-8') as f:
            f.write(content[:idx] + entry + content[idx:])

def update_init(skill_name, category, project_root):
    init_path = os.path.join(project_root, "skill_agent", category, "__init__.py")
    os.makedirs(os.path.dirname(init_path), exist_ok=True)
    content = ""
    if os.path.exists(init_path):
        with open(init_path, 'r', encoding='utf-8') as f: content = f.read()
    
    line = f"from .{skill_name} import handle_{skill_name}\n"
    if line not in content:
        with open(init_path, 'a', encoding='utf-8') as f: f.write(line)

def add_triggers_to_db(skill_name, triggers):
    try:
        from skill_agent.triggers import add_skill, add_trigger, init_db
        init_db()
        add_skill(skill_name, "")
        for t in triggers: add_trigger(skill_name, t)
        print(f"   ✅ Добавлено {len(triggers)} триггеров в БД")
    except Exception as e:
        print(f"   ⚠️ Ошибка БД: {e}")