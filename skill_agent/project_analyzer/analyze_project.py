# skill_agent/project_analyzer/analyze_project.py
import os
import json

def collect_project_context(root_dir):
    """👐 РУКИ: Собирает сырую структуру проекта без анализа"""
    context = []

    # 1. composer.json
    comp_path = os.path.join(root_dir, "composer.json")
    if os.path.exists(comp_path):
        with open(comp_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                context.append(f"📦 composer.json\nName: {data.get('name')}\nDesc: {data.get('description')}\nReqs: {list(data.get('require', {}).keys())[:10]}")
            except: pass

    # 2. README.md
    readme_path = os.path.join(root_dir, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            context.append(f"📖 README.md\n{f.read()[:1000]}...")

    # 3. Ключевые директории
    scan_dirs = ["app/Models", "app/MoonShine/Resources", "app/Http/Controllers", "routes"]
    for d in scan_dirs:
        full = os.path.join(root_dir, d)
        if os.path.exists(full):
            files = [f for f in os.listdir(full) if f.endswith('.php')]
            context.append(f"📁 {d}\n{', '.join(files[:20])}")

    # 4. Маршруты (фрагмент)
    routes_path = os.path.join(root_dir, "routes/web.php")
    if os.path.exists(routes_path):
        with open(routes_path, 'r', encoding='utf-8') as f:
            context.append(f"🛣️ routes/web.php\n{f.read()[:800]}...")

    return "\n\n".join(context)

def get_project_analysis(root_dir, ask_ai_fn):
    """👐->🧠->👐 Руки собирают -> Мозг думает -> Руки печатают"""
    print(f"📂 Руки: Сканирую {root_dir}...")
    raw_data = collect_project_context(root_dir)

    prompt = f"""Ты — Senior Laravel Architect.
📥 ДАННЫЕ ОТ СКРИПТА (РУКИ):
{raw_data}

🧠 ЗАДАЧА (МОЗГ):
Проанализируй эти данные и напиши краткое описание проекта на русском:
1. Какую бизнес-задачу решает проект?
2. Ключевые технологии и пакеты
3. Архитектура (модели, ресурсы, API)
4. Особенности (MoonShine, админка, очереди и т.д.)
Не выдумывай. Отвечай только по фактам из данных."""

    print("🧠 Мозг: Анализирую...")
    return ask_ai_fn(prompt)