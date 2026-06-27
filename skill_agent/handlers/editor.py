# skill_agent/handlers/editor.py
import re
import os
from skill_agent.state import WORK_DIR

# Импортируем базовый PHP-редактор
try:
    from skill_agent.PHP.php_editor import edit_method
except ImportError:
    edit_method = None

def handle_edit_method(cmd, cmd_line, ask_ai_fn):
    # 🔍 Отладка: раскомментируй если нужно
    # print(f"🔍 DEBUG: cmd='{cmd}'")
    
    # Триггеры (должны быть в cmd после нормализации)
    triggers = ["отредактируй метод", "измени метод", "обнови метод", "редактируй метод", "поменяй метод"]
    if not any(t in cmd for t in triggers):
        return False

    print("✏️ Режим редактирования метода активирован")

    # Извлекаем имя метода и целевой класс/файл
    # Поддерживаем варианты:
    # - "отредактируй метод replyField в SupportTicketResource"
    # - "измени метод index в ProductController"
    # - "обнови метод replyField" (попробуем найти файл по имени метода)
    
    method_name = None
    target_name = None
    
    # Паттерн 1: метод <name> в <Target>
    match = re.search(r'метод\s+([a-zA-Z_]\w*)\s+(?:в\s+)?([a-zA-Z_]\w*)', cmd_line, re.IGNORECASE)
    if match:
        method_name = match.group(1)
        target_name = match.group(2)
    
    # Паттерн 2: только метод <name> (попробуем найти по всему проекту)
    elif re.search(r'метод\s+([a-zA-Z_]\w*)', cmd_line, re.IGNORECASE):
        method_name = re.search(r'метод\s+([a-zA-Z_]\w*)', cmd_line, re.IGNORECASE).group(1)
        print(f"⚠️ Файл не указан, буду искать метод '{method_name}' по всему проекту...")
    
    if not method_name:
        print("⚠️ Не удалось определить имя метода. Пример: отредактируй метод replyField в SupportTicketResource")
        return True

    # Ищем файл
    file_path = None
    search_dir = WORK_DIR if WORK_DIR != "." else "."
    
    if target_name:
        # Ищем точное совпадение имени файла
        for root, _, files in os.walk(search_dir):
            for f in files:
                if f == f"{target_name}.php" or f.endswith(f"{target_name}Resource.php") or f.endswith(f"{target_name}Controller.php"):
                    file_path = os.path.join(root, f)
                    break
            if file_path: break
    
    # Если не нашли по target_name или его не было — ищем по имени метода внутри файлов
    if not file_path:
        print(f"🔍 Ищу файл, содержащий метод '{method_name}'...")
        for root, _, files in os.walk(search_dir):
            # Пропускаем тяжелые папки
            if any(skip in root for skip in ['vendor', 'node_modules', '.git', '__pycache__']):
                continue
            for f in files:
                if not f.endswith('.php'): continue
                fp = os.path.join(root, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        content = fh.read()
                        # Ищем сигнатуру метода
                        if re.search(rf'(?:public|private|protected)\s+function\s+{re.escape(method_name)}\s*\(', content):
                            file_path = fp
                            print(f"✅ Нашёл в: {file_path}")
                            break
                except: pass
            if file_path: break

    if not file_path:
        print(f"❌ Файл с методом '{method_name}' не найден в {WORK_DIR}/")
        return True

    # 🧠 Запрашиваем у модели НОВЫЙ код метода
    print(f"🧠 Запрашиваю новый код для метода '{method_name}'...")
    prompt = f"""Ты эксперт по PHP/Laravel. Напиши ТОЛЬКО код метода '{method_name}' для файла '{file_path}'.
Правила:
1. Верни только код метода (с сигнатурой function ...), без <?php, namespace, class.
2. Сохрани существующую сигнатуру (видимость, аргументы, return type), если не просили изменить.
3. Код должен быть валидным PHP 8.2+.

Пример ответа:
private function replyField(): Textarea
{{
    return Textarea::make('Ответ', 'admin_response')->required();
}}"""
    
    new_code = ask_ai_fn(prompt).strip()
    # Чистим markdown-обёртки
    new_code = re.sub(r'```(?:php)?\s*(.*?)\s*```', r'\1', new_code, flags=re.DOTALL).strip()
    
    if not new_code or len(new_code) < 20:
        print("⚠️ Модель вернула пустой или слишком короткий код. Попробуй уточнить задачу.")
        return True

    # 🔧 Вызываем PHP-редактор (бэкап + замена + php -l)
    print(f"✏️ Заменяю метод '{method_name}' в {os.path.basename(file_path)}...")
    
    if edit_method:
        success, msg = edit_method(file_path, method_name, new_code)
        print(msg)
    else:
        print("❌ Модуль php_editor не загружен! Проверь skill_agent/PHP/php_editor.py")
    
    return True