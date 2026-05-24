#!/usr/bin/env python3
"""
build.py — NBclaw 打包构建脚本
用法: python3 build.py [windows|linux|all]
"""
import sys
import os
import subprocess
import shutil
from pathlib import Path

PLAT = sys.platform.lower()
DIST = Path("dist")
DIST.mkdir(exist_ok=True)


def install_deps():
    print("📦 安装打包依赖...")
    pkgs = [
        "pyinstaller>=6.0.0",
        "ttkthemes>=0.3.3",
        "markdown>=3.5",
        "pygments>=2.17",
        "openai>=1.30.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
    ]
    subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + pkgs, check=True)
    print("✅ 依赖安装完成")


def build_windows():
    print("🔨 构建 Windows exe...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NBclaw",
        "--onefile",
        "--windowed",
        "--icon=NONE",
        # hidden imports
        "--hidden-import=openai",
        "--hidden-import=git",
        "--hidden-import=markdown",
        "--hidden-import=pygments",
        "--hidden-import=ttkthemes",
        "--hidden-import=pkg_resources",
        # additional files
        "--add-data=hardware.py;.",
        "--add-data=model_frameworks.py;.",
        "--add-data=repo_importer.py;.",
        "--add-data=skills;skills",
        "--add-data=security;security",
        # spec file output
        "--distpath=dist",
        "--workpath=dist/build",
        "--specpath=dist",
        "desktop.py",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    if result.returncode == 0:
        exe = DIST / "NBclaw.exe"
        if exe.exists():
            print(f"✅ 构建完成：{exe.absolute()}")
            print(f"📦 文件大小：{exe.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            # 可能在 build 目录
            for f in DIST.rglob("NBclaw.exe"):
                print(f"✅ 构建完成：{f.absolute()}")
                break
    else:
        print("❌ 构建失败")


def build_linux():
    print("🔨 构建 Linux 可执行文件...")
    # Linux 下用 --console 因为没有真正的 windowed 模式支持跨平台
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NBclaw",
        "--onefile",
        "--icon=NONE",
        "--hidden-import=openai",
        "--hidden-import=git",
        "--hidden-import=markdown",
        "--hidden-import=pygments",
        "--hidden-import=ttkthemes",
        "--add-data=hardware.py:.",
        "--add-data=model_frameworks.py:.",
        "--add-data=repo_importer.py:.",
        "--add-data=skills:skills",
        "--add-data=security:security",
        "--distpath=dist",
        "--workpath=dist/build",
        "--specpath=dist",
        "desktop.py",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    if result.returncode == 0:
        exe = DIST / "NBclaw"
        if exe.exists():
            print(f"✅ 构建完成：{exe.absolute()}")
            print(f"📦 文件大小：{exe.stat().st_size / 1024 / 1024:.1f} MB")
            os.chmod(str(exe), 0o755)
    else:
        print("❌ 构建失败")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    install_deps()

    if target in ("windows", "all"):
        if PLAT.startswith("win") or PLAT.startswith("cygwin"):
            build_windows()
        else:
            print("⚠️ 跳过 Windows 构建（当前系统非 Windows）")

    if target in ("linux", "all"):
        if PLAT.startswith("linux"):
            build_linux()
        else:
            print("⚠️ 跳过 Linux 构建（当前系统非 Linux）")

    if target == "all":
        print("\n📦 构建产物：")
        for f in DIST.rglob("*"):
            if f.is_file():
                size = f.stat().st_size / 1024 / 1024
                print(f"  {'exe' if f.suffix == '.exe' else 'bin':>3}  {f.name:<30} {size:>7.1f} MB")


if __name__ == "__main__":
    main()