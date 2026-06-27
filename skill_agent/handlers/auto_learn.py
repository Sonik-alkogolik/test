# skill_agent/handlers/auto_learn.py
# 🧠 Автоматическое обучение триггерам через AI

import re
import json
import os
from skill_agent.triggers.triggers_db import add_trigger, add_skill, init_db, get_all_triggers

def handle_auto_learn(cmd, cmd_line, ask_ai_fn):
    triggers = ["автообучение", "auto learn", "обучись", "learn from"]
    if not any(t in cmd_line.lower() for t in triggers):
        return False
    
    # Извлекаем запрос для обучения
    match = re.search(r'(?:автообучение|auto learn|обучись|learn from)\s+(.+?)(?:\s+для\s+(\w+))?', cmd_line, re.IGNORECASE)
    
    if not match:
        print("❌ Формат: автообучение 'запрос' для скилл")
        print("   Пример: автообучение 'покажи погоду' для api_executor")
        return True
    
    user_query = match.group(1).strip()
    skill_name = match.group(2) if match.group(2) else None
    
    # Если скилл не указан — определяем через AI
    if not skill_name:
        prompt = f"""Определи, какой скилл лучше всего подходит для команды: "{user_query}"

Доступные скиллы: api_executor, skill_remover, git, file, system, laravel_server, ping_test, trigger_manager

Верни ТОЛЬКО название скилла."""
        skill_name = ask_ai_fn(prompt).strip().lower()
        print(f"🤖 AI выбрал скилл: {skill_name}")
    
    # Проверяем существование скилла
    if not os.path.exists(f"skill_agent/handlers/{skill_name}.py"):
        print(f"❌ Скилл '{skill_name}' не найден")
        return True
    
    # Получаем существующие триггеры для этого скилла
    existing = []
    try:
        all_triggers = get_all_triggers()
        for name, triggers_list in all_triggers:
            if name == skill_name and triggers_list:
                existing = [t.strip() for t in triggers_list.split(', ')]
                break
    except:
        pass
    
    existing_str = ", ".join(existing) if existing else "нет триггеров"
    
    # Просим модель предложить триггеры
    prompt = f"""Проанализируй запрос пользователя и предложи 3-5 ключевых слов/фраз для триггеров.

ЗАПРОС: "{user_query}"
СКИЛЛ: {skill_name}
СУЩЕСТВУЮЩИЕ ТРИГГЕРЫ: {existing_str}

ПРАВИЛА:
1. Предложи новые триггеры, которых НЕТ в существующих
2. Учитывай синонимы на русском и английском
3. Верни ТОЛЬКО JSON-массив строк

Ответ:"""
    
    print("🧠 Анализирую запрос...")
    raw = ask_ai_fn(prompt).strip()
    
    match_json = re.search(r'\[[\s\S]*\]', raw)
    new_triggers = []
    
    if match_json:
        try:
            new_triggers = json.loads(match_json.group(0))
            if isinstance(new_triggers, list):
                new_triggers = [t.strip().lower() for t in new_triggers if t and isinstance(t, str) and t not in existing]
        except:
            pass
    
    if not new_triggers:
        # Fallback: извлекаем ключевые слова из запроса
        words = re.findall(r'[а-яa-z]+', user_query.lower())
        new_triggers = list(set([w for w in words if len(w) > 2 and w not in existing]))[:5]
    
    if not new_triggers:
        print("❌ Не удалось извлечь триггеры")
        return True
    
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
    
    print(f"✅ Добавлено {count} новых триггеров для '{skill_name}':")
    for t in new_triggers:
        print(f"   • {t}")
    
    print("\n📚 Теперь агент распознаёт эти команды!")
    return True