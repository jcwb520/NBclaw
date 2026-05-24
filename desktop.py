#!/usr/bin/env python3
"""
NBclaw Desktop Client v1.0
硬件自动侦察 · 在线/本地双模式 · 流式对话 · 对话历史 · 快捷键
"""
import os
import sys
import json
import time
import threading
import tempfile
import subprocess
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── UI 依赖 ──
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import ttkthemes

# ── 内容渲染 ──
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ── 导入内部模块 ──
from hardware import detect_hardware, HardwareProfile
from model_frameworks import framework_manager

PLAT = platform.system().lower()
VERSION = "v1.0.0"
CONFIG_DIR = Path.home() / ".nbclaw"
CONFIG_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_DIR = CONFIG_DIR / "history"
HISTORY_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════
# 配置管理
# ═══════════════════════════════════════════════
def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {
        "api_key": "",
        "api_base": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "ollama_model": "qwen2.5:1.5b",
        "mode": "online",  # "online" | "local"
        "temperature": 0.7,
        "theme": "clam",
    }

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))

def load_history() -> list:
    """加载所有对话历史"""
    histories = []
    for f in sorted(HISTORY_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text())
            histories.append(data)
        except Exception:
            pass
    return histories

def save_history(conversation_id: str, messages: list):
    """保存一次对话"""
    f = HISTORY_DIR / f"{conversation_id}.json"
    f.write_text(json.dumps({
        "id": conversation_id,
        "updated_at": datetime.now().isoformat(),
        "messages": messages,
    }, ensure_ascii=False))

def new_conversation_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ═══════════════════════════════════════════════
# Markdown 渲染（带代码高亮）
# ═══════════════════════════════════════════════
class MarkdownRenderer:
    def __init__(self):
        self._css = HtmlFormatter(style="monokai").get_style_defs(".highlight")
        self._style = """
        <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        pre { background: #1e1e1e; padding: 12px; border-radius: 8px; overflow-x: auto; }
        code { font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 13px; }
        blockquote { border-left: 3px solid #444; margin: 0; padding-left: 12px; color: #888; }
        </style>
        """
        self._md = markdown.Markdown(extensions=['fenced_code', 'tables', 'break_on_newline'])

    def render(self, text: str) -> str:
        self._md.reset()
        body = self._md.convert(text)
        return f"<html><head><meta charset='utf-8'>{self._style}</head><body>{body}</body></html>"


# ═══════════════════════════════════════════════
# 硬件侦察面板
# ═══════════════════════════════════════════════
class HardwarePanel:
    def __init__(self, parent, profile: HardwareProfile):
        self.profile = profile
        self.frame = ttk.Frame(parent, padding=10)
        self._build()

    def _build(self):
        p = self.profile
        # 标题
        ttk.Label(self.frame, text="🖥️ 硬件侦察结果", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Separator(self.frame).grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        labels = [
            ("系统", f"{p.os} {p.os_version}"),
            ("CPU", f"{p.cpu_brand} ({p.cpu_cores}核心)"),
            ("内存", f"{p.ram_gb} GB"),
            ("GPU", f"{p.gpu_name}"),
            ("显存", f"{p.vram_gb} GB" if p.vram_gb > 0 else "无独显（CPU模式）"),
            ("CUDA", "✅ 支持" if p.supports_cuda else "❌ 不支持"),
        ]
        for i, (key, val) in enumerate(labels):
            ttk.Label(self.frame, text=f"{key}：", font=("Segoe UI", 9, "bold")).grid(row=i+2, column=0, sticky="ne", padx=5)
            ttk.Label(self.frame, text=val, foreground="#333").grid(row=i+2, column=1, sticky="w")

        # 推荐模型
        row = len(labels) + 2
        ttk.Separator(self.frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 5))
        ttk.Label(self.frame, text="⭐ 推荐模型", font=("Segoe UI", 10, "bold")).grid(row=row+1, column=0, columnspan=2, sticky="w", pady=(5, 3))
        self.model_buttons = []
        for m in self.profile.recommend_model_size()[:4]:
            star = "⭐" if m["recommended"] else "  "
            btn = ttk.Button(self.frame, text=f"{star} {m['id'].split(':')[1]} ({m['size']})")
            btn.configure(command=lambda mid=m['id']: self._on_select_model(mid))
            btn.grid(row=row+2, column=0, columnspan=2, sticky="ew", pady=2)
            self.model_buttons.append((btn, m['id']))

        # 推荐框架
        row = row + 3
        ttk.Separator(self.frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 5))
        fw = self.profile.recommend_framework()
        ttk.Label(self.frame, text=f"💡 推荐框架：{fw}", font=("Segoe UI", 9)).grid(row=row+1, column=0, columnspan=2, sticky="w")

    def _on_select_model(self, model_id: str):
        cfg = load_config()
        cfg["ollama_model"] = model_id
        save_config(cfg)
        messagebox.showinfo("已选择", f"已设置默认模型：{model_id}\n\n在「本地模型」标签页中使用。")

    def show(self):
        self.frame.pack(side="left", fill="y", padx=0, pady=0)


