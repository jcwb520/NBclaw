#!/usr/bin/env python3
"""
hardware.py - 硬件自动侦察模块
在启动时检测：系统 / CPU / 内存 / GPU / VRAM
用于推荐最适合的模型框架和模型规模
"""
import platform
import subprocess
import re
import json
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class HardwareProfile:
    os: str              # windows / linux / macos
    os_version: str
    cpu_brand: str
    cpu_cores: int       # 物理核心数
    ram_gb: int          # 总内存 GB
    gpu_name: str        # GPU 名称
    vram_gb: int         # 显存 GB（0 = 无独显）
    gpu_driver: str      # 显卡驱动版本
    has_nvidia: bool
    has_amd: bool
    has_apple_silicon: bool
    supports_cuda: bool
    supports_amd_roc: bool

    def recommend_model_size(self) -> list:
        """推荐可运行的模型规模列表，按推荐度排序"""
        models = []

        vram = self.vram_gb
        ram = self.ram_gb

        # VRAM < 2GB：只能 CPU 模式
        if vram < 2:
            models.append({
                "id": "ollama:qwen2.5:1.5b",
                "size": "~1GB",
                "mode": "CPU",
                "recommended": False,
                "note": "你的显存较小，建议用 CPU 模式运行小模型"
            })
            return models

        # VRAM 2-4GB：推荐 1.5B-3B
        if vram < 4:
            models.append({
                "id": "ollama:qwen2.5:1.5b",
                "size": "~1GB",
                "mode": "GPU",
                "recommended": True,
                "note": "⭐ 推荐：qwen2.5 1.5B，显存刚好够，速度快"
            })
            models.append({
                "id": "ollama:phi3:3.8b",
                "size": "~2GB",
                "mode": "GPU",
                "recommended": False,
                "note": "phi3 3.8B 性能更好，但需要更多显存"
            })
            models.append({
                "id": "ollama:gemma2:2b",
                "size": "~1GB",
                "mode": "GPU",
                "recommended": False,
                "note": "gemma2 2B 较新，但质量稍弱"
            })
            return models

        # VRAM 4-6GB：推荐 7B Q4
        if vram < 6:
            models.append({
                "id": "ollama:qwen2.5:7b",
                "size": "~4GB",
                "mode": "GPU",
                "recommended": True,
                "note": "⭐ 推荐：qwen2.5 7B，平衡性能和显存"
            })
            models.append({
                "id": "ollama:llama3:8b",
                "size": "~5GB",
                "mode": "GPU",
                "recommended": False,
                "note": "llama3 8B 质量好，但占更多显存"
            })
            models.append({
                "id": "ollama:deepseek-r1:7b",
                "size": "~4GB",
                "mode": "GPU",
                "recommended": False,
                "note": "deepseek-r1 推理能力强，适合复杂任务"
            })
            return models

        # VRAM 6-8GB：推荐 7B-8B
        if vram < 8:
            models.append({
                "id": "ollama:qwen2.5:7b",
                "size": "~4GB",
                "mode": "GPU",
                "recommended": True,
                "note": "⭐ 推荐：qwen2.5 7B，流畅运行"
            })
            models.append({
                "id": "ollama:llama3:8b",
                "size": "~5GB",
                "mode": "GPU",
                "recommended": True,
                "note": "⭐ 推荐：llama3 8B，质量优秀"
            })
            models.append({
                "id": "ollama:deepseek-r1:7b",
                "size": "~4GB",
                "mode": "GPU",
                "recommended": False,
                "note": "deepseek-r1 推理强"
            })
            models.append({
                "id": "ollama:qwen2.5:14b",
                "size": "~8GB",
                "mode": "GPU",
                "recommended": False,
                "note": "qwen2.5 14B 质量更高，需要更多显存"
            })
            return models

        # VRAM 8-12GB：推荐 7B-14B
        if vram < 12:
            models.append({
                "id": "ollama:qwen2.5:14b",
                "size": "~8GB",
                "mode": "GPU",
                "recommended": True,
                "note": "⭐ 推荐：qwen2.5 14B，质量接近 GPT-4"
            })
            models.append({
                "id": "ollama:deepseek-r1:14b",
                "size": "~9GB",
                "mode": "GPU",
                "recommended": True,
                "note": "⭐ 推荐：deepseek-r1 14B，推理能力超强"
            })
            models.append({
                "id": "ollama:llama3:8b",
                "size": "~5GB",
                "mode": "GPU",
                "recommended": False,
                "note": "llama3 8B 快速响应"
            })
            return models

        # VRAM >= 12GB：高端推荐
        models.append({
            "id": "ollama:qwen2.5:14b",
            "size": "~8GB",
            "mode": "GPU",
            "recommended": True,
            "note": "⭐ 推荐：qwen2.5 14B，流畅运行"
        })
        models.append({
            "id": "ollama:deepseek-r1:14b",
            "size": "~9GB",
            "mode": "GPU",
            "recommended": True,
            "note": "⭐ 推荐：deepseek-r1 14B，顶级推理"
        })
        models.append({
            "id": "ollama:qwen2.5:7b",
            "size": "~4GB",
            "mode": "GPU",
            "recommended": False,
            "note": "qwen2.5 7B 快速，省显存"
        })
        return models

    def recommend_framework(self) -> str:
        """推荐最适合的模型框架"""
        if self.supports_cuda and self.vram_gb >= 6:
            return "vllm"
        if self.has_nvidia:
            return "ollama"  # Ollama 对 NVIDIA 支持也很好
        if self.has_apple_silicon:
            return "ollama"  # Ollama 对 Apple Silicon 有优化
        if self.vram_gb < 2:
            return "llama.cpp"  # CPU 高效
        return "ollama"

    def summary(self) -> str:
        """硬件摘要"""
        return (
            f"系统: {self.os} {self.os_version}\n"
            f"CPU: {self.cpu_brand} ({self.cpu_cores}核心)\n"
            f"内存: {self.ram_gb}GB\n"
            f"GPU: {self.gpu_name} ({self.vram_gb}GB显存)\n"
            f"CUDA: {'✅ 支持' if self.supports_cuda else '❌ 不支持'}\n"
            f"推荐框架: {self.recommend_framework()}"
        )


