#!/bin/bash
# NBclaw Linux 安装脚本
# 用法: bash install.sh

set -e

INSTALL_DIR="$HOME/NBclaw"
GITHUB_RAW="https://raw.githubusercontent.com"

echo "=== NBclaw Linux 安装器 ==="
echo ""

# 1. 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3.8+"
    exit 1
fi

# 2. 交互式获取 Token
read -p "请输入 GitHub 用户名: " GH_USER
read -sp "请输入 GitHub 密码 (Personal Access Token): " GH_TOKEN
echo ""

if [ -z "$GH_TOKEN" ]; then
    echo "❌ Token 不能为空"
    exit 1
fi

REPO_URL="https://${GH_TOKEN}@github.com/${GH_USER}/NBclaw.git"

# 3. 克隆或更新
if [ -d "$INSTALL_DIR" ]; then
    echo "📁 NBclaw 已存在，更新中..."
    cd "$INSTALL_DIR"
    git pull "$REPO_URL" main 2>/dev/null || true
else
    echo "📥 克隆仓库..."
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 4. 安装依赖
echo "📦 安装依赖..."
pip3 install --upgrade pip -q
pip3 install -r requirements.txt -q

# 5. 写入 .env
cat > .env << EOF
GITHUB_USER=${GH_USER}
GITHUB_REPO=NBclaw
GITHUB_TOKEN=${GH_TOKEN}
MODEL=ollama
OLLAMA_MODEL=qwen2.5:1.5b
EOF

echo ""
echo "✅ 安装完成！"
echo "启动命令: cd $INSTALL_DIR && python3 bootstrap.py"