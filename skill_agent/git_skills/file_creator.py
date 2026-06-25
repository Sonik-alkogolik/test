# file_creator.py
# Скилл: создание/редактирование файлов через AI

import requests
import re
import os
import subprocess
from config import OLLAMA_URL, MODEL_NAME

def create_or_edit_file(file_path, task_description):
    """
    Создаёт или редактирует файл, учитывая его расширение.
    """
    # Определяем язык по расширению
    ext = os.path.splitext(file_path)[1].lower()
    lang_prompt = {
        '.php': "PHP код для Laravel/Moonshine. Используй <?php, namespaces, типизацию.",
        '.py': "Python код. Без <?php, используй def, import, PEP-8.",
        '.js': "JavaScript код. Используй ES6+, модули.",
        '.json': "Валидный JSON, только данные, без кода.",
        '.md': "Markdown разметка.",
    }.get(ext, "Код или текст")

    prompt = f"Напиши {lang_prompt} для файла '{file_path}'. Задача: {task_description}. Верни только код, без обёрток ```."
    
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        raw_code = res.json()["response"]
    except Exception as e:
        return False, f"❌ Ошибка связи с Ollama: {e}"

    # Чистим обёртки
    clean_code = re.sub(r'```(?:php|python|js)?\s*(.*?)\s*```', r'\1', raw_code, flags=re.DOTALL).strip()
    if not clean_code:
        clean_code = raw_code

    # Создаём папки
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    # Бэкап
    if os.path.exists(file_path):
        with open(file_path + ".bak", "w", encoding="utf-8") as f:
            f.write(open(file_path, "r", encoding="utf-8").read())

    # Запись
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(clean_code)

    # Проверка (только для PHP)
    if ext == '.php':
        result = subprocess.run(["php", "-l", file_path], capture_output=True, text=True)
        if "No syntax errors detected" not in result.stdout:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(open(file_path + ".bak", "r", encoding="utf-8").read())
            return False, "❌ PHP синтаксис сломан. Бэкап восстановлен."
    
    return True, f"✅ Файл {file_path} сохранён."