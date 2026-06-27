# skill_agent/handlers/skill_remover.py
import os
import re
import sqlite3

def handle_skill_remover(cmd, cmd_line, ask_ai_fn):
    triggers = ["удалить скилл", "remove skill", "удали скилл", "delete skill"]
    if not any(t in cmd_line.lower() for t in triggers):
        return False
    
    match = re.search(r'(?:удалить скилл|remove skill|удали скилл|delete skill)\s+(\w+)', cmd_line, re.IGNORECASE)
    if not match:
        print("❌ Формат: удалить скилл <имя>")
        return True
    
    skill_name = match.group(1)
    print(f"🗑️ Удаляю скилл '{skill_name}'...")
    
    # 1. Удаляем файл
    handler_path = f"skill_agent/handlers/{skill_name}.py"
    if os.path.exists(handler_path):
        os.remove(handler_path)
        print(f"   ✅ Удалён файл: {handler_path}")
    
    # 2. Удаляем триггеры из БД
    try:
        db_path = "skill_agent/triggers/triggers.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM triggers WHERE skill_id=(SELECT id FROM skills WHERE name=?)", (skill_name,))
            cursor.execute("DELETE FROM skills WHERE name=?", (skill_name,))
            conn.commit()
            conn.close()
            print(f"   ✅ Удалены триггеры из БД")
    except Exception as e:
        print(f"   ⚠️ Ошибка БД: {e}")
    
    # 3. Удаляем из router.py
    router_path = "skill_agent/router.py"
    if os.path.exists(router_path):
        with open(router_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = rf'    \{{"name": "{skill_name}",[^}}]*\}},\n?'
        new_content = re.sub(pattern, '', content)
        with open(router_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"   ✅ Удалён из router.py")
    
    # 4. Удаляем из __init__.py
    init_path = "skill_agent/handlers/__init__.py"
    if os.path.exists(init_path):
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = re.sub(rf'from .{skill_name} import handle_{skill_name}\n', '', content)
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"   ✅ Удалён из __init__.py")
    
    print(f"🎉 Скилл '{skill_name}' удалён!")
    return True