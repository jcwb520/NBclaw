#!/usr/bin/env python3
"""
model_frameworks.py - 模型框架管理器
一键安装框架 + 下载模型 + 状态检测
"""
import os
import sys
import subprocess
import platform
import json
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional

# ─────────────────────────────────────────────
# 框架定义
# ─────────────────────────────────────────────
FRAMEWORKS = {
    "ollama": {
        "name": "Ollama",
        "desc": "本地 LLM 运行框架（推荐）",
        "linux":    "curl -fsSL https://ollama.com/install.sh | sh",
        "macos":    "curl -fsSL https://ollama.com/install.sh | sh",
        "windows":  "irm https://ollama.com/install.ps1 | iex",
        "check":    "ollama --version",
        "post":     "setup_ollama_models",
    },
    "llama.cpp": {
        "name": "llama.cpp",
        "desc": "纯 C/C++，CPU 高效推理，支持 GGUF",
        "linux":    "git clone https://github.com/ggerganov/llama.cpp.git && cd llama.cpp && mkdir -p build && cd build && cmake .. && make -j$(nproc) && make install",
        "macos":    "git clone https://github.com/ggerganov/llama.cpp.git && cd llama.cpp && mkdir -p build && cd build && cmake .. && make -j$(sysctl -n hw.ncpu)",
        "windows":  "git clone https://github.com/ggerganov/llama.cpp.git && cd llama.cpp && mkdir build && cd build && cmake .. -G 'Visual Studio 17 2022' && cmake --build . --config Release",
        "check":    "python -c \"import llama_cpp\"",
    },
    "vllm": {
        "name": "vLLM",
        "desc": "PagedAttention 高吞吐量推理，GPU 首选",
        "linux":    "pip install vllm",
        "macos":    "pip install vllm  # 仅 Linux GPU 推荐",
        "windows":  "pip install vllm  # 仅 Linux GPU 推荐",
        "check":    "python -c \"import vllm; print(vllm.__version__)\"",
        "gpu":      True,
    },
    "lm-studio": {
        "name": "LM Studio",
        "desc": "桌面 GUI，一键拉模型，支持 LocalAI 协议",
        "linux":    "wget -q https://releases.lmstudio.ai/linux/x86/0.2.9/LM-Studio-0.2.9.AppImage -O lm-studio.AppImage && chmod +x lm-studio.AppImage",
        "macos":    "brew install lm-studio",
        "windows":  "winget install lm-studio",
        "check":    "lm-studio --version",
    },
    "jan": {
        "name": "Jan",
        "desc": "开源 ChatGPT 替代，本地模型市场集成",
        "linux":    "wget -q https://jan.ai/install.sh -O install.sh && chmod +x install.sh && ./install.sh",
        "macos":    "brew install jan",
        "windows":  "winget install jan",
        "check":    "jan --version",
    },
}

# ─────────────────────────────────────────────
# 模型定义
# ─────────────────────────────────────────────
MODELS = {
    # Ollama 模型
    "ollama:qwen2.5:1.5b":   {"cmd": "ollama pull qwen2.5:1.5b",    "size": "~1GB"},
    "ollama:qwen2.5:7b":     {"cmd": "ollama pull qwen2.5:7b",       "size": "~4GB"},
    "ollama:qwen2.5:14b":    {"cmd": "ollama pull qwen2.5:14b",      "size": "~8GB"},
    "ollama:llama3:8b":      {"cmd": "ollama pull llama3:8b",         "size": "~5GB"},
    "ollama:llama3.1:8b":    {"cmd": "ollama pull llama3.1:8b",       "size": "~5GB"},
    "ollama:deepseek-r1:7b": {"cmd": "ollama pull deepseek-r1:7b",    "size": "~4GB"},
    "ollama:deepseek-r1:14b":{"cmd": "ollama pull deepseek-r1:14b",   "size": "~9GB"},
    "ollama:mistral:7b":     {"cmd": "ollama pull mistral:7b",       "size": "~4GB"},
    "ollama:phi3:3.8b":      {"cmd": "ollama pull phi3:3.8b",         "size": "~2GB"},
    "ollama:gemma2:2b":      {"cmd": "ollama pull gemma2:2b",         "size": "~1GB"},
    "ollama:codellama:7b":   {"cmd": "ollama pull codellama:7b",     "size": "~4GB"},
    # GGUF 格式
    "gguf:qwen2.5-1.5b":     {"cmd": "huggingface-cli download qwen-community/qwen2.5-1.5b-instruct-GGUF qwen2.5-1.5b-instruct-q4_K_M.gguf --local-dir ./models", "size": "~1GB"},
    "gguf:llama3-8b":        {"cmd": "huggingface-cli download meta-llama/Meta-Llama-3-8B-Instruct-GGUF llama-3-8b-instruct-q4_k_m.gguf --local-dir ./models", "size": "~5GB"},
    "gguf:mistral-7b":       {"cmd": "huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF mistral-7b-instruct-v0.2-q4_k_m.gguf --local-dir ./models", "size": "~4GB"},
}


