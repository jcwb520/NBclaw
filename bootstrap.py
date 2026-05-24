#!/usr/bin/env python3
"""
NBclaw - 本地 AI 基础设施管理器
框架 + 模型 一键下载，对话主循环
"""
import os
import sys
import time
import re
import subprocess
import platform
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ─────────────────────────────────────────────
# 框架安装命令表
# ─────────────────────────────────────────────
FRAMES = {
    "ollama": {
        "linux":    "curl -fsSL https://ollama.com/install.sh | sh",
        "macos":    "curl -fsSL https://ollama.com/install.sh | sh",
        "windows":  "irm https://ollama.com/install.ps1 | iex",
        "desc":     "最流行的本地模型运行框架，支持海量模型",
    },
    "llama.cpp": {
        "linux":    "git clone https://github.com/ggerganov/llama.cpp.git && cd llama.cpp && mkdir -p build && cd build && cmake .. && make -j$(nproc) && make install",
        "macos":    "git clone https://github.com/ggerganov/llama.cpp.git && cd llama.cpp && mkdir -p build && cd build && cmake .. && make -j$(sysctl -n hw.ncpu)",
        "windows":  "git clone https://github.com/ggerganov/llama.cpp.git && cd llama.cpp && mkdir build && cd build && cmake .. -G 'Visual Studio 17 2022' && cmake --build . --config Release",
        "desc":     "纯 C/C++ 实现，CPU 高效推理，支持 GGUF 格式",
    },
    "vllm": {
        "linux":    "pip install vllm",
        "macos":    "pip install vllm  # 仅 Linux GPU 推荐",
        "windows":  "pip install vllm  # 仅 Linux GPU 推荐",
        "desc":     "PagedAttention 高吞吐量推理，GPU 首选",
    },
    "lm-studio": {
        "linux":    "wget -q https://releases.lmstudio.ai/linux/x86/0.2.9/LM-Studio-0.2.9.AppImage -O lm-studio.AppImage && chmod +x lm-studio.AppImage",
        "macos":    "brew install lm-studio  # 或下载 .dmg",
        "windows":  "winget install lm-studio  # 或下载 .exe",
        "desc":     "桌面 GUI，一键拉模型，支持 LocalAI 协议",
    },
    "jan": {
        "linux":    "wget -q https://jan.ai/install.sh -O install.sh && chmod +x install.sh && ./install.sh",
        "macos":    "brew install jan  # 或下载 .dmg",
        "windows":  "winget install jan  # 或下载 .exe",
        "desc":     "开源 ChatGPT 替代，本地模型市场集成",
    },
}

# ─────────────────────────────────────────────
# 模型下载命令表
# ─────────────────────────────────────────────
MODELS = {
    # Ollama 模型
    "ollama:qwen2.5:1.5b":   "ollama pull qwen2.5:1.5b",
    "ollama:qwen2.5:7b":     "ollama pull qwen2.5:7b",
    "ollama:qwen2.5:14b":    "ollama pull qwen2.5:14b",
    "ollama:llama3:8b":      "ollama pull llama3:8b",
    "ollama:llama3.1:8b":    "ollama pull llama3.1:8b",
    "ollama:deepseek-r1:7b":  "ollama pull deepseek-r1:7b",
    "ollama:deepseek-r1:14b": "ollama pull deepseek-r1:14b",
    "ollama:mistral:7b":     "ollama pull mistral:7b",
    "ollama:phi3:3.8b":      "ollama pull phi3:3.8b",
    "ollama:gemma2:2b":      "ollama pull gemma2:2b",
    "ollama:codellama:7b":   "ollama pull codellama:7b",
    # llama.cpp / 直接下载
    "gguf:qwen2.5-1.5b":    "huggingface-cli download qwen-community/qwen2.5-1.5b-instruct-GGUF qwen2.5-1.5b-instruct-q4_K_M.gguf --local-dir ./models",
    "gguf:llama3-8b":       "huggingface-cli download meta-llama/Meta-Llama-3-8B-Instruct-GGUF llama-3-8b-instruct-q4_K_M.gguf --local-dir ./models",
    "gguf:mistral-7b":      "huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF mistral-7b-instruct-v0.2-q4_k_m.gguf --local-dir ./models",
}

