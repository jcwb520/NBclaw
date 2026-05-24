#!/usr/bin/env python3
"""
NBclaw Bootstrap - 首次运行检测 + 启动配置向导
"""
import os
import sys
from pathlib import Path

# 检查是否首次运行（是否存在 .env 文件）
ENV_FILE = Path(".env")

if not ENV_FILE.exists():
    print("检测到首次运行，启动配置向导...")
    # 运行 github_setup.py
    import github_setup
    github_setup.main()
    print("\n配置完成，请重新启动 NBclaw。")
    sys.exit(0)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 原有 Agent 启动逻辑
def main():
    print("=" * 50)
    print(" NBclaw 智能体启动中...")
    print("=" * 50)
    # TODO: Agent 主循环
    print("✅ NBclaw 已就绪")

if __name__ == "__main__":
    main()