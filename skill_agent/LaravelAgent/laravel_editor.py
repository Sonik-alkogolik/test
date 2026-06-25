# laravel_editor.py
# Адаптер Laravel/Moonshine поверх универсального PHP-редактора

from skill_agent.PHP.php_editor import edit_method
import re

def validate_laravel_context(code, method_name):
    """
    Лёгкая валидация Laravel-кода перед сохранением.
    Можно расширять под Moonshine, Livewire, Filament и т.д.
    """
    warnings = []
    
    # Проверка наличия импортов Illuminate, если используются типизированные аргументы
    if "Request " in code or "Request$" in code:
        if "use Illuminate\\Http\\Request;" not in code:
            warnings.append("️ Используется Request, но нет импорта Illuminate\\Http\\Request")
            
    # Проверка видимости методов в ресурсах Moonshine
    if "Resource" in method_name and "public function" not in code and "protected function" not in code:
        warnings.append("️ В Moonshine Resource методы обычно public/protected")
        
    return warnings

def update_laravel_method(filepath, method_name, new_code, framework="laravel"):
    """
    Обновляет метод с учётом контекста фреймворка.
    Возвращает (success: bool, message: str)
    """
    # 1. Валидация контекста
    warnings = validate_laravel_context(new_code, method_name)
    if warnings:
        warning_msg = "\n".join(warnings)
        print(warning_msg)
        # Можно добавить логику: прервать или продолжить с предупреждением
        # Пока продолжаем, так как код может быть корректным без импортов (если они уже есть в файле)

    # 2. Вызываем базовый PHP-редактор (он сделает бэкап, замену, php -l)
    success, msg = edit_method(filepath, method_name, new_code)
    
    if success:
        return True, f"✅ Laravel метод '{method_name}' обновлён"
    return False, msg