def detect_hardware() -> HardwareProfile:
    """执行完整硬件侦察"""
    plat = platform.system().lower()
    os_version = ""
    cpu_brand = ""
    cpu_cores = os.cpu_count() or 4
    ram_gb = 8
    gpu_name = "未知"
    vram_gb = 0
    gpu_driver = ""
    has_nvidia = False
    has_amd = False
    has_apple_silicon = False
    supports_cuda = False
    supports_amd_roc = False

    # OS 版本
    try:
        if plat == "windows":
            os_version = platform.release()
        elif plat == "linux":
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME"):
                        os_version = line.split("=")[1].strip().strip('"')
                        break
        else:
            os_version = platform.mac_ver()[0]
    except Exception:
        os_version = "unknown"

    # CPU 品牌
    try:
        if plat == "windows":
            brand = subprocess.run(
                ["powershell", "-Command",
                 "(Get-WmiObject Win32_Processor).Name"],
                capture_output=True, text=True, timeout=5
            )
            cpu_brand = brand.stdout.strip().split("\n")[0].strip()
        elif plat == "linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        cpu_brand = line.split(":")[1].strip()
                        break
        else:
            cpu_brand = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
    except Exception:
        cpu_brand = "Unknown CPU"

    # 内存
    try:
        if plat == "windows":
            mem_out = subprocess.run(
                ["powershell", "-Command",
                 "(Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB"],
                capture_output=True, text=True, timeout=5
            )
            ram_gb = int(float(mem_out.stdout.strip()))
        elif plat == "linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        kb = int(line.split()[1])
                        ram_gb = kb // 1024 // 1024
                        break
        else:
            ram_gb = int(subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()) // 1024**3
    except Exception:
        pass

    # GPU + CUDA
    try:
        if plat == "windows":
            gpu_out = subprocess.run(
                ["powershell", "-Command",
                 "Get-WmiObject Win32_VideoController | Select-Object -First 1 -ExpandProperty Name"],
                capture_output=True, text=True, timeout=5
            )
            gpu_name = gpu_out.stdout.strip().split("\n")[0].strip()

            # NVIDIA 检测
            nvidia_out = subprocess.run(
                ["powershell", "-Command",
                 "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>nul"],
                capture_output=True, text=True, timeout=5
            )
            if nvidia_out.returncode == 0 and nvidia_out.stdout.strip():
                has_nvidia = True
                supports_cuda = True
                lines = nvidia_out.stdout.strip().split("\n")
                if lines:
                    parts = lines[0].split(",")
                    gpu_name = parts[0].strip()
                    if len(parts) >= 3:
                        vram_str = parts[2].strip().replace("MiB", "").replace("MB", "").strip()
                        vram_gb = int(vram_str) // 1024
                    if len(parts) >= 2:
                        gpu_driver = parts[1].strip()

        elif plat == "linux":
            # nvidia-smi
            nvidia_out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if nvidia_out.returncode == 0 and nvidia_out.stdout.strip():
                has_nvidia = True
                supports_cuda = True
                lines = nvidia_out.stdout.strip().split("\n")
                if lines:
                    parts = lines[0].split(",")
                    gpu_name = parts[0].strip()
                    if len(parts) >= 3:
                        vram_str = parts[2].strip().replace("MiB", "").replace("MB", "").strip()
                        vram_gb = int(vram_str) // 1024
                    if len(parts) >= 2:
                        gpu_driver = parts[1].strip()
            else:
                # AMD GPU
                amd_out = subprocess.run(
                    ["rocm-smi", "--showid"],
                    capture_output=True, text=True, timeout=5
                )
                if amd_out.returncode == 0:
                    has_amd = True
                    supports_amd_roc = True
                    vram_gb = 8  # 假设
                    gpu_name = "AMD GPU"
        else:
            # macOS
            apple_silicon = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            if "Apple" in apple_silicon or "M" in apple_silicon:
                has_apple_silicon = True
                supports_cuda = False
                gpu_name = "Apple Silicon"
                # 读取显存
                vram_out = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True, timeout=5
                )
                if vram_out.returncode == 0:
                    total_mem = int(vram_out.stdout.strip())
                    # Apple Silicon 共享显存：总内存的约1/4
                    vram_gb = total_mem // 1024**3 // 4
                    if vram_gb < 1:
                        vram_gb = 8  # 默认估计
    except Exception:
        pass

    # 如果没检测到 GPU，默认给一个保守估计
    if gpu_name == "未知" or gpu_name == "":
        if vram_gb == 0:
            # 无独显，尝试用 CPU 模式
            vram_gb = 0
            gpu_name = "集成显卡 (无独显)"

    profile = HardwareProfile(
        os=plat,
        os_version=os_version,
        cpu_brand=cpu_brand,
        cpu_cores=cpu_cores,
        ram_gb=ram_gb,
        gpu_name=gpu_name,
        vram_gb=vram_gb,
        gpu_driver=gpu_driver,
        has_nvidia=has_nvidia,
        has_amd=has_amd,
        has_apple_silicon=has_apple_silicon,
        supports_cuda=supports_cuda,
        supports_amd_roc=supports_amd_roc,
    )
    return profile


if __name__ == "__main__":
    p = detect_hardware()
    print("=== 硬件侦察结果 ===")
    print(p.summary())
    print("\n=== 推荐模型 ===")
    for m in p.recommend_model_size():
        star = "⭐" if m["recommended"] else "  "
        print(f"{star} {m['id']} | {m['size']} | {m['mode']} | {m['note']}")
    print(f"\n推荐框架: {p.recommend_framework()}")