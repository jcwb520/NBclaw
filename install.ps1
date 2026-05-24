# install.ps1 - NBclaw Windows 安装脚本
param()

$ErrorActionPreference = "Stop"
$INSTALL_DIR = "$env:USERPROFILE\NBclaw"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  NBclaw 安装器 (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python 已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    Write-Host "   下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# 2. 交互式获取 Token
Write-Host ""
$GH_TOKEN = Read-Host "请输入 GitHub Personal Access Token (Classic PAT)"
while (-not $GH_TOKEN) {
    Write-Host "Token 不能为空" -ForegroundColor Red
    $GH_TOKEN = Read-Host "请输入 GitHub PAT"
}

$GH_USER = Read-Host "请输入 GitHub 用户名"
while (-not $GH_USER) {
    Write-Host "用户名不能为空" -ForegroundColor Red
    $GH_USER = Read-Host "请输入 GitHub 用户名"
}

$REPO_URL = "https://$($TOKEN)@github.com/$USERNAME/NBclaw.git"

# 3. 克隆或更新
if (Test-Path $INSTALL_DIR) {
    Write-Host ""
    Write-Host "📁 NBclaw 已存在，更新中..." -ForegroundColor Yellow
    Set-Location $INSTALL_DIR
    git remote set-url origin "https://${GH_TOKEN}@github.com/${GH_USER}/NBclaw.git"
    git pull origin main 2>$null
} else {
    Write-Host ""
    Write-Host "📥 克隆仓库..." -ForegroundColor Yellow
    git clone --depth=1 "https://${GH_TOKEN}@github.com/${GH_USER}/NBclaw.git" $INSTALL_DIR
    Set-Location $INSTALL_DIR
}

# 4. 安装依赖
Write-Host ""
Write-Host "📦 安装依赖..." -ForegroundColor Yellow
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
Write-Host "✅ 依赖安装完成" -ForegroundColor Green

# 5. 写入 .env
@"
GITHUB_USER=${GH_USER}
GITHUB_REPO=NBclaw
GITHUB_TOKEN=${GH_TOKEN}
MODEL=ollama
OLLAMA_MODEL=qwen2.5:1.5b
"@ | Out-File -Encoding UTF8 .env
Write-Host "✅ 配置文件写入完成" -ForegroundColor Green

# 6. 尝试安装 Ollama（可选）
$ollamaCheck = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaCheck) {
    Write-Host ""
    $installOllama = Read-Host "是否现在安装 Ollama？[y/N]"
    if ($installOllama -eq "y" -or $installOllama -eq "Y") {
        Write-Host "📦 安装 Ollama..." -ForegroundColor Yellow
        irm https://ollama.com/install.ps1 | iex
        Write-Host "🤖 拉取默认模型 qwen2.5:1.5b（可能需要几分钟）..." -ForegroundColor Yellow
        ollama pull qwen2.5:1.5b
        Write-Host "✅ Ollama + 模型安装完成" -ForegroundColor Green
    }
}

# 6b. 创建桌面快捷方式
Write-Host ""
Write-Host "🔗 创建桌面快捷方式..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\NBclaw.lnk")
$Shortcut.TargetPath = "python.exe"
$Shortcut.Arguments = "`"$INSTALL_DIR\bootstrap.py`""
$Shortcut.WorkingDirectory = $INSTALL_DIR
$Shortcut.IconLocation = "shell32.dll,1"
$Shortcut.Description = "NBclaw AI Assistant"
$Shortcut.Save()
Write-Host "✅ 快捷方式已创建！" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "启动命令: cd $INSTALL_DIR ; python bootstrap.py" -ForegroundColor Yellow
Write-Host "桌面快捷方式: NBclaw.lnk" -ForegroundColor Yellow
Write-Host ""