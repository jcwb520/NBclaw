#!/bin/bash
# NBclaw Linux/macOS 安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.sh | bash

set -e

REPO="jcwb520/NBclaw"
INSTALL_DIR="$HOME/NBclaw"

echo "=== NBclaw 安装器 ==="
echo "安装目录: $INSTALL_DIR"

# 清理旧目录（如果存在）
if [ -d "$INSTALL_DIR" ]; then
    echo "发现旧安装，正在删除..."
    rm -rf "$INSTALL_DIR"
fi

# 克隆仓库
echo "正在克隆 NBclaw..."
git clone "https://github.com/${REPO}.git" "$INSTALL_DIR"

cd "$INSTALL_DIR"

# 创建虚拟环境
echo "正在创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "正在安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 启动引导
echo "正在启动引导程序..."
python bootstrap.py

echo ""
echo "=== 安装完成 ==="
echo "激活环境: cd $INSTALL_DIR && source venv/bin/activate"
echo "启动 NBclaw: python bootstrap.py"