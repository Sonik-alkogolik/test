# skill_agent/populate_triggers.py
# 🚀 Заполнение базы триггеров для существующих навыков

import sqlite3
import os
import re
from datetime import datetime

DB_PATH = "skill_agent/triggers.db"

def init_db():
    """Создаёт таблицы если их нет"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            created_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER,
            trigger_text TEXT,
            is_exact INTEGER DEFAULT 1,
            use_count INTEGER DEFAULT 0,
            last_used TEXT,
            FOREIGN KEY (skill_id) REFERENCES skills (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trigger_synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_id INTEGER,
            synonym TEXT,
            FOREIGN KEY (trigger_id) REFERENCES triggers (id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def add_skill(name, description=""):
    """Добавляет новый навык"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO skills (name, description, created_at) VALUES (?, ?, ?)",
        (name, description, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def add_trigger(skill_name, trigger, is_exact=True):
    """Добавляет триггер для навыка"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM skills WHERE name = ?", (skill_name,))
    skill = cursor.fetchone()
    if not skill:
        add_skill(skill_name, "")
        cursor.execute("SELECT id FROM skills WHERE name = ?", (skill_name,))
        skill = cursor.fetchone()
    
    trigger_lower = trigger.lower().strip()
    cursor.execute("""
        INSERT OR IGNORE INTO triggers (skill_id, trigger_text, is_exact)
        VALUES (?, ?, ?)
    """, (skill[0], trigger_lower, 1 if is_exact else 0))
    
    conn.commit()
    conn.close()

def populate_from_skills():
    """
    Заполняет базу триггерами из существующих навыков
    """
    print("📊 Заполняю базу триггеров...")
    
    # ✅ БАЗОВЫЕ НАВЫКИ И ИХ ТРИГГЕРЫ
    skills_triggers = {
        "git": {
            "description": "Работа с Git: init, add, commit, push, pull, status",
            "triggers": [
                "git", "гит", "коммит", "commit", "запушь", "push", 
                "pull", "статус", "status", "добавь в гит", "add",
                "закоммитить", "commit changes", "git init"
            ]
        },
        "file": {
            "description": "Создание или редактирование файлов с кодом",
            "triggers": [
                "создай файл", "новый файл", "create file", 
                "отредактируй файл", "edit file", "сохрани код",
                "запиши в файл", "write file", "сделай файл"
            ]
        },
        "edit_method": {
            "description": "Точечное редактирование метода в PHP файле",
            "triggers": [
                "отредактируй метод", "измени функцию", "обнови метод",
                "исправь метод", "edit method", "update function",
                "поменяй функцию", "перепиши метод"
            ]
        },
        "system": {
            "description": "Системные команды: help, exit, workon, skillup, analyze project",
            "triggers": [
                "помощь", "help", "выход", "exit", "workon",
                "skillup", "анализ", "analyze", "прочитай проект",
                "перейди в", "создай скилл", "create skill"
            ]
        },
        "laravel_server": {
            "description": "Запуск php artisan serve",
            "triggers": [
                "запусти сервер", "artisan serve", "php artisan",
                "запусти laravel", "start server", "serve",
                "запусти проект", "запусти локально"
            ]
        },
        "ping_test": {
            "description": "Выполнение ping 8.8.8.8",
            "triggers": [
                "пропингуй", "пинг", "ping", "проверь связь",
                "ping 8.8.8.8", "пропинговать", "check connection"
            ]
        }
    }
    
    # Добавляем навыки и триггеры
    for skill_name, data in skills_triggers.items():
        add_skill(skill_name, data["description"])
        for trigger in data["triggers"]:
            add_trigger(skill_name, trigger)
        print(f"  ✅ {skill_name}: {len(data['triggers'])} триггеров")
    
    print("\n🎉 База триггеров заполнена!")

def show_all_triggers():
    """Показывает все триггеры в базе"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.name, GROUP_CONCAT(t.trigger_text, ', ')
        FROM skills s
        LEFT JOIN triggers t ON s.id = t.skill_id
        GROUP BY s.id
    """)
    result = cursor.fetchall()
    conn.close()
    
    print("\n📋 Текущие триггеры в базе:")
    for skill_name, triggers in result:
        if triggers:
            print(f"  🔹 {skill_name}: {triggers}")
        else:
            print(f"  🔸 {skill_name}: (нет триггеров)")

def get_skill_by_trigger(cmd_line):
    """
    🔍 Быстрый поиск навыка по команде
    """
    cmd_lower = cmd_line.lower()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ищем точные совпадения
    cursor.execute("""
        SELECT s.name, t.trigger_text
        FROM triggers t
        JOIN skills s ON t.skill_id = s.id
        WHERE t.is_exact = 1 AND ? LIKE '%' || t.trigger_text || '%'
        ORDER BY LENGTH(t.trigger_text) DESC
        LIMIT 1
    """, (cmd_lower,))
    
    result = cursor.fetchone()
    conn.close()
    return result

# ============= ЗАПУСК =============
if __name__ == "__main__":
    print("🚀 Инициализация базы триггеров...")
    init_db()
    populate_from_skills()
    show_all_triggers()
    
    # Тест поиска
    print("\n🧪 Тест поиска:")
    test_commands = [
        "пропингуй 8.8.8.8",
        "запушь изменения",
        "создай файл test.php",
        "запусти сервер"
    ]
    for cmd in test_commands:
        result = get_skill_by_trigger(cmd)
        if result:
            print(f"  ✅ '{cmd}' → {result[0]} (триггер: {result[1]})")
        else:
            print(f"  ❌ '{cmd}' → не найдено")