# skill_agent/handlers/ping_test.py
# Auto-generated: выполнения ping 8.8.8.8 при команде пропингуй
# Triggers: пропингуй, пинг, ping, 8.8.8.8
# Created: 2026-06-25 17:27:39

import subprocess
import os

def handle_ping_test(cmd, cmd_line, ask_ai_fn):
    """
    Выполняет ping 8.8.8.8 при команде пропингуй
    """
    # Проверяем триггеры
    triggers = ["пропингуй", "пинг", "ping", "8.8.8.8"]
    if not any(t in cmd_line.lower() for t in triggers):
        return False
    
    try:
        # Определяем ОС для правильной команды ping
        is_windows = os.name == 'nt'
        
        if is_windows:
            ping_cmd = ['ping', '8.8.8.8', '-n', '4']
        else:
            ping_cmd = ['ping', '-c', '4', '8.8.8.8']
        
        print(f"🔄 Выполняю: {' '.join(ping_cmd)}")
        
        result = subprocess.run(
            ping_cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print("✅ Ping успешен:")
            print(result.stdout)
        else:
            print("❌ Ping не удался:")
            print(result.stderr or result.stdout)
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Таймаут выполнения ping")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return True