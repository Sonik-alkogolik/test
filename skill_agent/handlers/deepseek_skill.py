import os, sys, re
from deepseek_api import DeepSeekAPI

def handle_deepseek_skill(cmd, cmd_line, ask_ai_fn):
    triggers = ["deepseek", "ds"]
    if not any(t in cmd_line.lower() for t in triggers):
        return False
    question = re.sub(r'^(deepseek|ds)\s*', '', cmd_line, flags=re.IGNORECASE).strip()
    if not question:
        print("❌ Вопрос не указан")
        return True
    try:
        client = DeepSeekAPI()
        response = client.chat(model="deepseek-chat", messages=[{"role": "user", "content": question}])
        print("\n🤖 DeepSeek:", response['choices'][0]['message']['content'])
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return True