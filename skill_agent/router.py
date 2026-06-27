# skill_agent/router.py
import sys
import os
import json
import re
import importlib
import sqlite3
import time

sys.path.append(os.getcwd())

from skill_agent.state import WORK_DIR
from skill_agent.handlers.system import handle_system

def resolve_skill_module(action):
    base = os.path.join(os.getcwd(), "skill_agent")
    if not os.path.exists(base): return None
    for category in os.listdir(base):
        cat_path = os.path.join(base, category)
        if os.path.isdir(cat_path) and not category.startswith('_'):
            if os.path.exists(os.path.join(cat_path, f"{action}.py")):
                try: return importlib.import_module(f"skill_agent.{category}.{action}")
                except: continue
    return None

def load_skills_from_db():
    db_path = os.path.join("skill_agent", "triggers", "triggers.db")
    registry = []
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM skills")
            for skill_id, name in cursor.fetchall():
                cursor.execute("SELECT trigger_text FROM triggers WHERE skill_id = ?", (skill_id,))
                triggers = [t[0] for t in cursor.fetchall()[:7]]
                desc = f"Триггеры: {', '.join(triggers)}" if triggers else "универсальный запрос"
                desc = desc.replace('"', "'").replace('\n', ' ').replace('\r', '')[:150]
                registry.append({"name": name, "description": desc, "params": "cmd_line: str"})
            conn.close()
        except Exception as e:
            print(f"⚠️ Ошибка БД: {e}")
    if not registry:
        registry = [{"name": "git", "description": "Git команды", "params": "cmd_line: str"}]
    return registry

def get_ai_decision(cmd_line, ask_ai_fn):
    registry = load_skills_from_db()
    valid_names = [s["name"] for s in registry] + ["chat", "recommend_skill"]
    
    prompt = f"""Диспетчер. Выбери строго ОДНО имя из списка: {', '.join(valid_names)}.
Запрос: "{cmd_line}"
Верни ТОЛЬКО JSON: {{"action": "имя_из_списка"}}"""
    
    raw = ask_ai_fn(prompt).strip().replace('```', '').strip()
    try:
        data = json.loads(re.search(r'\{.*\}', raw, re.DOTALL).group(0))
        action = data.get("action", "chat")
        if action in valid_names:
            return {"action": action, "params": {"cmd_line": cmd_line}}
    except: pass
    
    # 🔒 Fallback: если AI ошибся, ищем прямое совпадение по имени скилла в запросе
    for name in valid_names:
        if name in cmd_line.lower():
            return {"action": name, "params": {"cmd_line": cmd_line}}
    return {"action": "chat", "params": {"prompt": cmd_line}}

def execute_action(decision, ask_ai_fn):
    action = decision.get("action", "chat")
    params = decision.get("params", {})
    cmd_line = params.get("cmd_line", "")

    if action == "recommend_skill":
        words = re.findall(r'[a-zа-я]+', cmd_line.lower())
        keyword = words[-1] if words else "code"
        print(f"🧠 Подбираю скилл для: '{keyword}'...")

        for attempt in range(1, 4):
            try:
                prompt = f"Имя скилла для {keyword}: "
                raw = ask_ai_fn(prompt).strip().replace('```', '').strip()
                parts = raw.split(':', 1) if ':' in raw else [raw, ""]
                name = re.sub(r'[^a-z0-9_]', '', parts[0].strip().lower())[:20] or f"{keyword}_skill"
                desc = parts[1].strip()[:60] if len(parts) > 1 else f"инструменты для {keyword}"
                print(f"🛠 AI: '{name}' — {desc}")
                print("⏳ Создаю...")
                time.sleep(1)
                from skill_agent.skill_factory.skill_creator import create_universal_skill
                create_universal_skill(name, desc, ask_ai_fn)
                print("✅ Готово.\n")
                return
            except Exception as e:
                print(f"⚠️ Попытка {attempt}: {e}")
                import traceback; traceback.print_exc()
                if attempt == 3:
                    print("❌ Fallback: создаю базовый скилл")
                    try:
                        from skill_agent.skill_factory.skill_creator import create_universal_skill
                        create_universal_skill(f"{keyword}_helper", f"помощник для {keyword}", ask_ai_fn)
                        print("✅ Fallback создан.\n")
                    except Exception as e2:
                        print(f"💥 Fallback не сработал: {e2}")
                        import traceback; traceback.print_exc()
        return

    if action == "chat":
        print("🤖", ask_ai_fn(params.get("prompt", cmd_line)))
        print("✅ Готов.\n")
        return

    try:
        module = resolve_skill_module(action)
        if not module:
            try: module = importlib.import_module(f"skill_agent.handlers.{action}")
            except ImportError: module = None
        if not module: print(f"⚠️ '{action}' не найден"); return
        handler = getattr(module, f"handle_{action}", None)
        if not handler: print(f"⚠️ Нет handle_{action}"); return
        cmd = cmd_line.strip().lower()
        try: handler(cmd, cmd_line, ask_ai_fn)
        except TypeError: handler(cmd_line, ask_ai_fn)
    except Exception as e: print(f"❌ '{action}': {e}")

def run_command(cmd_line, ask_ai_fn):
    cmd = cmd_line.strip().lower()
    if cmd in ["exit", "выход", "quit"]: print("👋 Пока!"); sys.exit(0)
    if cmd in ["help", "помощь", "?"]: print("📖 Просто напиши задачу."); return

    # 🔹 Динамический вывод триггеров из БД
    if any(x in cmd for x in ["покажи триггеры", "список триггеров", "триггеры"]):
        db_path = os.path.join("skill_agent", "triggers", "triggers.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            rows = conn.execute("""
                SELECT s.name, t.trigger_text 
                FROM skills s JOIN triggers t ON s.id = t.skill_id 
                ORDER BY s.name
            """).fetchall()
            conn.close()
            if rows:
                print("📋 Загруженные скиллы и триггеры:")
                cur_skill = ""
                for skill, trigger in rows:
                    if skill != cur_skill:
                        cur_skill = skill
                        print(f"\n🔹 {skill}:")
                    print(f"  - {trigger}")
            else: print("⚠️ БД триггеров пуста.")
        return

    if any(x in cmd for x in ["создай скилл", "create skill", "новый скилл"]):
        handle_system(cmd, cmd_line, ask_ai_fn)
        return

    decision = get_ai_decision(cmd_line, ask_ai_fn)
    execute_action(decision, ask_ai_fn)