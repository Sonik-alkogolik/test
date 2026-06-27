# skill_agent/handlers/learn_triggers.py
# 🧠 Автоматическое обучение триггерам

import re
import json
import os
from skill_agent.triggers.triggers_db import add_trigger, add_skill, init_db

def handle_learn_triggers(cmd, cmd_line, ask_ai_fn):
    # Проверяем триггеры
    triggers = ["обучи триггерам", "learn triggers", "запомни команду", "обучить"]
    if not any(t in cmd_line.lower() for t in triggers):
        return False
    
    # Извлекаем команду для обучения
    match = re.search(r'(?:обучи триггерам|learn triggers|запомни команду|обучить)\s+(.+?)(?:\s+для\s+(\w+))?', cmd_line, re.IGNORECASE)
    
    if not match:
        print("❌ Формат: обучи триггерам 'команда' для скилл")
        print("   Пример: обучи триггерам 'погода в городе' для api_executor")
        return True
    
    command = match.group(1).strip()
    skill_name = match.group(2) if match.group(2) else None
    
    # Если скилл не указан — спрашиваем AI
    if not skill_name:
        prompt = f"""Определи, какой скилл лучше всего подходит для команды: "{command}"

Доступные скиллы: api_executor, skill_remover, git, file, system, laravel_server, ping_test, trigger_manager

Верни ТОЛЬКО название скилла."""
        skill_name = ask_ai_fn(prompt).strip().lower()
        print(f"🤖 AI выбрал скилл: {skill_name}")
    
    # Проверяем, существует ли скилл
    if not os.path.exists(f"skill_agent/handlers/{skill_name}.py"):
        print(f"❌ Скилл '{skill_name}' не найден")
        print("   Доступные скиллы: api_executor, skill_remover, git, file, system, laravel_server, ping_test, trigger_manager")
        return True
    
    # Извлекаем ключевые слова из команды для триггеров
    prompt = f"""Из команды "{command}" извлеки 3-5 ключевых слов/фраз для триггеров.
Верни ТОЛЬКО JSON-массив строк."""
    
    raw = ask_ai_fn(prompt).strip()
    match_json = re.search(r'\[[\s\S]*\]', raw)
    
    new_triggers = []
    if match_json:
        try:
            new_triggers = json.loads(match_json.group(0))
            if isinstance(new_triggers, list):
                new_triggers = [t.strip().lower() for t in new_triggers if t and isinstance(t, str)]
        except:
            pass
    
    if not new_triggers:
        # Fallback: разбиваем команду на слова
        words = re.findall(r'[а-яa-z]+', command.lower())
        new_triggers = list(set([w for w in words if len(w) > 2]))[:5]
    
    # Сохраняем в БД
    init_db()
    add_skill(skill_name, "")
    count = 0
    for t in new_triggers:
        try:
            add_trigger(skill_name, t)
            count += 1
        except:
            pass
    
    print(f"✅ Добавлено {count} триггеров для скилла '{skill_name}':")
    for t in new_triggers:
        print(f"   • {t}")
    
    return True