#!/usr/bin/env python3
"""
NBclaw GitHub Setup - 自动创建仓库 + 初始化代码
"""
import os
import sys
import getpass
import subprocess
import shlex
import requests
from pathlib import Path

GITHUB_API = "https://api.github.com"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("=" * 50)
    print(" NBclaw 首次运行配置向导")
    print("=" * 50)
    print("我将帮你创建 GitHub 仓库并初始化代码。")
    print("注意：请输入 GitHub 用户名和 Personal Access Token。")
    print(" Token 需要 repo 权限。")
    print("-" * 50)

def get_credentials():
    """获取 GitHub 用户名和 Token"""
    username = input("请输入 GitHub 用户名: ").strip()
    token = getpass.getpass("请输入 GitHub 密码 (Personal Access Token): ").strip()
    return username, token

def verify_credentials(username, token):
    """验证 GitHub 凭证"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(f"{GITHUB_API}/user", headers=headers)
    if resp.status_code == 200:
        print(f"✅ 登录成功，欢迎 {resp.json().get('login')}!")
        return True
    else:
        print(f"❌ 登录失败: {resp.json().get('message', '未知错误')}")
        return False

def create_repo(username, token, repo_name="NBclaw"):
    """创建 GitHub 仓库"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    # 检查仓库是否已存在
    check_resp = requests.get(f"{GITHUB_API}/repos/{username}/{repo_name}", headers=headers)
    if check_resp.status_code == 200:
        print(f"ℹ️ 仓库 {repo_name} 已存在，跳过创建。")
        return True

    # 创建新仓库
    data = {
        "name": repo_name,
        "description": "NBclaw - The Self-Evolving AI Agent",
        "private": False,
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True
    }
    resp = requests.post(f"{GITHUB_API}/user/repos", headers=headers, json=data)
    if resp.status_code == 201:
        print(f"✅ 仓库 {repo_name} 创建成功！")
        return True
    else:
        print(f"❌ 创建仓库失败: {resp.json().get('message')}")
        return False

def run_git(cmd, cwd=None):
    """安全的 git 命令执行"""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )
    return result.returncode, result.stdout, result.stderr

def init_local_repo(username, token, repo_name="NBclaw"):
    """初始化本地仓库并推送"""
    repo_path = Path.cwd()

    # 配置 git 用户信息
    run_git('git config --global user.email "nbclaw@auto.local"', cwd=repo_path)
    run_git('git config --global user.name "NBclaw Auto Setup"', cwd=repo_path)

    # 初始化 git 仓库
    if not (repo_path / ".git").exists():
        run_git("git init", cwd=repo_path)
        print("✅ 初始化 Git 仓库")

    # 切换到 main 分支
    run_git("git branch -M main", cwd=repo_path)

    # 添加远程仓库（使用 HTTPS + Token 方式）
    remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    # 先移除旧的 origin（如果存在）
    run_git(f"git remote remove origin 2>/dev/null; git remote add origin {shlex.quote(remote_url)}", cwd=repo_path)

    # 创建初始文件
    files_to_create = {
        "README.md": f"# {repo_name}\n\nThe Self-Evolving AI Agent.\n",
        ".gitignore": "__pycache__/\n*.pyc\n.env\n.venv/\nvenv/\n",
        "requirements.txt": "openai>=1.30.0\npython-dotenv>=1.0.0\nGitPython>=3.1.43\nrequests>=2.31.0\n",
        "bootstrap.py": "# Bootstrap 入口文件\nfrom pathlib import Path\n\nENV_FILE = Path('.env')\nif not ENV_FILE.exists():\n    print('首次运行请配置 GitHub 凭证')\n    # TODO: 启动配置向导\n",
        ".github/": ""
    }

    for name, content in files_to_create.items():
        filepath = repo_path / name
        if name.endswith("/"):
            filepath.mkdir(parents=True, exist_ok=True)
        elif not filepath.exists():
            filepath.write_text(content, encoding="utf-8")

    # 提交
    run_git("git add .", cwd=repo_path)
    run_git('git commit -m "Initial commit by NBclaw setup"', cwd=repo_path)

    # 推送
    code, out, err = run_git("git push -u origin main --force", cwd=repo_path)
    if code == 0:
        print(f"✅ 代码已推送到 GitHub: https://github.com/{username}/{repo_name}")
    else:
        print(f"⚠️ 推送遇到问题: {err}")

def save_env_file(username, token, repo_name="NBclaw"):
    """保存 .env 文件"""
    env_content = f"""GITHUB_USER={username}
GITHUB_REPO={repo_name}
GITHUB_TOKEN={token}
MODEL=ollama
OLLAMA_MODEL=qwen2.5:1.5b
"""
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    print("✅ 配置文件 .env 已生成")

def main():
    """主设置流程"""
    clear_screen()
    print_banner()

    # 1. 获取凭证
    username, token = get_credentials()

    # 2. 验证凭证
    if not verify_credentials(username, token):
        print("❌ 凭证无效，请重新运行 setup。")
        sys.exit(1)

    # 3. 创建仓库
    if not create_repo(username, token):
        print("❌ 仓库创建失败，请检查权限。")
        sys.exit(1)

    # 4. 初始化本地仓库并推送
    init_local_repo(username, token)

    # 5. 保存配置
    save_env_file(username, token)

    print("\n" + "=" * 50)
    print("🎉 NBclaw 初始化完成！")
    print("现在可以启动智能体了。")
    print("=" * 50)

if __name__ == "__main__":
    main()