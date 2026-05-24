# NBclaw 核心架构 v1.0

## 核心理念

**一个稳定的内核 + 无限可插拔的模块。**

模块可以随时替换、升级、移除，核心框架完全不动。
你以后整合什么进去都行：Hermes Agent、OpenClaw、任意 Agent。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              Desktop Shell（PyQt/PyInstaller）          │
│     聊天界面 + 硬件检测 + 模型选择 + 设置面板            │
└────────────────────┬────────────────────────────────────┘
                     │ IPC（localhost HTTP）
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    NBclaw Hub（Core）                    │
│  ┌─────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │ PluginMgr   │  │ EventBus   │  │ ConfigStore    │   │
│  │ 插件管理器   │  │ 事件总线    │  │ 配置存储        │   │
│  └─────────────┘  └────────────┘  └────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┬─────────────┐
         ▼           ▼           ▼             ▼
    ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
    │ Hermes  │ │ OpenClaw │ │ Memory  │ │ Skills   │
    │ Plugin  │ │ Channel  │ │ Plugin  │ │ Plugin   │
    │         │ │ Plugin   │ │         │ │          │
    └─────────┘ └──────────┘ └─────────┘ └──────────┘
```

---

## 核心组件

### 1. PluginManager（插件管理器）

负责：
- 发现插件（`plugins/` 目录扫描）
- 加载/卸载/热更新插件
- 维护插件生命周期（init → start → stop）

### 2. EventBus（事件总线）

负责：
- 插件之间松耦合通信
- 事件类型：`user.message`、`agent.response`、`channel.connected`……
- 任何插件可以订阅/发布事件

### 3. ConfigStore（配置存储）

负责：
- 统一的配置读写（JSON/YAML）
- 每个插件的配置隔离存储
- Hub 核心配置统一管理

### 4. IPC 层

Desktop Shell ↔ Hub 通过 HTTP WebSocket 长连接通信：
- Shell 发命令给 Hub（选模型、发送消息）
- Hub 发事件给 Shell（流式输出、状态更新）

---

## 插件接口标准

每个插件必须实现：

```python
class PluginInterface:
    name: str           # 插件唯一标识
    version: str        # 版本号

    def init(self, ctx: PluginContext): ...
    def start(self): ...
    def stop(self): ...
    def handle_message(self, msg: dict) -> dict: ...
    def get_status(self) -> dict: ...
```

PluginContext 提供：
- `event_bus` — 事件订阅/发布
- `config` — 插件专属配置读写
- `hub` — 访问其他插件能力

---

## 内置插件（开箱即用）

| 插件 | 作用 | 状态 |
|------|------|------|
| `hermes-agent` | AI 能力核心，模型调用 | ✅ |
| `openclaw-channel` | 整合 OpenClaw 通道能力 | 🔲 待集成 |
| `memory` | 记忆系统（对话历史、持久化） | 🔲 |
| `skills` | 技能系统（SKILL.md 管理） | 🔲 |
| `content-tracker` | 内容追踪（路边社自动分发） | 🔲 |
| `video-pipeline` | 视频流水线（ComfyUI） | 🔲 |

---

## 目录结构

```
nbclaw/
├── core/                    # 核心框架（稳定不变）
│   ├── __init__.py
│   ├── hub.py              # Hub 主进程
│   ├── plugin_manager.py   # 插件管理器
│   ├── event_bus.py        # 事件总线
│   ├── config_store.py     # 配置存储
│   └── ipc.py              # IPC 通信层
├── plugins/                # 插件目录（随时增删）
│   ├── hermes_agent/
│   ├── openclaw_channel/
│   ├── memory/
│   ├── skills/
│   └── ...
├── desktop.py              # 桌面客户端（GUI Shell）
├── hardware.py             # 硬件检测
├── build.py                # 打包脚本
└── requirements.txt
```

---

## 设计原则

1. **核心永远稳定** — Hub/PluginManager/EventBus 写完后不动
2. **插件完全独立** — 插件挂了不影响 Hub和其他插件
3. **通信只通过 EventBus** — 插件之间不直接引用，避免耦合
4. **配置隔离** — 插件不读写其他插件的配置
5. **热插拔** — 可以运行时加载/卸载插件（无需重启 Hub）
6. **桌面是唯一入口** — 用户所有交互通过 Shell，Shell 只做展示和转发