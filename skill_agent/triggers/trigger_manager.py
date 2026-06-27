# skill_agent/handlers/trigger_manager.py
# 🧠 Управление триггерами

import re
import json
import sqlite3
import os
from skill_agent.triggers.triggers_db import (
    get_all_triggers,
    add_trigger,
    add_skill,
    find_skill_by_trigger,
    get_skill_triggers
)

def handle_trigger_manager(cmd, cmd_line, ask_ai_fn):
    """
    Управление триггерами через естественный язык
    """
    cmd_lower = cmd_line.lower()
    
    # ===== 1. ПОКАЗАТЬ ВСЕ ТРИГГЕРЫ =====
    if any(x in cmd_lower for x in ["покажи триггеры", "все триггеры", "show triggers", "список триггеров"]):
        print("\n📋 Триггеры в базе:")
        triggers = get_all_triggers()
        for skill_name, triggers_list in triggers:
            if triggers_list:
                print(f" 🔹 {skill_name}:")
                for t in triggers_list.split(', '):
                    print(f"      • {t}")
            else:
                print(f"  🔸 {skill_name}: (нет триггеров)")
        return True
    
    # ===== 2. ПОКАЗАТЬ ТРИГГЕРЫ ДЛЯ КОНКРЕТНОГО НАВЫКА =====
    if any(x in cmd_lower for x in ["триггеры для", "triggers for"]):
        match = re.search(r'(?:триггеры для|triggers for)\s+(\w+)', cmd_lower)
        if match:
            skill_name = match.group(1)
            triggers = get_skill_triggers(skill_name)
            if triggers:
                print(f"\n🔹 Триггеры для {skill_name}:")
                for t in triggers:
                    print(f"  • {t}")
            else:
                print(f"❌ Навык '{skill_name}' не найден или нет триггеров")
            return True
    
    # ===== 3. ДОБАВИТЬ ТРИГГЕР =====
    if any(x in cmd_lower for x in ["добавь триггер", "add trigger", "новый триггер"]):
        match = re.search(r'(?:добавь триггер|add trigger|новый триггер)\s+["\']?(.+?)["\']?\s+(?:для|for)\s+(\w+)', cmd_line)
        if match:
            trigger, skill_name = match.groups()
            add_trigger(skill_name, trigger)
            print(f"✅ Добавлен триггер '{trigger}' для {skill_name}")
            return True
        else:
            print("❌ Формат: добавь триггер 'текст' для название_скилла")
            return True
    
    # ===== 4. УДАЛИТЬ ТРИГГЕР =====
    if any(x in cmd_lower for x in ["удалить триггер", "delete trigger"]):
        match = re.search(r'(?:удалить триггер|delete trigger)\s+["\']?(.+?)["\']?\s+(?:для|for)\s+(\w+)', cmd_line)
        if match:
            trigger, skill_name = match.groups()
            db_path = os.path.join("skill_agent", "triggers", "triggers.db")
            if not os.path.exists(db_path):
                db_path = "skill_agent/triggers/triggers.db"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM triggers 
                WHERE skill_id = (SELECT id FROM skills WHERE name = ?) 
                AND trigger_text = ?
            """, (skill_name, trigger.lower()))
            conn.commit()
            conn.close()
            print(f"✅ Удалён триггер '{trigger}' для {skill_name}")
            return True
        else:
            print("❌ Формат: удалить триггер 'текст' для название_скилла")
            return True
    
    # ===== 5. СПРОСИТЬ У МОДЕЛИ О ТРИГГЕРАХ =====
    if any(x in cmd_lower for x in ["спроси у модели", "предложи триггеры"]):
        match = re.search(r'(?:для|for)\s+(\w+)', cmd_line)
        if match:
            skill_name = match.group(1)
            existing = get_skill_triggers(skill_name)
            existing_str = ", ".join(existing) if existing else "нет триггеров"
            
            prompt = f"""Предложи 5-10 новых триггеров для скилла {skill_name}.
Существующие триггеры: {existing_str}
Верни ТОЛЬКО JSON-массив строк."""
            
            print("🧠 Спрашиваю модель...")
            raw = ask_ai_fn(prompt).strip()
            clean = re.sub(r'```(?:json)?\s*', '', raw).replace('```', '').strip()
            
            try:
                match_json = re.search(r'\[[\s\S]*\]', clean)
                if match_json:
                    new_triggers = json.loads(match_json.group(0))
                    print(f"\n💡 Модель предложила для {skill_name}:")
                    for t in new_triggers:
                        print(f"  • {t}")
                    
                    print("\n➡️ Добавить все? (да/нет)")
                    if input("> ").strip().lower() in ["да", "yes", "д"]:
                        for t in new_triggers:
                            add_trigger(skill_name, t)
                        print(f"✅ Добавлено {len(new_triggers)} триггеров")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            return True
    
    # ===== 6. ПОМОЩЬ =====
    if any(x in cmd_lower for x in ["помощь триггеры", "help triggers"]):
        print("""
📖 Команды для управления триггерами:

  • покажи триггеры                    — все триггеры
  • триггеры для ping_test              — триггеры конкретного навыка
  • добавь триггер 'текст' для ping_test — добавить триггер
  • удалить триггер 'текст' для ping_test — удалить триггер
  • предложи триггеры для ping_test     — AI предложит триггеры
""")
        return True
    
    return False