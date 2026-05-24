# NBclaw

本地 AI 基础设施管理器 — 框架一键安装 + 模型一键下载 + 对话

## 功能

**框架管理** — 一条命令安装：
- `ollama` — 最流行，本地模型运行核心
- `llama.cpp` — CPU 高效，GGUF 格式支持
- `vllm` — GPU 高吞吐推理
- `lm-studio` — 桌面 GUI
- `jan` — 开源 ChatGPT 替代

**模型下载** — 支持 Ollama / GGUF 双格式：
- qwen2.5 (1.5b / 7b / 14b)
- llama3 / llama3.1 (8b)
- deepseek-r1 (7b / 14b)
- mistral / phi3 / gemma2 / codellama

**对话** — 安装完模型直接聊天，历史上下文保留

**自动同步** — 变更自动 push 到 GitHub

## 快速开始

```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.sh | bash

# Windows PowerShell
iwr https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.ps1 -OutFile install.ps1; .\install.ps1
```

## 命令列表

```
list frames       列出可安装的框架
list models       列出可下载的模型
install <框架名>   安装框架（如: install ollama）
pull <模型ID>     下载模型（如: pull ollama:qwen2.5:7b）
status            查看环境状态
exit              退出
直接输入内容      与 AI 对话
```

## 完整安装流程（推荐）

```
1. install ollama        # 安装 Ollama 框架
2. pull ollama:qwen2.5:7b  # 下载 qwen2.5 7B 模型
3. 重启 Ollama: ollama serve
4. 直接对话
```

## 文件结构

```
bootstrap.py      主程序（框架管理 + 模型下载 + 对话）
github_setup.py   GitHub 仓库创建工具
install.sh        Linux 安装脚本
install.ps1       Windows 安装脚本
requirements.txt   依赖
.env              配置文件（首次运行自动生成）
```