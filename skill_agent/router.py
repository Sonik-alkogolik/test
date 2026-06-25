# skill_agent/router.py
# Здесь живёт вся логика управления командами

import sys
import os
import json
import re

# Импортируем скиллы прямо здесь
from skill_agent.git_skills.git_skills_add import git_init, git_add, git_commit, git_status, git_push, git_pull
try:
    from skill_agent.git_skills.file_creator import create_or_edit_file
    from skill_agent.self_improve.skill_up import run_skill_up
except ImportError:
    pass

def get_intent(user_text, ask_ai_fn):
    """Распознает намерение через AI (если не сработала точная команда)"""
    prompt = f"""Ты маршрутизатор. Верни JSON: {{"action": "create_file", "target": "файл", "params": "задача"}}
Запрос: {user_text}"""
    try:
        raw = ask_ai_fn(prompt).replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except:
        return {"action": "chat", "target": "", "params": ""}

def run_command(cmd_line, ask_ai_fn):
    """
    Обрабатывает команду пользователя.
    ask_ai_fn — функция для запросов к модели (передается из agent.py)
    """
    # 🔧 Нормализация: приводим всё к нижнему регистру и чистим
    cmd = cmd_line.strip().lower()
    
    # 1. Исправляем опечатки и транслит
    fixes = {
        "сделй": "сделай", "гит": "git", "инит": "init", "адд": "add",
        "пуш": "push", "пулл": "pull", "статус": "status", "чек": "check",
        "закоммить": "commit", "закоммитить": "commit", "закоммичу": "commit",
        "зафиксируй": "commit", "зафиксируйте": "commit", "зафиксируем": "commit", "зафиксировать": "commit",
        "добавь": "add", "добавьте": "add", "добавим": "add", "добавить": "add",
        "сохрани": "commit", "сохраните": "commit", "сохраним": "commit",
        "отправь": "push", "отправьте": "push", "отправим": "push", "залей": "push", "залейте": "push",
        "забери": "pull", "заберите": "pull", "обнови": "pull", "обновите": "pull",
        "инициализируй": "init", "инициализировать": "init"
    }
    for wrong, right in fixes.items():
        cmd = cmd.replace(wrong, right)
    
    # 🔥 ПРИОРИТЕТ 1: Системные команды
    if "skillup" in cmd:
        print("🧠 Запускаю skillUP...")
        if run_skill_up: run_skill_up()
        else: print("❌ Модуль skill_up не загружен!")
        return
    
    if cmd in ["exit", "выход", "quit"]:
        print("👋 Пока!"); sys.exit(0)
    
    if cmd in ["help", "помощь", "?"]:
        print("📖 Команды: skillup, create file X.php with Y, git init/add/commit/push, help, exit")
        return

    # 🔥 ПРИОРИТЕТ 2: Git-команды (максимально гибкий детектор)
    # Проверяем наличие слова "git" ИЛИ русских синонимов + действие
    is_git_cmd = ("git" in cmd) or ("гит" in cmd_line.lower())
    
    if is_git_cmd:
        # Определяем действие по ключевым словам
        if "init" in cmd or "инициализ" in cmd_line.lower():
            print(git_init())
            return
        elif "add" in cmd or "индекс" in cmd_line.lower():
            print(git_add("."))
            return
        elif "commit" in cmd or "фикс" in cmd_line.lower() or "сохран" in cmd_line.lower():
            # Извлекаем сообщение коммита
            msg = "auto update"
            import re
            # Ищем текст в кавычках
            quotes = re.search(r'["\'](.+?)["\']', cmd_line)
            if quotes:
                msg = quotes.group(1)
            else:
                # Если нет кавычек, берём всё после слова "commit" или "зафикси"
                for marker in ["commit", "зафикси", "сохрани"]:
                    if marker in cmd_line.lower():
                        parts = cmd_line.lower().split(marker, 1)
                        if len(parts) > 1:
                            candidate = parts[1].strip().strip('"').strip("'")
                            if candidate and len(candidate) < 100:
                                msg = candidate
                                break
            print(git_commit(msg))
            return
        elif "push" in cmd or "отправ" in cmd_line.lower() or "залей" in cmd_line.lower():
            print(git_push())
            return
        elif "pull" in cmd or "забери" in cmd_line.lower() or "обнов" in cmd_line.lower():
            print(git_pull())
            return
        elif "status" in cmd:
            print(git_status())
            return

    # 🔥 ПРИОРИТЕТ 3: Блокировка случайного создания файлов
    if "create file" not in cmd and "создай файл" not in cmd:
        print("🤖", ask_ai_fn(f"Ответь кратко на: {cmd_line}"))
        return

    # 🔥 ПРИОРИТЕТ 4: Создание файлов через AI
    intent = get_intent(cmd_line, ask_ai_fn)
    action = intent.get("action", "chat")
    target = intent.get("target", "")
    params = intent.get("params", "")

    if action == "create_file":
        print(f"📝 Создаю файл: {target}")
        if create_or_edit_file:
            success, msg = create_or_edit_file(target, params)
            print(msg)
        else:
            print("❌ Модуль file_creator не загружен!")
    else:
        print("🤖", ask_ai_fn(f"Ответь кратко: {cmd_line}"))