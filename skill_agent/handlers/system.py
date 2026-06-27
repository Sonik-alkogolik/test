# skill_agent/handlers/system.py
import sys
import os
import re
import subprocess
from datetime import datetime
from skill_agent.state import WORK_DIR

# ================= ИМПОРТЫ СКИЛЛОВ =================
try:
    from skill_agent.self_improve.skill_up import run_skill_up
except ImportError:
    run_skill_up = None

try:
    from skill_agent.skill_factory.skill_creator import create_universal_skill
    print("✅ [System] Фабрика скиллов v5.0 загружена")
except Exception as e:
    print(f"⚠️ [System] Фабрика скиллов: {e}")
    create_universal_skill = None

def analyze_project(project_path, ask_ai_fn=None):
    """📊 Анализирует структуру проекта через AI"""
    if not os.path.exists(project_path):
        return f"❌ Папка '{project_path}' не найдена"
    
    print(f"\n📊 Анализирую проект: {project_path}")
    print("="*60)
    print("📂 Сканирую структуру...")
    
    total_files = 0
    total_dirs = 0
    key_files_found = []
    key_files = {
        "composer.json": "PHP/Laravel",
        "package.json": "Node.js/Vue/React",
        "artisan": "Laravel",
        "agent.py": "Python AI Agent"
    }
    
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ['node_modules', 'vendor', '__pycache__', '.git']]
        total_dirs += 1
        for f in files:
            if f in key_files:
                key_files_found.append(f"{f} ({key_files[f]})")
            total_files += 1
            
    prompt = f"""Ты эксперт по архитектуре ПО. Кратко опиши проект по данным:
- Папка: {os.path.basename(project_path)}
- Файлов: {total_files}, Папок: {total_dirs}
- Ключевые файлы: {', '.join(key_files_found[:5])}
Напиши 3-4 предложения: что это за проект и его стек."""

    try:
        return ask_ai_fn(prompt).strip()
    except:
        return "⚠️ Не удалось получить описание."


def handle_system(cmd, cmd_line, ask_ai_fn):
    global WORK_DIR

    # 1️⃣ Анализ проекта
    if "проанализируй проект" in cmd_line.lower() or "analyze project" in cmd_line.lower():
        target = WORK_DIR if WORK_DIR != "." else os.getcwd()
        if not os.path.isabs(target): target = os.path.join(os.getcwd(), target)
        result = analyze_project(target, ask_ai_fn)
        print(f"\n📋 Результат:\n{result}")
        return True

    # 2️⃣ SkillUP
    if "skillup" in cmd:
        print("🧠 Запускаю skillUP...")
        if run_skill_up: run_skill_up()
        else: print("❌ Модуль skill_up не загружен!")
        return True

    # 3️⃣ Exit
    if cmd in ["exit", "выход", "quit"]:
        print("👋 Пока!")
        sys.exit(0)

    # 4️⃣ Help
    if cmd in ["help", "помощь", "?"]:
        print("📖 Команды:")
        print("  • workon <папка>              — выбрать проект")
        print("  • analyze project             — анализ проекта")
        print("  • создай скилл <имя> для <описание> — создать новый скилл (v5.0)")
        print("  • help / exit                 — справка / выход")
        return True

    # 5️⃣ Workon
    if "workon" in cmd or cmd.startswith("cd ") or "перейди в" in cmd_line.lower():
        folder = cmd_line.replace("workon", "").replace("cd ", "").replace("перейди в", "").strip()
        if "showcase" in folder.lower(): folder = "showcase-designer"
        folder = folder.strip('"').strip("'")
        if os.path.exists(folder):
            WORK_DIR = folder
            print(f"✅ Рабочая папка: {WORK_DIR}/")
        else:
            print(f"⚠️ Папка '{folder}' не найдена.")
        return True

    # 6️⃣ 🏭 УНИВЕРСАЛЬНАЯ ФАБРИКА СКИЛЛОВ v5.0
    if any(x in cmd_line.lower() for x in ["создай скилл", "create skill", "новый скилл"]):
        print("🏭 Запуск фабрики скиллов v5.0...")
        
        # Парсинг: "создай скилл <имя> для <описание>"
        match = re.search(r'скилл\s+(\w+)\s+(?:для\s+)?(.+)', cmd_line, re.IGNORECASE)
        if match:
            name, desc = match.group(1), match.group(2).strip()
        else:
            print("⚠️ Формат: 'создай скилл <имя> для <описание>'")
            print("   Пример: 'создай скилл docker для управления контейнерами'")
            return True
        
        print(f"📝 Имя: '{name}', Описание: '{desc}'")
        
        if create_universal_skill:
            create_universal_skill(name, desc, ask_ai_fn, project_root=WORK_DIR if WORK_DIR != "." else ".")
        else:
            print("❌ Модуль create_universal_skill не найден")
        return True

    return False