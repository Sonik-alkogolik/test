# skill_agent/triggers_db.py
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "triggers.db")

def init_db():
    """Создаёт таблицы если их нет"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица навыков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            created_at TEXT
        )
    """)
    
    # Таблица триггеров
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
    
    # Таблица синонимов
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

def add_skill(name, description):
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
    
    # Получаем skill_id
    cursor.execute("SELECT id FROM skills WHERE name = ?", (skill_name,))
    skill = cursor.fetchone()
    if not skill:
        add_skill(skill_name, "")
        cursor.execute("SELECT id FROM skills WHERE name = ?", (skill_name,))
        skill = cursor.fetchone()
    
    # Добавляем триггер
    cursor.execute("""
        INSERT OR IGNORE INTO triggers (skill_id, trigger_text, is_exact)
        VALUES (?, ?, ?)
    """, (skill[0], trigger.lower(), 1 if is_exact else 0))
    
    conn.commit()
    conn.close()

def find_skill_by_trigger(cmd_line):
    """
    🔍 Быстрый поиск навыка по команде
    Возвращает: (skill_name, trigger, confidence)
    """
    cmd_lower = cmd_line.lower()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Ищем точные совпадения
    cursor.execute("""
        SELECT s.name, t.trigger_text, t.use_count
        FROM triggers t
        JOIN skills s ON t.skill_id = s.id
        WHERE t.is_exact = 1 AND ? LIKE '%' || t.trigger_text || '%'
        ORDER BY t.use_count DESC, LENGTH(t.trigger_text) DESC
        LIMIT 1
    """, (cmd_lower,))
    
    result = cursor.fetchone()
    if result:
        # Обновляем счётчик использования
        cursor.execute("""
            UPDATE triggers 
            SET use_count = use_count + 1, last_used = ?
            WHERE trigger_text = ?
        """, (datetime.now().isoformat(), result[1]))
        conn.commit()
        conn.close()
        return (result[0], result[1], 0.95)
    
    # 2. Ищем частичные совпадения (по словам)
    words = cmd_lower.split()
    for word in words:
        if len(word) < 3:
            continue
        cursor.execute("""
            SELECT s.name, t.trigger_text
            FROM triggers t
            JOIN skills s ON t.skill_id = s.id
            WHERE t.trigger_text LIKE ? OR ? LIKE '%' || t.trigger_text || '%'
            LIMIT 1
        """, (f"%{word}%", word))
        result = cursor.fetchone()
        if result:
            conn.close()
            return (result[0], result[1], 0.7)
    
    conn.close()
    return (None, None, 0)

def get_all_triggers():
    """Получить все триггеры для отображения"""
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
    return result

def get_skill_triggers(skill_name):
    """Получить триггеры для конкретного навыка"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.trigger_text
        FROM triggers t
        JOIN skills s ON t.skill_id = s.id
        WHERE s.name = ?
    """, (skill_name,))
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def learn_from_conversation(skill_name, user_phrase, ask_ai_fn):
    """
    🧠 Автообучение: запоминает новые фразы
    """
    # Проверяем, есть ли уже такой триггер
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM triggers t
        JOIN skills s ON t.skill_id = s.id
        WHERE s.name = ? AND t.trigger_text = ?
    """, (skill_name, user_phrase.lower()))
    
    if not cursor.fetchone():
        # Новый триггер!
        add_trigger(skill_name, user_phrase)
        print(f"🧠 Запомнил: '{user_phrase}' → {skill_name}")
    
    conn.close()