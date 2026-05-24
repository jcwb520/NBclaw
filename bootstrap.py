#!/usr/bin/env python3
"""
NBclaw - 技能吸收 + GitHub同步 + 对话主循环
"""
import os
import sys
import time
import git
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class ModelManager:
    def __init__(self):
        self.mode = os.getenv("MODEL", "ollama")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    def get_client(self):
        if self.mode == "ollama":
            return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        return OpenAI()

    def check_ollama(self) -> bool:
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


def sync_with_github():
    """自动同步变更到 GitHub"""
    try:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return
        repo = git.Repo(".")
        remote_url = f"https://{token}@github.com/{os.getenv('GITHUB_USER')}/NBclaw.git"
        repo.remote().set_url(remote_url)
        repo.git.add(A=True)
        if repo.is_dirty(untracked_files=True):
            repo.index.commit(f"Auto-sync: {time.strftime('%Y-%m-%d %H:%M')}")
            repo.remote().push()
            print("🔄 [Sync] Pushed to GitHub")
    except Exception as e:
        print(f"Sync skipped: {e}")


def main():
    print("=" * 50)
    print(" NBclaw 智能体启动中...")
    print("=" * 50)

    # Ollama 前置检测
    mm = ModelManager()
    if not mm.check_ollama():
        print("⚠️ Ollama 未运行")
        print("   Linux/macOS: curl -fsSL https://ollama.com/install.sh | sh")
        print("   Windows: https://ollama.com/download")
        print("   启动后运行: ollama serve")
        sys.exit(1)

    client = mm.get_client()
    print(f"✅ Ollama 已连接 (模型: {mm.model})")
    print("🧠 NBclaw 已启动 (输入 'exit' 退出)")

    while True:
        try:
            sync_with_github()
            user_input = input("You: ").strip()

            if user_input.lower() == "exit":
                break

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