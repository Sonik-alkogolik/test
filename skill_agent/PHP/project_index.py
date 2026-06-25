# project_index.py
# Индексатор PHP-файлов проекта. Сохраняет структуру в JSON.

import os
import json

INDEX_FILE = "php_project_map.json"

def build_index(root_dir="."):
    """Сканирует проект, игнорируя vendor/node_modules/.git"""
    print(f"🔍 Индексирую PHP файлы в {root_dir}...")
    php_files = []
    
    for root, dirs, files in os.walk(root_dir):
        for skip in ['vendor', 'node_modules', '.git', '__pycache__']:
            if skip in dirs: dirs.remove(skip)
            
        for file in files:
            if file.endswith(".php"):
                rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                php_files.append(rel_path)
    
    php_files.sort()
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(php_files, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Найдено {len(php_files)} .php файлов. Карта сохранена.")
    return php_files

def load_index():
    if not os.path.exists(INDEX_FILE):
        return []
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_files(query):
    """Поиск по индексу (частичное совпадение)"""
    index = load_index()
    return [f for f in index if query.lower() in f.lower()]