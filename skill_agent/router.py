# skill_agent/router.py
import sys
import os
import json
import re
import importlib
import sqlite3

sys.path.append(os.getcwd())

from skill_agent.state import WORK_DIR
from skill_agent.handlers.system import handle_system

# Базовые хендлеры (для надёжности)
from skill_agent.handlers.git import handle_git
from skill_agent.handlers.file import handle_file
from skill_agent.handlers.editor import handle_edit_method

def load_skills_from_db():
    """🔍 Динамически загружает скиллы и их триггеры из БД"""
    db_path = os.path.join("skill_agent", "triggers", "triggers.db")
    registry = []
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM skills")
            skills = cursor.fetchall()
            
            for skill_id, name in skills:
                cursor.execute("SELECT trigger_text FROM triggers WHERE skill_id = ?", (skill_id,))
                triggers = [t[0] for t in cursor.fetchall()]
                # Ограничиваем 15 триггерами, чтобы не перегружать контекст модели
                triggers_str = ", ".join(triggers[:15]) if triggers else "универсальный запрос"
                registry.append({
                    "name": name,
                    "description": f"Скилл '{name}'. Триггеры: {triggers_str}",
                    "params": "cmd_line: str"
                })
            conn.close()
        except Exception as e:
            print(f"⚠️ Ошибка чтения БД: {e}")

    # Fallback если БД пуста или недоступна
    if not registry:
        registry = [
            {"name": "git", "description": "Git: init, add, commit, push, pull, status", "params": "cmd_line: str"},
            {"name": "system", "description": "Системные: help, exit, workon, создай скилл", "params": "cmd_line: str"}
        ]
    return registry

def get_ai_decision(cmd_line, ask_ai_fn):
    """🧠 AI-маршрутизатор с динамическим реестром из БД"""
    registry = load_skills_from_db()
    tools_context = "\n".join([f"- {s['name']}: {s['description']}" for s in registry])
    
    prompt = f"""Ты — диспетчер AI-агента. Выбери инструмент по запросу пользователя.

🛠 ДОСТУПНЫЕ ИНСТРУМЕНТЫ (загружены из БД):
{tools_context}

🗣 ЗАПРОС: "{cmd_line}"
📁 Папка: {WORK_DIR}

📋 ИНСТРУКЦИЯ:
1. Если запрос подходит под описание/триггеры инструмента → верни:
   {{"action": "имя_из_списка", "params": {{"cmd_line": "{cmd_line}"}}}}
2. Если это вопрос/болтовня → верни:
   {{"action": "chat", "params": {{"prompt": "{cmd_line}"}}}}
3. ТОЛЬКО валидный JSON, без markdown, без пояснений.

✅ ПРИМЕРЫ:
"зафиксируй изменения" → {{"action": "git", "params": {{"cmd_line": "зафиксируй изменения"}}}}
"создай скилл docker" → {{"action": "system", "params": {{"cmd_line": "создай скилл docker"}}}}
"привет" → {{"action": "chat", "params": {{"prompt": "привет"}}}}

Ответ:"""
    
    raw = ask_ai_fn(prompt).strip()
    raw = re.sub(r'```json\s*', '', raw).replace('```', '').strip()
    
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"⚠️ Ошибка парсинга JSON: {e}")
    
    return {"action": "chat", "params": {"prompt": cmd_line}}

def execute_action(decision, ask_ai_fn):
    """👐 Динамически загружает и вызывает хендлер"""
    action = decision.get("action", "chat")
    params = decision.get("params", {})
    cmd_line = params.get("cmd_line", "")

    if action == "chat":
        print("🤖", ask_ai_fn(params.get("prompt", "")))
        return

    try:
        module = importlib.import_module(f"skill_agent.handlers.{action}")
        handler = getattr(module, f"handle_{action}", None)
        
        if not handler:
            print(f"⚠️ В модуле '{action}' нет функции handle_{action}")
            return
        
        cmd = cmd_line.strip().lower()
        # Адаптер сигнатур: пробуем 3 аргумента → 2 аргумента
        try:
            handler(cmd, cmd_line, ask_ai_fn)
        except TypeError:
            handler(cmd_line, ask_ai_fn)
            
    except ModuleNotFoundError:
        print(f"⚠️ Скилл '{action}' не найден. Попробуй: 'создай скилл {action} для ...'")
    except Exception as e:
        print(f"❌ Ошибка '{action}': {e}")
        print("💡 Попробуй перефразировать или 'help'")

def run_command(cmd_line, ask_ai_fn):
    """Главная точка входа."""
    cmd = cmd_line.strip().lower()
    
    # 🛑 Аварийные команды (без AI, 100% надёжно)
    if cmd in ["exit", "выход", "quit"]:
        print("👋 Пока!"); sys.exit(0)
    if cmd in ["help", "помощь", "?"]:
        print("📖 Я сам решаю, что делать. Просто напиши, что нужно.")
        return

    # 🏭 Фабрика скиллов (жёсткий триггер, обходим AI)
    if any(x in cmd for x in ["создай скилл", "create skill", "новый скилл"]):
        handle_system(cmd, cmd_line, ask_ai_fn)
        return

    # 🤖 Остальное → AI-маршрутизация (реестр берётся из БД)
    decision = get_ai_decision(cmd_line, ask_ai_fn)
    execute_action(decision, ask_ai_fn)