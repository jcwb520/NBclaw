#!/bin/bash
# install.sh - NBclaw Linux/macOS 安装脚本
set -e

INSTALL_DIR="$HOME/NBclaw"
GITHUB_RAW="https://raw.githubusercontent.com"

echo "=========================================="
echo "  NBclaw 安装器 (Linux/macOS)"
echo "=========================================="
echo ""

# 1. 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3.8+"
    exit 1
fi
echo "✅ Python 版本: $(python3 --version)"

# 2. 交互式获取信息
read -p "请输入 GitHub 用户名: " GH_USER
while [ -z "$GH_USER" ]; do
    echo "用户名不能为空，请重新输入:"
    read -p "GitHub 用户名: " GH_USER
done

echo -n "请输入 GitHub Personal Access Token (密码模式输入): "
read -s GH_TOKEN
echo ""
while [ -z "$GH_TOKEN" ]; do
    echo "Token 不能为空"
    echo -n "请输入 GitHub PAT: "
    read -s GH_TOKEN
    echo ""
done

REPO_URL="https://${GH_TOKEN}@github.com/${GH_USER}/NBclaw.git"

# 3. 克隆或更新
if [ -d "$INSTALL_DIR" ]; then
    echo ""
    echo "📁 NBclaw 已存在，更新中..."
    cd "$INSTALL_DIR"
    git remote set-url origin "$REPO_URL"
    git pull origin main 2>/dev/null || echo "⚠️  pull 失败，继续..."
else
    echo ""
    echo "📥 克隆仓库..."
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 4. 安装依赖
echo ""
echo "📦 安装依赖..."
pip3 install --upgrade pip -q
pip3 install -r requirements.txt -q
echo "✅ 依赖安装完成"

# 5. 写入 .env
cat > .env << EOF
GITHUB_USER=${GH_USER}
GITHUB_REPO=NBclaw
GITHUB_TOKEN=${GH_TOKEN}
MODEL=ollama
OLLAMA_MODEL=qwen2.5:1.5b
EOF
echo "✅ 配置文件写入完成"

# 6. 尝试安装 Ollama（可选）
if ! command -v ollama &>/dev/null; then
    echo ""
    echo "⬇️ 检测到 Ollama 未安装，是否现在安装？ [y/N]"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        echo "📦 安装 Ollama（需要 sudo 权限）..."
        curl -fsSL https://ollama.com/install.sh | sh
        echo "🤖 拉取默认模型 qwen2.5:1.5b（可能需要几分钟）..."
        ollama pull qwen2.5:1.5b
        echo "✅ Ollama + 模型安装完成"
    fi
fi

echo ""
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "启动命令:"
echo "  cd $INSTALL_DIR && python3 bootstrap.py"
echo ""
echo "常用命令:"
echo "  install ollama   - 安装 Ollama 框架"
echo "  pull ollama:qwen2.5:7b  - 下载模型"
echo "  absorb <url>     - 从 URL 吸收技能"
echo "  list skills      - 列出技能"
echo "  直接输入文字     - 与 AI 对话"
echo ""
echo "📁 安装目录: $INSTALL_DIR"
echo "📄 文档: $INSTALL_DIR/README.md"
echo ""