class ModelFrameworkManager:
    def __init__(self):
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        self.install_dir = Path.home() / "NBclaw" / "frameworks"
        self.install_dir.mkdir(parents=True, exist_ok=True)

    # ── 检测 ──
    def is_installed(self, framework_id: str) -> bool:
        """检查框架是否已安装"""
        fw = FRAMEWORKS.get(framework_id)
        if not fw:
            return False
        if "check" in fw:
            try:
                subprocess.run(fw["check"], shell=True, capture_output=True, timeout=5)
                return True
            except Exception:
                pass
        return False

    def check_ollama_running(self) -> tuple[bool, int]:
        """检查 Ollama 是否运行，返回 (是否运行, 模型数量)"""
        try:
            r = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True, timeout=5
            )
            if r.returncode == 0:
                data = json.loads(r.stdout)
                return True, len(data.get("models", []))
        except Exception:
            pass
        return False, 0

    # ── 列表 ──
    def list_frameworks(self) -> List[Dict]:
        """列出所有框架及安装状态"""
        result = []
        for fid, info in FRAMEWORKS.items():
            installed = self.is_installed(fid)
            result.append({
                "id":        fid,
                "name":      info["name"],
                "desc":      info["desc"],
                "installed": installed,
            })
        return result

    def list_models(self) -> List[Dict]:
        """列出所有模型"""
        result = []
        for mid, info in MODELS.items():
            result.append({
                "id":   mid,
                "cmd":  info["cmd"],
                "size": info.get("size", ""),
            })
        return result

    # ── 安装框架 ──
    def install(self, framework_id: str) -> Dict:
        """安装指定框架"""
        fw = FRAMEWORKS.get(framework_id)
        if not fw:
            return {"success": False, "error": f"未知框架: {framework_id}"}

        cmd = fw.get(self.system) or fw.get("linux")
        if not cmd or cmd == "N/A":
            return {"success": False, "error": f"框架 {framework_id} 暂不支持 {self.system}"}

        print(f"📦 开始安装 {fw['name']}...")
        try:
            result = subprocess.run(cmd, shell=True, timeout=600)
            if result.returncode != 0:
                return {"success": False, "error": f"安装失败: {result.stderr}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装超时（超过10分钟）"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        # 后置处理
        if fw.get("post") == "setup_ollama_models":
            self._setup_ollama_models()

        print(f"✅ {fw['name']} 安装完成！")
        return {"success": True, "message": f"{fw['name']} 安装成功"}

    def _setup_ollama_models(self):
        """Ollama 安装后拉取默认模型"""
        default_model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        print(f"🤖 正在拉取默认模型 {default_model}（这可能需要几分钟）...")
        try:
            subprocess.run(["ollama", "pull", default_model], timeout=600)
            print(f"✅ {default_model} 已就绪！")
        except Exception as e:
            print(f"⚠️ 模型拉取失败，请稍后手动运行: ollama pull {default_model}")

    # ── 下载模型 ──
    def pull_model(self, model_id: str) -> Dict:
        """下载指定模型"""
        info = MODELS.get(model_id.lower())
        if not info:
            return {"success": False, "error": f"未知模型: {model_id}"}

        print(f"⬇️ 开始下载 {model_id}（{info.get('size','')}）...")
        try:
            result = subprocess.run(info["cmd"], shell=True, timeout=600)
            if result.returncode == 0:
                return {"success": True, "message": f"模型 {model_id} 下载完成"}
            else:
                return {"success": False, "error": f"下载失败: {result.stderr}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "下载超时（超过10分钟）"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── 状态 ──
    def status(self) -> Dict:
        """返回完整环境状态"""
        running, count = self.check_ollama_running()
        return {
            "ollama": {
                "running": running,
                "model_count": count,
            },
            "frameworks": {fid: self.is_installed(fid) for fid in FRAMEWORKS},
        }


# 全局实例
framework_manager = ModelFrameworkManager()