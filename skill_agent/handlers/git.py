# skill_agent/handlers/git.py
import re
import sqlite3
import os
import subprocess

def _run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip() or r.stderr.strip()

# Рабочие fallback-функции (подменятся импортом, если он есть)
git_init = lambda: _run("git init")
git_add = lambda p=".": _run(f"git add {p}")
git_commit = lambda m: _run(f'git commit -m "{m}"')
git_status = lambda: _run("git status")
git_push = lambda: _run("git push")
git_pull = lambda: _run("git pull")
git_remote_add = lambda u: _run(f"git remote add origin {u}")

try:
    from skill_agent.git_skills.git_skills_add import (
        git_init, git_add, git_commit, git_status, git_push, git_pull, git_remote_add
    )
except ImportError:
    pass  # Оставляем subprocess-версии

def load_git_triggers():
    """Загружает триггеры из БД. Формат в БД: action:слово"""
    db_path = os.path.join("skill_agent", "triggers", "triggers.db")
    triggers = {"commit": [], "restore": [], "push": [], "pull": [], "status": [], "init": []}

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM skills WHERE name = 'git'")
            skill = cursor.fetchone()
            if skill:
                cursor.execute("SELECT trigger_text FROM triggers WHERE skill_id = ?", (skill[0],))
                for (t,) in cursor.fetchall():
                    t = t.strip().lower()
                    if ":" in t:
                        action, keyword = t.split(":", 1)
                        if action in triggers:
                            triggers[action].append(keyword)
                    else:
                        for action in triggers:
                            triggers[action].append(t)
            conn.close()
        except Exception as e:
            print(f"⚠️ Ошибка БД: {e}")
    return triggers

def handle_git(cmd, cmd_line, ask_ai_fn=None):
    cmd_l = cmd_line.lower()
    triggers = load_git_triggers()

    all_t = [t for action in triggers.values() for t in action]
    if not any(t in cmd_l for t in all_t + ["git", "гит"]):
        return False

    # 🔥 COMMIT
    if any(t in cmd_l for t in triggers["commit"]):
        print("📊 Статус:")
        print(git_status())
        msg = "auto update"
        if ask_ai_fn:
            msg = ask_ai_fn(f"Кратко опиши изменения для commit message (1 строка):\n{git_status()[:800]}").strip().replace('"', '') or "auto update"
        print(f"💬 Коммит: \"{msg}\"")
        if input("✅ Закоммитить локально? (y/n): ").strip().lower() in ["y", "да", "+"]:
            git_add(".")
            print(git_commit(msg))
            res = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
            if "origin" in res.stdout:
                if input("🌍 Запушить в origin? (y/n): ").strip().lower() in ["y", "да", "+"]:
                    print(git_push())
            else:
                if input("🔗 Подключить remote? (y/n): ").strip().lower() in ["y", "да", "+"]:
                    url = input("📎 URL: ").strip()
                    if url: print(git_remote_add(url))
                    if input("🚀 Запушить? (y/n): ").strip().lower() in ["y", "да", "+"]: print(git_push())
        return True

    # 🔥 RESTORE
    if any(t in cmd_l for t in triggers["restore"]):
        if input("⚠️ Отменить все несохранённые изменения? (y/n): ").strip().lower() in ["y", "да", "+"]:
            r = subprocess.run("git restore .", shell=True, capture_output=True, text=True)
            if r.returncode != 0: subprocess.run("git checkout -- .", shell=True)
            print("✅ Откачено.")
            print(git_status())
        return True

    if any(t in cmd_l for t in triggers["push"]): print(git_push()); return True
    if any(t in cmd_l for t in triggers["pull"]): print(git_pull()); return True
    if any(t in cmd_l for t in triggers["status"]): print(git_status()); return True
    if any(t in cmd_l for t in triggers["init"]): print(git_init()); return True

    print(git_status())
    return True