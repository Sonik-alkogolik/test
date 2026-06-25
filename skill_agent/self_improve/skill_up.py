# skill_up.py
# Цикл самоулучшения: сканирование → AI-план → безопасное выполнение

import os
import json
import subprocess
import sys
import requests
from config import OLLAMA_URL, MODEL_NAME

def ask_ai(prompt):
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        return res.json()["response"]
    except Exception as e:
        return f"❌ AI Error: {e}"

def scan_structure(root_dir="skill_agent"):
    """Сканирует структуру скиллов (игнорирует __pycache__, .git)"""
    tree = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
        level = root.replace(root_dir, '').count(os.sep)
        indent = "  " * level
        tree.append(f"{indent}📁 {os.path.basename(root)}/")
        for f in files:
            if not f.startswith("__"):
                tree.append(f"{indent}  📄 {f}")
    return "\n".join(tree)

def get_improvement_plan(structure):
    prompt = f"""Ты архитектор AI-агентов. Вот моя структура:
    {structure}
    Предложи 2-3 конкретных улучшения. Верни СТРОГО JSON массив, пример:
    [
    {{"type": "install", "target": "pandas", "reason": "анализ данных"}},
    {{"type": "search", "target": "python best practices", "reason": "улучшить код"}}
    ]
    Только JSON, без текста до и после."""
    
    raw = ask_ai(prompt)
    # Чистим от markdown и лишних символов
    raw = raw.replace("```json", "").replace("```", "").strip()
    
    # Пробуем найти JSON внутри ответа (если модель добавила текст)
    import re
    json_match = re.search(r'\[.*\]', raw, re.DOTALL)
    if json_match:
        raw = json_match.group(0)
    
    try:
        return json.loads(raw)
    except Exception as e:
        print(f"⚠️ Не удалось распарсить JSON: {e}")
        print(f"📄 Сырой ответ: {raw[:200]}...")
        # Возвращаем безопасный fallback
        return [{"type": "text", "target": "Предложи улучшения вручную", "reason": raw[:100]}]

def execute_install(package):
    print(f"📦 pip install {package}...")
    res = subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True, text=True)
    return "✅ Установлено" if res.returncode == 0 else f"❌ {res.stderr[:100]}"

def execute_search(query):
    print(f" Поиск: {query}")
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
        return "\n".join([f"- {r['title']}: {r['href']}" for r in results])
    except ImportError:
        return "⚠️ Нужен duckduckgo-search. Предложи: install duckduckgo-search"
    except Exception as e:
        return f"❌ {str(e)[:100]}"

def run_skill_up():
    print("🧠 Запускаю цикл self-upgrade...")
    struct = scan_structure()
    print("📂 Моя структура:\n" + struct[:500] + ("..." if len(struct) > 500 else ""))
    
    print("\n🤖 Запрашиваю план улучшений...")
    plan = get_improvement_plan(struct)
    
    if not plan:
        print("❌ План не получен. Попробуй позже.")
        return

    print("\n📋 Предложенные улучшения:")
    for i, step in enumerate(plan, 1):
        print(f"{i}. [{step.get('type')}] {step.get('target')} — {step.get('reason')}")
    
    confirm = input("\n🔧 Выполнить? (y/n): ").lower()
    if confirm != 'y':
        print("🛑 Отменено.")
        return

    for step in plan:
        stype = step.get("type")
        target = step.get("target")
        
        if stype == "install":
            print(execute_install(target))
        elif stype == "search":
            print(execute_search(target))
        elif stype == "api_setup":
            print(f"⚙️ Настройка API '{target}' требует ручного вмешательства (безопасность). Пропускаю.")
        else:
            print(f"ℹ️ {step.get('reason')}")
    
    print("\n✅ Цикл завершён. Структура обновлена.")