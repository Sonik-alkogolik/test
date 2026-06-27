# skill_agent/handlers/project_advisor.py
# 🧠 Анализ проекта и рекомендации по улучшению

import os
import re
import json
from skill_agent.state import WORK_DIR

def handle_project_advisor(cmd, cmd_line, ask_ai_fn):
    """
    Анализирует проект и даёт рекомендации по улучшению
    """
    # Проверяем триггеры
    triggers = [
        "улучшить проект", "как улучшить", "оптимизировать проект",
        "project advice", "рекомендации по проекту", "найти слабые места",
        "улучши проект", "советы по проекту"
    ]
    
    if not any(t in cmd_line.lower() for t in triggers):
        return False
    
    # 🎯 Извлекаем путь: берём последнее слово/путь из строки
    parts = cmd_line.split()
    
    # Ищем путь (может содержать \ и /)
    project_path = None
    for part in reversed(parts):
        # Проверяем, похоже ли на путь
        if ':' in part or '/' in part or '\\' in part or os.path.isabs(part):
            project_path = part
            break
        # Проверяем существование (относительный путь)
        if os.path.exists(part):
            project_path = part
            break
    
    # Если путь не найден — используем текущую папку
    if not project_path:
        from skill_agent.state import WORK_DIR
        project_path = WORK_DIR if WORK_DIR != "." else os.getcwd()
    
    # Убираем возможные кавычки
    project_path = project_path.strip('"').strip("'")
    
    # Если путь относительный — делаем абсолютным
    if not os.path.isabs(project_path):
        project_path = os.path.join(os.getcwd(), project_path)
    
    # Нормализуем путь (заменяем / на \ для Windows, но это не обязательно)
    project_path = os.path.normpath(project_path)
    
    if not os.path.exists(project_path):
        print(f"❌ Путь '{project_path}' не найден")
        print("💡 Укажи правильный путь к проекту")
        print("   Пример: как улучшить проект C:/путь/к/проекту")
        return True
    
    print(f"\n🔍 Анализирую проект: {project_path}")
    print("="*60)
    
    # Собираем информацию о проекте
    info = collect_project_info(project_path)
    
    # Формируем промпт для AI
    prompt = f"""Ты — эксперт по оптимизации проектов. Проанализируй проект и дай конкретные рекомендации по улучшению.

📊 ИНФОРМАЦИЯ О ПРОЕКТЕ:
- Путь: {project_path}
- Название: {os.path.basename(project_path)}
- Папок: {info['total_dirs']}
- Файлов: {info['total_files']}
- Основные типы: {info['top_extensions']}
- Технологии: {', '.join(info['technologies'][:5]) if info['technologies'] else 'Не определены'}
- Ключевые файлы: {', '.join(info['key_files'][:10])}
- Фреймворк: {info['framework']}

📝 Задача: Дай 5-7 конкретных рекомендаций по улучшению проекта.
Каждая рекомендация должна быть полезной и конкретной.

Формат ответа:
1. [Краткое название] — [подробное описание и что сделать]

Дополнительно укажи:
- Что можно оптимизировать
- Какие зависимости можно обновить
- Какие практики стоит применить
- Что можно улучшить в архитектуре

Ответ:"""
    
    # Отправляем AI для анализа
    print("🧠 Генерирую рекомендации...")
    print("="*60)
    
    try:
        recommendations = ask_ai_fn(prompt).strip()
        print(f"\n📊 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ ПРОЕКТА:\n")
        print(recommendations)
    except Exception as e:
        print(f"❌ Ошибка получения рекомендаций: {e}")
    
    print("\n" + "="*60)
    
    return True


def collect_project_info(project_path):
    """
    Собирает информацию о проекте
    """
    info = {
        'total_dirs': 0,
        'total_files': 0,
        'extensions': {},
        'key_files': [],
        'technologies': [],
        'top_extensions': '',
        'framework': 'Не определён'
    }
    
    # Ключевые файлы для определения технологий
    tech_map = {
        'composer.json': 'PHP/Laravel',
        'package.json': 'Node.js/Vue/React',
        'artisan': 'Laravel',
        'agent.py': 'Python AI Agent',
        'requirements.txt': 'Python',
        'Dockerfile': 'Docker',
        'Gemfile': 'Ruby on Rails',
        'Cargo.toml': 'Rust',
        'go.mod': 'Go',
        '.gitignore': 'Git'
    }
    
    dirs_scanned = 0
    files_scanned = 0
    
    for root, dirs, files in os.walk(project_path):
        # Пропускаем служебные папки
        if any(x in root for x in ['node_modules', 'vendor', '__pycache__', '.git', 'dist', 'build', '.venv', 'venv']):
            continue
        
        dirs_scanned += 1
        
        for file in files:
            if file.startswith('.'):
                continue
            files_scanned += 1
            ext = os.path.splitext(file)[1] or 'no_ext'
            info['extensions'][ext] = info['extensions'].get(ext, 0) + 1
            
            if file in tech_map:
                if file not in info['key_files']:
                    info['key_files'].append(file)
                tech = tech_map[file]
                if tech not in info['technologies']:
                    info['technologies'].append(tech)
    
    info['total_dirs'] = dirs_scanned
    info['total_files'] = files_scanned
    
    # Определяем фреймворк
    if 'Laravel' in info['technologies'] or 'artisan' in info['key_files']:
        info['framework'] = 'Laravel'
    elif 'composer.json' in info['key_files']:
        info['framework'] = 'PHP (возможно Laravel)'
    elif 'agent.py' in info['key_files']:
        info['framework'] = 'Python AI Agent'
    elif 'package.json' in info['key_files']:
        info['framework'] = 'Node.js/Vue.js'
    
    # Топ расширений
    sorted_ext = sorted(info['extensions'].items(), key=lambda x: x[1], reverse=True)[:5]
    info['top_extensions'] = ', '.join([f"{ext} ({count})" for ext, count in sorted_ext])
    
    return info