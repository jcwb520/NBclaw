# NBclaw 🦶 — 本地 AI 基础设施管理器

> **「我把它扔到 GitHub，别的智能体拿到链接就能一键装到自己电脑上。」**
>
> **Windows 双击即用 · Linux 一行命令 · 硬件自动侦察 · 模型自动推荐**

---

## ⭐ v1.0.0 新特性

### 🖥️ 桌面客户端（重磅）
- **Windows 原生 exe**：双击即用，无需安装 Python 环境
- **硬件自动侦察**：启动时自动检测 CPU / 内存 / GPU / 显存
- **模型智能推荐**：根据你的显存大小自动推荐最适合的模型
- **在线 + 本地双模式**：填一个 DeepSeek API Key 即可对话，也可切换 Ollama 本地模型
- **流式对话**：实时显示 AI 回复，体验丝滑
- **对话历史**：侧边栏显示所有历史对话，可随时切换
- **Markdown + 代码高亮**：代码块自动语法高亮
- **快捷键支持**：`Ctrl+N` 新对话 / `Ctrl+K` 聚焦输入框

### 🤖 智能推荐逻辑
| 你的显存 | 推荐模型 |
|---------|---------|
| 0GB（无独显）| qwen2.5:1.5b（CPU模式）|
| 2-4GB | phi3:3.8b / qwen2.5:1.5b |
| 4-6GB | qwen2.5:7b（⭐推荐）|
| 6-8GB | qwen2.5:7b / llama3:8b |
| 8GB+ | qwen2.5:14b / deepseek-r1:14b |

---

## 🚀 快速安装

### Windows（双击即用）
```powershell
# 下载 exe（GitHub Release）
# 然后直接双击 NBclaw.exe 运行

# 或用安装脚本
iwr https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.ps1 -OutFile install.ps1; .\install.ps1
```

### Linux / macOS
```bash
curl -fsSL https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.sh | bash
```

---

## 📦 功能一览

### 框架管理
```
ollama    — 最流行，本地模型运行核心
llama.cpp — CPU 高效，GGUF 格式支持
vllm      — GPU 高吞吐推理
lm-studio — 桌面 GUI
jan       — 开源 ChatGPT 替代
```

### 模型下载
```
ollama:qwen2.5:1.5b   ollama:pull qwen2.5:1.5b
ollama:qwen2.5:7b     ollama:pull qwen2.5:7b
ollama:llama3:8b      ollama:pull llama3:8b
ollama:deepseek-r1:7b ollama:pull deepseek-r1:7b
...
```

### 万能技能吸收
```
absorb https://github.com/psf/requests     # GitHub 仓库
absorb https://example.com/tool.py         # 单文件
absorb https://example.com/post.html       # 网页代码块
```

### 桌面客户端（GUI）
- 硬件自动侦察 → 模型智能推荐
- 在线模式（DeepSeek API Key）
- 本地模式（Ollama）
- 流式对话 + Markdown 渲染
- 对话历史 + 快捷键
- 系统主题适配（深色/浅色）

---

## 📁 文件结构

```
NBclaw/
├── desktop.py            # 桌面客户端入口
├── hardware.py           # 硬件侦察模块
├── bootstrap.py         # CLI 主程序
├── model_frameworks.py  # 框架管理
├── repo_importer.py     # 技能吸收引擎
├── build.py             # PyInstaller 打包脚本
├── skills/              # 技能存储
│   └── __init__.py
├── security/            # 安全沙箱
│   └── __init__.py
├── install.sh           # Linux 安装
├── install.ps1          # Windows 安装
├── requirements.txt
└── README.md
```

---

## 🔧 从源码运行

```bash
# 1. 克隆
git clone https://github.com/jcwb520/NBclaw.git
cd NBclaw

# 2. 安装依赖
pip install -r requirements.txt
pip install ttkthemes markdown pygments openai python-dotenv requests

# 3. 运行桌面客户端
python desktop.py

# 或运行 CLI 版本
python bootstrap.py
```

---

## 🎯 使用流程

```
① 打开 NBclaw
② （自动）硬件侦察 → 显示推荐模型
③ 填入 DeepSeek API Key（在线模式）
   或 install ollama + pull 模型（本地模式）
④ 直接对话
⑤ 想学新技能 → absorb <URL>
```

---

## 📦 打包构建

```bash
# Windows exe
python build.py windows

# Linux 可执行文件
python build.py linux

# 全部
python build.py all
```

---

**NBclaw = 自举型 AI 基础设施管理器**
- 你把它扔到 GitHub → 别的智能体能一键装到自己的电脑
- 它会自动侦察硬件 → 推荐最适合的模型
- 你只填一个 API Key → 它帮你搞定一切