PLAT = platform.system().lower()


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────
def run_cmd(cmd: str, desc: str = "", timeout: int = 300) -> bool:
    """执行命令"""
    print(f"\n▶ {desc or cmd}")
    print("-" * 40)
    try:
        result = subprocess.run(cmd, shell=True, timeout=timeout)
        ok = result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏱️  命令执行超时")
        return False
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False
    print("-" * 40)
    print("✅ 成功" if ok else "❌ 失败")
    return ok


# ─────────────────────────────────────────────
# 框架命令
# ─────────────────────────────────────────────
def cmd_list_frames():
    print("\n📦 可安装的框架：")
    print(f"  {'框架':<14} {'说明'}")
    print("  " + "-" * 65)
    for name, info in FRAMES.items():
        plat_cmd = info.get(PLAT) or info.get("linux") or "N/A"
        hint = "(当前系统)" if plat_cmd != "N/A" else ""
        print(f"  {name:<14} {info['desc']} {hint}")


def cmd_list_models():
    print("\n🤖 可下载的模型：")
    print(f"  {'模型ID':<28} {'下载命令'}")
    print("  " + "-" * 65)
    for mid, cmd in MODELS.items():
        print(f"  {mid:<28} {cmd}")


def cmd_install_frame(name: str):
    info = FRAMES.get(name.lower())
    if not info:
        print(f"❌ 未知框架: {name}")
        print("  可用框架:", ", ".join(FRAMES.keys()))
        return
    cmd = info.get(PLAT) or info.get("linux")
    if cmd == "N/A":
        print(f"❌ 框架 {name} 暂不支持 {PLAT}，请参考文档手动安装")
        return
    run_cmd(cmd, f"安装 {name} ({PLAT})")


def cmd_pull_model(model_id: str):
    cmd = MODELS.get(model_id.lower())
    if not cmd:
        if model_id.startswith("ollama:"):
            cmd = f"ollama pull {model_id.split(':', 1)[1]}"
        elif model_id.startswith("gguf:"):
            model_name = model_id.split(":", 1)[1]
            cmd = f"huggingface-cli download {model_name} --local-dir ./models"
        else:
            print(f"❌ 未知模型: {model_id}")
            print("  输入 list models 查看可用模型")
            return
    run_cmd(cmd, f"下载模型 {model_id}", timeout=600)


def cmd_status():
    print("\n📊 环境状态：")

    # Ollama
    try:
        r = subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"],
                           capture_output=True, timeout=5)
        if r.returncode == 0:
            import json
            try:
                data = json.loads(r.stdout)
                models = data.get("models", [])
                print(f"  Ollama:      🟢 运行中 ({len(models)} 个模型)")
                for m in models:
                    print(f"    - {m.get('name','?')}")
            except Exception:
                print("  Ollama:      🟢 运行中")
        else:
            print("  Ollama:      🔴 未运行  (输入: install ollama)")
    except Exception:
        print("  Ollama:      🔴 未运行  (输入: install ollama)")

    # 其他框架检测
    for frame in ["llama.cpp", "vllm", "lm-studio", "jan"]:
        which = subprocess.run(["which", frame], capture_output=True)
        status = "🟢 已安装" if which.returncode == 0 else "⚪ 未安装"
        print(f"  {frame:<12} {status}")

    # skills 目录
    skills_dir = Path("skills")
    if skills_dir.exists():
        skill_files = list(skills_dir.glob("skill_*.py"))
        print(f"  技能:        📚 {len(skill_files)} 个已加载")
    else:
        print("  技能:        📭 暂无技能")


# ─────────────────────────────────────────────
# 技能吸收命令（repo_importer）
# ─────────────────────────────────────────────
def cmd_absorb(url: str):
    """从 URL 吸收技能（GitHub / 网站 / 文件）"""
    try:
        from repo_importer import enhanced_importer
    except ImportError:
        print("❌ repo_importer 模块未找到，请确保 repo_importer.py 在同目录")
        return
    print(f"🧠 吸收技能: {url}")
    result = enhanced_importer.absorb_from_url(url)
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"📁 技能文件: {result['skill_file']}")
    else:
        print(f"❌ 吸收失败: {result.get('error', '未知错误')}")


