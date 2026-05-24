# install.ps1 - Windows Native (No venv)
param()
$ErrorActionPreference = "Stop"
Write-Host "=== NBclaw Windows Installer (Native) ===" -ForegroundColor Cyan

# 1. 获取 GitHub Token
$TOKEN = Read-Host "请输入 GitHub Personal Access Token"
if (-not $TOKEN) {
    Write-Error "Token 不能为空"
    exit 1
}
$USERNAME = Read-Host "请输入 GitHub 用户名"
$REPO = "NBclaw"
$INSTALL_DIR = "$env:USERPROFILE\NBclaw"
$REPO_URL = "https://$($TOKEN)@github.com/$USERNAME/$REPO.git"

# 2. 克隆仓库
if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "正在克隆仓库..."
    git clone --depth=1 $REPO_URL $INSTALL_DIR
} else {
    Set-Location $INSTALL_DIR
    git pull
}
Set-Location $INSTALL_DIR

# 3. 安装依赖（全局或用户级）
Write-Host "正在安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt --user

# 4. 写入 .env
@"
GITHUB_USER=$USERNAME
GITHUB_REPO=$REPO
GITHUB_TOKEN=$TOKEN
MODEL=ollama
OLLAMA_MODEL=qwen3:4b
"@ | Out-File -Encoding UTF8 .env

Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host "启动命令: cd $INSTALL_DIR ; python bootstrap.py" -ForegroundColor Yellow