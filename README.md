# NBclaw 🦶

**本地 AI 基础设施管理器** — 框架一键安装 · 模型一键下载 · 万能技能吸收 · 对话主循环

> 「我把它扔到 GitHub，别的智能体拿到链接就能一键装到自己电脑上。」

---

## 核心功能

### 📦 模型框架管理
一条命令安装主流本地模型框架：

| 框架 | 说明 |
|------|------|
| Ollama | 最流行，本地模型运行核心 |
| llama.cpp | 纯 C/C++，CPU 高效，支持 GGUF |
| vLLM | PagedAttention，GPU 高吞吐 |
| LM Studio | 桌面 GUI，一键拉模型 |
| Jan | 开源 ChatGPT 替代 |

### 🤖 模型下载
支持 Ollama / GGUF 双格式：

```
qwen2.5 (1.5b / 7b / 14b)
llama3 / llama3.1 (8b)
deepseek-r1 (7b / 14b)
mistral / phi3 / gemma2 / codellama
```

### 🌐 万能技能吸收
从任意 URL 吸收技能，不仅仅是 GitHub：

```
absorb https://github.com/psf/requests      ← GitHub 仓库
absorb https://example.com/tool.py         ← 原始文件
absorb https://example.com/blog/post.html  ← 网页代码块
```

### 🔄 自动同步
启动时自动推送到 GitHub，变更不过夜。

### 🔐 安全沙箱
所有技能命令在临时目录执行，危险命令过滤，路径遍历保护。

---

## 快速安装

```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.sh | bash

# Windows PowerShell
iwr https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.ps1 -OutFile install.ps1; .\install.ps1
```

---

## 命令列表

```
list frames        列出可安装的框架
list models        列出可下载的模型
install <框架名>   安装框架（如: install ollama）
pull <模型ID>      下载模型（如: pull ollama:qwen2.5:7b）
absorb <url>       从 URL 吸收技能（GitHub/网站/文件）
list skills        列出所有技能
enable skill <名>  启用技能
status             查看环境状态
exit               退出
直接输入内容       与 AI 对话
```

---

## 推荐安装流程

```
1. install ollama              # 安装 Ollama 框架
2. pull ollama:qwen2.5:7b     # 下载 qwen2.5 7B 模型
3. 直接对话                    # 自动连接 Ollama
```

---

## 文件结构

```
NBclaw/
├── bootstrap.py           主程序（命令路由 + 对话）
├── model_frameworks.py    框架安装 + 模型下载
├── repo_importer.py       万能技能吸收引擎
├── skills/                技能存储目录
│   └── __init__.py        技能加载器
├── security/              安全模块
│   └── __init__.py        沙箱执行器
├── install.sh             Linux 安装脚本
├── install.ps1           Windows 安装脚本
├── requirements.txt       Python 依赖
└── README.md
```

---

## 自举流程

```
用户 clone → 运行 bootstrap.py → 自动拉模型 → 对话
  ↓
absorb <GitHub URL> → 生成技能 → enable skill → 技能可用
  ↓
变更自动 push → 其他机器 clone → 获得相同能力
```

---

## 下一步进化方向

- [ ] 技能依赖自动安装（requirements.txt 分析）
- [ ] 技能测试沙箱（自动单元测试）
- [ ] 技能版本管理（支持回滚）
- [ ] 跨技能协作（多技能组合完成复杂任务）
- [ ] PyInstaller 打包成单文件 exe
- [ ] GitHub Release 自动更新

---

**一句话定位**：NBclaw 是一个「会自己长大的桌面 AI 软件」——你把它扔到 GitHub，别的智能体拿到链接就能一键装到自己电脑上，并具备从任何来源吸收新技能的能力。