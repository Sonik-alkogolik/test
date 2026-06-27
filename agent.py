# agent.py
import sys
import os
import requests
import subprocess
import time

sys.path.append(os.getcwd())

from config import OLLAMA_URL, MODEL_NAME
from skill_agent.router import run_command

def ensure_ollama_running():
    """Запускает Ollama с моделью в новом окне если не работает"""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            print("✅ Ollama уже работает")
            models = [m["name"] for m in r.json().get("models", [])]
            if not any("qwen2.5-coder:14b" in m for m in models):
                print("📥 Загружаю модель qwen2.5-coder:14b...")
                subprocess.run(["ollama", "pull", "qwen2.5-coder:14b"], check=True)
            return
    except Exception as e:
        print(f"⚠️ Ollama не отвечает: {e}")
    
    print("🚀 Запускаю Ollama в новом окне...")
    # Запускаем только serve (модель подгрузится при первом запросе)
    subprocess.Popen(
        ["powershell", "-NoExit", "-Command", "ollama serve"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    time.sleep(5)
    print("💡 Подожди 10 сек, затем введи команду")

def ask_ai(prompt):
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        return res.json()["response"] if res.status_code == 200 else f"Ошибка: {res.status_code}"
    except Exception as e:
        return f"Ошибка подключения: {e}"

if __name__ == "__main__":
    ensure_ollama_running()
    print("🚀 AI Agent v4.0 (Modular) Ready.")
    while True:
        try:
            cmd = input("\n> ").strip()
            if cmd:
                run_command(cmd, ask_ai)
        except KeyboardInterrupt:
            print("\n👋 Interrupted."); sys.exit(0)
        except Exception as e:
            print(f"💥 Ошибка: {e}")