# ═══════════════════════════════════════════════
# 设置面板（API 配置）
# ═══════════════════════════════════════════════
class SettingsPanel:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent, padding=15)
        self.cfg = load_config()
        self._build()

    def _build(self):
        ttk.Label(self.frame, text="⚙️ 在线模型配置", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Separator(self.frame).pack(fill="x", pady=(0, 10))

        # API Key
        ttk.Label(self.frame, text="API Key（DeepSeek / OpenAI 兼容）", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.key_var = tk.StringVar(value=self.cfg.get("api_key", ""))
        ttk.Entry(self.frame, textvariable=self.key_var, show="•", width=55).pack(fill="x", pady=(3, 8))

        # API Base
        ttk.Label(self.frame, text="API Base URL", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.base_var = tk.StringVar(value=self.cfg.get("api_base", "https://api.deepseek.com"))
        ttk.Entry(self.frame, textvariable=self.base_var, width=55).pack(fill="x", pady=(3, 8))

        # 模型
        ttk.Label(self.frame, text="模型名称", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.model_var = tk.StringVar(value=self.cfg.get("model", "deepseek-chat"))
        ttk.Entry(self.frame, textvariable=self.model_var, width=55).pack(fill="x", pady=(3, 8))

        ttk.Button(self.frame, text="💾 保存配置", command=self._save).pack(anchor="w", pady=(5, 0))

        ttk.Separator(self.frame).pack(fill="x", pady=20)

        # 本地模型
        ttk.Label(self.frame, text="🤖 本地模型（Ollama）", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(self.frame, text="Ollama 模型名", font=("Segoe UI", 9)).pack(anchor="w")
        self.ollama_model_var = tk.StringVar(value=self.cfg.get("ollama_model", "qwen2.5:1.5b"))
        ttk.Entry(self.frame, textvariable=self.ollama_model_var, width=55).pack(fill="x", pady=(3, 8))
        ttk.Button(self.frame, text="💾 保存", command=self._save).pack(anchor="w", pady=(5, 0))

        ttk.Separator(self.frame).pack(fill="x", pady=20)

        # 参数
        ttk.Label(self.frame, text="🎛️ 模型参数", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(20, 0))
        ttk.Label(self.frame, text="Temperature", font=("Segoe UI", 9)).pack(anchor="w")
        self.temp_var = tk.DoubleVar(value=self.cfg.get("temperature", 0.7))
        self.temp_label = ttk.Label(self.frame, text="0.7", font=("Segoe UI", 9), foreground="#0066cc")
        self.temp_label.pack(anchor="w")
        ttk.Scale(self.frame, from_=0.0, to=2.0, variable=self.temp_var,
                  orient="horizontal", length=300,
                  command=lambda v: self.temp_label.config(text=f"{float(v):.1f}")).pack(anchor="w", pady=(3, 3))
        ttk.Button(self.frame, text="💾 保存参数", command=self._save).pack(anchor="w", pady=(5, 0))

    def _save(self):
        self.cfg["api_key"] = self.key_var.get().strip()
        self.cfg["api_base"] = self.base_var.get().strip()
        self.cfg["model"] = self.model_var.get().strip()
        self.cfg["ollama_model"] = self.ollama_model_var.get().strip()
        self.cfg["temperature"] = self.temp_var.get()
        save_config(self.cfg)
        messagebox.showinfo("保存成功", "配置已保存，重启后生效")

    def show(self):
        self.frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)


# ═══════════════════════════════════════════════
# 主聊天界面
# ═══════════════════════════════════════════════
class ChatPanel:
    def __init__(self, parent):
        self.parent = parent
        self.messages = []
        self.conversation_id = new_conversation_id()
        self.renderer = MarkdownRenderer()
        self.frame = ttk.Frame(parent, padding=0)
        self._build()

    def _build(self):
        # 顶部栏
        top = ttk.Frame(self.frame, padding=(10, 5))
        top.pack(fill="x")
        self.model_label = ttk.Label(top, text="在线模式", font=("Segoe UI", 9, "bold"), foreground="#0066cc")
        self.model_label.pack(side="left")
        ttk.Button(top, text="🗑️ 清空对话", command=self._clear).pack(side="right")

        # 对话区域
        self.chat_area = scrolledtext.ScrolledText(
            self.frame, wrap="word", font=("Segoe UI", 11),
            bg="#fefefe", fg="#1a1a1a",
            insertbackground="#1a1a1a",
            relief="flat", padx=10, pady=10,
            state="disabled"
        )
        self.chat_area.pack(fill="both", expand=True, padx=5, pady=5)

        # 输入区
        input_frame = ttk.Frame(self.frame, padding=(5, 5))
        input_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.input_box = tk.Text(input_frame, font=("Segoe UI", 11), height=4, wrap="word",
                                relief="solid", borderwidth=1)
        self.input_box.pack(side="left", fill="x", expand=True)
        self.input_box.bind("<Shift-Return>", lambda e: None)
        self.input_box.bind("<Return>", self._on_enter)

        # 发送按钮
        self.send_btn = ttk.Button(input_frame, text="▶", width=4, command=self._send)
        self.send_btn.pack(side="right", padx=(5, 0))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.frame, textvariable=self.status_var, font=("Segoe UI", 8),
                  foreground="#888").pack(side="bottom", anchor="w", padx=10, pady=(0, 3))

    def _append(self, role: str, content: str):
        """追加消息到聊天区域"""
        timestamp = datetime.now().strftime("%H:%M")
        tag = "user" if role == "user" else "bot"
        color = "#1a56db" if role == "user" else "#1a1a1a"
        bg = "#e8f0fe" if role == "user" else "#fefefe"

        self.chat_area.configure(state="normal")

        prefix = "🙂 你" if role == "user" else "🤖 AI"
        self.chat_area.insert("end", f"\n{prefix} · {timestamp}\n", tag)
        self.chat_area.insert("end", content + "\n")
        if role == "bot":
            self.chat_area.insert("end", "\n" + "─" * 40 + "\n")

        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")

    def _on_enter(self, event):
        self._send()
        return "break"

    def _send(self):
        text = self.input_box.get("1.0", "end").strip()
        if not text:
            return
        self.input_box.delete("1.0", "end")
        self._append("user", text)
        self.messages.append({"role": "user", "content": text})
        self._stream_reply()

    def _stream_reply(self):
        """流式回复"""
        self.status_var.set("⏳ 思考中...")
        cfg = load_config()

        try:
            if cfg.get("mode") == "local":
                client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
                model = cfg.get("ollama_model", "qwen2.5:1.5b")
            else:
                if not cfg.get("api_key"):
                    self._append("bot", "⚠️ 请先在「设置」中填写 API Key")
                    self.status_var.set("未配置 API Key")
                    return
                client = OpenAI(api_key=cfg["api_key"], base_url=cfg.get("api_base") + "/v1")
                model = cfg.get("model", "deepseek-chat")

            # 流式
            self.chat_area.configure(state="normal")
            bot_tag = "bot_stream"
            self.chat_area.insert("end", f"\n🤖 AI · {datetime.now().strftime('%H:%M')}\n", bot_tag)
            cursor = "end"

            full_reply = []
            def on_chunk(chunk):
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_reply.append(content)
                    self.chat_area.insert(cursor, content)
                    self.chat_area.see("end")

            self._append_stream = True
            response = client.chat.completions.create(
                model=model,
                messages=self.messages,
                temperature=cfg.get("temperature", 0.7),
                stream=True,
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    self.chat_area.insert("end", chunk.choices[0].delta.content)
                    self.chat_area.see("end")

            self.chat_area.insert("end", "\n" + "─" * 40 + "\n")
            self.chat_area.configure(state="disabled")

            reply_text = "".join(full_reply)
            self.messages.append({"role": "assistant", "content": reply_text})
            self.status_var.set("✅ 就绪")

            # 保存历史
            save_history(self.conversation_id, self.messages)

        except Exception as e:
            self.chat_area.configure(state="disabled")
            self._append("bot", f"❌ 错误：{str(e)}")
            self.status_var.set(f"❌ {e}")

    def _clear(self):
        if messagebox.askyesno("清空确认", "确定清空当前对话？"):
            self.messages.clear()
            self.chat_area.configure(state="normal")
            self.chat_area.delete("1.0", "end")
            self.chat_area.configure(state="disabled")
            self.conversation_id = new_conversation_id()

    def show(self):
        self.frame.pack(side="right", fill="both", expand=True)


# ═══════════════════════════════════════════════
# 侧边栏（历史 + 模式切换）
# ═══════════════════════════════════════════════
class SidePanel:
    def __init__(self, parent, on_switch_chat):
        self.parent = parent
        self.on_switch_chat = on_switch_chat
        self.frame = ttk.Frame(parent, width=220)
        self._build()

    def _build(self):
        # 标题
        ttk.Label(self.frame, text=f"NBclaw {VERSION}", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 3))
        ttk.Label(self.frame, text="本地 AI 基础设施管理器", font=("Segoe UI", 8), foreground="#888").pack(anchor="w", padx=10, pady=(0, 8))

        # 模式切换
        self.mode_var = tk.StringVar(value=load_config().get("mode", "online"))
        mode_frame = ttk.Frame(self.frame)
        mode_frame.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Radiobutton(mode_frame, text="🌐 在线", variable=self.mode_var, value="online",
                       command=self._switch_mode).pack(side="left")
        ttk.Radiobutton(mode_frame, text="🖥️ 本地", variable=self.mode_var, value="local",
                       command=self._switch_mode).pack(side="left")

        ttk.Separator(self.frame).pack(fill="x", padx=8, pady=(0, 8))

        # 历史
        ttk.Label(self.frame, text="📜 对话历史", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10)
        self.history_list = tk.Listbox(self.frame, font=("Segoe UI", 9), height=15,
                                      activestyle="none", relief="flat", bg="#f5f5f5")
        self.history_list.pack(fill="both", expand=True, padx=8, pady=(3, 5))
        self.history_list.bind("<Double-Button-1>", self._on_history_select)
        self._load_history()

        # 底部按钮
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x", padx=8, pady=(0, 10))
        ttk.Button(btn_frame, text="🆕 新对话", command=self._new_chat).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="⚙️ 设置", command=self._open_settings).pack(fill="x", pady=2)

    def _load_history(self):
        self.history_list.delete(0, "end")
        for h in load_history()[:30]:
            ts = h.get("updated_at", "")[:16].replace("T", " ")
            first_msg = ""
            for m in h.get("messages", []):
                if m["role"] == "user":
                    first_msg = m["content"][:30]
                    break
            label = f"{ts} · {first_msg}"
            self.history_list.insert("end", label)

    def _on_history_select(self, event):
        idx = self.history_list.curselection()
        if idx:
            histories = load_history()
            if idx[0] < len(histories):
                self.on_switch_chat(histories[idx[0]]["messages"])

    def _switch_mode(self):
        cfg = load_config()
        cfg["mode"] = self.mode_var.get()
        save_config(cfg)

    def _new_chat(self):
        self.on_switch_chat([])

    def _open_settings(self):
        # 在新窗口打开设置
        win = tk.Toplevel(self.parent)
        win.title("⚙️ NBclaw 设置")
        win.geometry("450x500")
        win.resizable(False, False)
        SettingsPanel(win).show()

    def show(self):
        self.frame.pack(side="left", fill="y", padx=0, pady=0)


# ═══════════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════════
class NBclawApp:
    def __init__(self):
        self.root = ttkthemes.ThemedTk(theme="clam")
        self.root.title(f"NBclaw {VERSION} — 本地 AI 基础设施管理器")
        self.root.geometry("1100x700")
        self.root.minsize(900, 550)

        # 检测硬件
        self.hw_profile = detect_hardware()

        # 主布局
        self.main_frame = ttk.Frame(self.root, padding=0)
        self.main_frame.pack(fill="both", expand=True)

        # 左侧栏
        self.side = SidePanel(self.main_frame, self._on_switch_chat)
        self.side.show()

        # 硬件面板（可选折叠）
        self.hw_panel = HardwarePanel(self.main_frame, self.hw_profile)
        self.hw_panel.show()

        # 聊天面板
        self.chat = ChatPanel(self.main_frame)
        self.chat.show()

        # 快捷键
        self.root.bind("<Command-n>", lambda e: self._new_chat())
        self.root.bind("<Command-k>", lambda e: self._focus_input())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 启动时更新模型标签
        cfg = load_config()
        mode = cfg.get("mode", "online")
        self._update_mode_label(mode)

    def _update_mode_label(self, mode: str):
        if mode == "local":
            self.chat.model_label.config(text="🖥️ 本地模式 · " + load_config().get("ollama_model", "qwen2.5:1.5b"))
        else:
            self.chat.model_label.config(text="🌐 在线模式 · " + load_config().get("model", "deepseek-chat"))

    def _on_switch_chat(self, messages: list):
        self.chat.messages = messages or []
        self.chat.input_box.delete("1.0", "end")
        self.chat.chat_area.configure(state="normal")
        self.chat.chat_area.delete("1.0", "end")
        self.chat.chat_area.configure(state="disabled")
        if messages:
            for m in messages:
                self.chat._append(m["role"], m["content"])

    def _new_chat(self):
        self._on_switch_chat([])

    def _focus_input(self):
        self.chat.input_box.focus()

    def _on_close(self):
        if self.chat.messages:
            save_history(self.chat.conversation_id, self.chat.messages)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    print("🚀 启动 NBclaw Desktop...")
    cfg = load_config()
    if cfg.get("api_key"):
        print(f"✅ 在线模式：{cfg.get('model', 'deepseek-chat')}")
    else:
        print("⚠️ 未配置 API Key，请在界面「设置」中填写")
    app = NBclawApp()
    app.run()