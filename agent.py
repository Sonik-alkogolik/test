# agent.py
import sys
import os
import requests

sys.path.append(os.getcwd())

from config import OLLAMA_URL, MODEL_NAME
from skill_agent.router import run_command

def ask_ai(prompt):
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        return res.json()["response"] if res.status_code == 200 else f"Ошибка: {res.status_code}"
    except Exception as e:
        return f"Ошибка подключения: {e}"

if __name__ == "__main__":
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