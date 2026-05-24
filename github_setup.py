#!/usr/bin/env python3
"""
NBclaw GitHub 工具 - 创建仓库、验证凭证
"""
import os
import sys
import getpass
import requests
from pathlib import Path

GITHUB_API = "https://api.github.com"


def verify_credentials(token: str) -> str | None:
    """验证 Token，返回用户名或 None"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(f"{GITHUB_API}/user", headers=headers)
    if resp.status_code == 200:
        return resp.json().get("login")
    return None


def create_repo(token: str, repo_name: str = "NBclaw", description: str = "NBclaw - The Self-Evolving AI Agent") -> bool:
    """创建 GitHub 仓库（已存在则跳过）"""
    username = verify_credentials(token)
    if not username:
        print("❌ Token 无效")
        return False

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 检查是否已存在
    check = requests.get(f"{GITHUB_API}/repos/{username}/{repo_name}", headers=headers)
    if check.status_code == 200:
        print(f"ℹ️ 仓库 {username}/{repo_name} 已存在")
        return True

    # 创建
    data = {
        "name": repo_name,
        "description": description,
        "private": False,
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True,
        "auto_init": True  # 自动生成 README
    }
    resp = requests.post(f"{GITHUB_API}/user/repos", headers=headers, json=data)
    if resp.status_code == 201:
        print(f"✅ 仓库 {username}/{repo_name} 创建成功！")
        return True
    else:
        print(f"❌ 创建失败: {resp.json().get('message', '未知错误')}")
        return False


def interactive_setup():
    """交互式配置（首次运行用）"""
    print("=" * 50)
    print(" NBclaw 首次运行配置")
    print("=" * 50)

    token = getpass.getpass("请输入 GitHub 密码 (Personal Access Token): ").strip()
    if not token:
        print("Token 不能为空")
        sys.exit(1)

    username = verify_credentials(token)
    if not username:
        print("❌ Token 无效，请检查后重试")
        sys.exit(1)

    print(f"✅ 登录成功，欢迎 {username}！")

    if not create_repo(token):
        sys.exit(1)

    # 保存 .env
    env_path = Path(".env")
    env_content = f"""GITHUB_USER={username}
GITHUB_REPO=NBclaw
GITHUB_TOKEN={token}
MODEL=ollama
OLLAMA_MODEL=qwen2.5:1.5b
"""
    env_path.write_text(env_content, encoding="utf-8")
    print("✅ 配置文件 .env 已生成")

    print("\n🎉 配置完成！运行 python bootstrap.py 启动智能体")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_setup()
    elif sys.argv[1] == "create":
        # python github_setup.py create <token>
        create_repo(sys.argv[2] if len(sys.argv) > 2 else os.getenv("GITHUB_TOKEN", ""))