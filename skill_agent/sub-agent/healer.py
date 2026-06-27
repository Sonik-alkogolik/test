# skill_agent/sub-agent/healer.py
import os

def self_heal(error_trace, current_file="", ask_ai_fn=None):
    if not ask_ai_fn: return False
    
    prompt = f"🚨 ОШИБКА: {error_trace[:300]}\n📁 ФАЙЛ: {current_file}\n🔧 Верни ТОЛЬКО исправленный полный код файла. Без пояснений, без markdown."
    
    fix_code = ask_ai_fn(prompt).strip()
    # Очистка от markdown
    fix_code = fix_code.replace("```python", "").replace("```", "").strip()
    
    if len(fix_code) < 20: return False
    print("🛠 Модель вернула фикс. Готов к записи...")
    return fix_code