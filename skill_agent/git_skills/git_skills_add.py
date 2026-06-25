# skill_agent/git_skills/git_skills_add.py
# Smart Git Wrapper: авто-инициализация, ветки, push/pull

import os
import subprocess

def _run_git(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = res.stdout.strip()
    err = res.stderr.strip()
    return out if out else err

def git_init(params=""):
    if os.path.exists(".git"):
        return "✅ Репозиторий уже инициализирован."
    return _run_git("git init -b main")

def git_add(params=""):
    path = params.strip() if params.strip() else "."
    res = _run_git(f"git add {path}")
    return res if res else "✅ Файлы добавлены в индекс."

def git_commit(params=""):
    # 🤖 SMART RECOVERY: Если репо нет → init → add → commit
    if not os.path.exists(".git"):
        print("⚠️ Репозиторий не найден. Автоматически: git init -> git add .")
        git_init()
        git_add(".")

    msg = params.strip() if params.strip() else "auto update"
    return _run_git(f'git commit -m "{msg}"')

def git_status(params=""):
    return _run_git("git status")

def git_get_branch(params=""):
    # Берёт ветку напрямую из Git
    branch = _run_git("git branch --show-current")
    return branch if branch else "main"

def git_push(params=""):
    if not os.path.exists(".git"):
        return "❌ Сначала выполните `git init`."

    branch = git_get_branch()
    # Проверяем, привязан ли remote origin
    remote = _run_git("git remote -v")
    if not remote:
        return f"⚠️ Remote 'origin' не привязан. Добавьте: git remote add origin <url>"

    print(f"🚀 Отправляю изменения в ветку: {branch}")
    return _run_git(f"git push origin {branch}")

def git_pull(params=""):
    if not os.path.exists(".git"):
        return "❌ Сначала выполните `git init`."
    branch = git_get_branch()
    return _run_git(f"git pull origin {branch}")