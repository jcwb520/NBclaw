#!/bin/bash
# install.sh - Linux Native

echo "=== NBclaw Linux Installer ==="

# 1. 获取 Token
read -p "请输入 GitHub Personal Access Token: " TOKEN
if [ -z "$TOKEN" ]; then
    echo "Token 不能为空"
    exit 1
fi
read -p "请输入 GitHub 用户名: " USERNAME

REPO="NBclaw"
INSTALL_DIR="$HOME/NBclaw"
REPO_URL="https://${TOKEN}@github.com/${USERNAME}/${REPO}.git"

# 2. 克隆
if [ ! -d "$INSTALL_DIR" ]; then
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
else
    cd "$INSTALL_DIR" && git pull
fi
cd "$INSTALL_DIR"

# 3. 安装依赖（系统级或用户级）
pip3 install --upgrade pip --user
pip3 install -r requirements.txt --user

# 4. 写配置
cat > .env << EOF
GITHUB_USER=$USERNAME
GITHUB_REPO=$REPO
GITHUB_TOKEN=$TOKEN
MODEL=ollama
OLLAMA_MODEL=qwen3:4b
EOF

echo "✅ 安装完成！启动命令: cd $INSTALL_DIR && python3 bootstrap.py"