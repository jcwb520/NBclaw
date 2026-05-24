# NBclaw

The Self-Evolving AI Agent.

## 核心特性

- **自举能力**：别人跑一个安装命令，后续所有初始化由智能体自主完成
- **自动建库**：首次运行自动创建 GitHub 仓库
- **技能吸收**：absorb 命令吸收其他仓库的技能
- **双系统支持**：Windows/Linux 安装脚本

## 快速开始

### Linux/macOS

```bash
curl -fsSL https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.sh | bash
```

### Windows

```powershell
iwr https://raw.githubusercontent.com/jcwb520/NBclaw/main/install.ps1 -OutFile install.ps1; .\install.ps1
```

## 架构

- `bootstrap.py` - 首次运行检测 + 启动配置向导
- `github_setup.py` - GitHub 仓库创建 + 代码初始化
- `skills/` - 可扩展技能目录
- `agents/` - Agent 核心逻辑