def cmd_list_skills():
    """列出所有已吸收的技能"""
    skills_dir = Path("skills")
    if not skills_dir.exists():
        print("📭 暂无技能")
        return
    skill_files = list(skills_dir.glob("skill_*.json"))
    if not skill_files:
        print("📭 暂无技能")
        return
    print(f"📚 已发现 {len(skill_files)} 个技能：")
    for meta_file in skill_files:
        import json
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            status_icon = "✅" if metadata.get("status") == "enabled" else "⏳"
            print(f"  {status_icon} {metadata.get('name', meta_file.stem)}")
        except Exception:
            print(f"  ❓ {meta_file.stem}")


def cmd_enable_skill(skill_name: str):
    """启用技能"""
    try:
        from repo_importer import enhanced_importer
        enhanced_importer.enable_skill(skill_name)
        print(f"✅ 技能已启用: {skill_name}")
    except Exception as e:
        print(f"❌ 启用失败: {e}")


# ─────────────────────────────────────────────
# 对话主循环
# ─────────────────────────────────────────────
class ModelManager:
    def __init__(self):
        self.mode = os.getenv("MODEL", "ollama")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    def get_client(self):
        if self.mode == "ollama":
            return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        return OpenAI()

    def check_ollama(self) -> bool:
        try:
            r = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True, timeout=5
            )
            return r.returncode == 0
        except Exception:
            return False


def sync_with_github():
    """自动同步到 GitHub"""
    try:
        import git
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return
        repo = git.Repo(".")
        remote_url = f"https://{token}@github.com/{os.getenv('GITHUB_USER')}/NBclaw.git"
        repo.remote().set_url(remote_url)
        repo.git.add(A=True)
        if repo.is_dirty(untracked_files=True):
            repo.index.commit(f"Auto-sync: {time.strftime('%Y-%m-%d %H:%M')}")
            repo.remote().push()
            print("🔄 [Sync] Pushed to GitHub")
    except Exception:
        pass


def print_banner():
    print("=" * 50)
    print("  NBclaw 本地 AI 基础设施管理器")
    print("=" * 50)
    print("""
命令列表：
  list frames      列出可安装的框架
  list models      列出可下载的模型
  install <框架名>  安装框架（如: install ollama）
  pull <模型ID>    下载模型（如: pull ollama:qwen2.5:7b）
  absorb <url>     从 URL 吸收技能（GitHub/网站/文件）
  list skills      列出所有技能
  enable skill <名>  启用技能
  status           查看环境状态
  exit             退出
  直接输入内容     与 AI 对话
""")


def main():
    print_banner()

    mm = ModelManager()
    if mm.check_ollama():
        print(f"✅ Ollama 已连接，当前模型: {mm.model}")
    else:
        print("⚠️  Ollama 未运行 (输入: install ollama)")

    print("=" * 50)

    client = mm.get_client()
    messages = []

    while True:
        try:
            sync_with_github()
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue

            lower = user_input.lower()

            # ── 内建命令 ──
            if lower == "exit":
                print("👋 再见！")
                break

            if lower == "list frames":
                cmd_list_frames()
                continue

            if lower == "list models":
                cmd_list_models()
                continue

            if lower == "status":
                cmd_status()
                continue

            if lower.startswith("install "):
                name = user_input.split(" ", 1)[1].strip()
                cmd_install_frame(name)
                continue

            if lower.startswith("pull "):
                model_id = user_input.split(" ", 1)[1].strip()
                cmd_pull_model(model_id)
                continue

            if lower.startswith("absorb "):
                url = user_input.split(" ", 1)[1].strip()
                cmd_absorb(url)
                continue

            if lower == "list skills":
                cmd_list_skills()
                continue

            if lower.startswith("enable skill "):
                name = user_input.split(" ", 2)[2].strip()
                cmd_enable_skill(name)
                continue

            # ── 对话 ──
            messages.append({"role": "user", "content": user_input})
            response = client.chat.completions.create(
                model=mm.model,
                messages=messages
            )
            reply = response.choices[0].message.content
            print(f"\nBot: {reply}")
            messages.append({"role": "assistant", "content": reply})

        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()