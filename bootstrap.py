#!/usr/bin/env python3
"""
NBclaw Bootstrap - 技能吸收 + GitHub同步 + 对话主循环
"""
import os
import sys
import time
import git
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# 技能吸收模块
from repo_importer import repo_importer

load_dotenv()


class ModelManager:
    def __init__(self):
        self.mode = os.getenv("MODEL", "ollama")
        self.model = os.getenv("OLLAMA_MODEL", "qwen3:4b")

    def get_client(self):
        if self.mode == "ollama":
            return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        return OpenAI()

    def check_ollama(self) -> bool:
        """检查 Ollama 是否运行"""
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


def sync_with_github():
    """自动同步到 GitHub"""
    try:
        token = os.getenv("GITHUB_TOKEN")
        repo = git.Repo(".")
        if token:
            remote_url = f"https://{token}@github.com/{os.getenv('GITHUB_USER')}/NBclaw.git"
            repo.remote().set_url(remote_url)
            repo.git.add(A=True)
            if repo.is_dirty(untracked_files=True):
                repo.index.commit(f"Auto-sync: {time.strftime('%Y-%m-%d %H:%M')}")
                repo.remote().push()
                print("🔄 [Sync] Pushed to GitHub")
    except Exception as e:
        print(f"Sync skipped: {e}")


def handle_command(user_input: str) -> bool:
    """处理命令"""
    if user_input.startswith("absorb "):
        url = user_input.split(" ", 1)[1].strip()
        print(f"🧠 吸收技能: {url}")
        result = repo_importer.absorb(url)
        print(f"✅ {result.get('message', '完成')}")
        return True

    if user_input == "list skills":
        skills = repo_importer.list_skills()
        for s in skills:
            print(f" • {s['name']} ({s['status']})")
        return True

    return False


def check_prerequisites():
    """前置检测"""
    # Ollama 检测
    mm = ModelManager()
    if not mm.check_ollama():
        print("⚠️ Ollama 未运行，请先安装并启动 Ollama")
        print("   Linux/macOS: curl -fsSL https://ollama.com/install.sh | sh")
        print("   Windows: https://ollama.com/download")
        print("   启动后: ollama serve")
        return False
    return True


def main():
    print("=" * 50)
    print(" NBclaw 智能体启动中...")
    print("=" * 50)

    if not check_prerequisites():
        sys.exit(1)

    mm = ModelManager()
    client = mm.get_client()
    print(f"✅ Ollama 已连接 (模型: {mm.model})")
    print("🧠 NBclaw 已启动 (输入 'exit' 退出)")

    while True:
        try:
            sync_with_github()
            user_input = input("You: ").strip()

            if user_input.lower() == "exit":
                break

            if handle_command(user_input):
                continue

            # 普通对话
            response = client.chat.completions.create(
                model=mm.model,
                messages=[{"role": "user", "content": user_input}]
            )
            print("Bot:", response.choices[0].message.content)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    main()