# skills/__init__.py - 技能加载器
import os
import sys
import importlib.util
import json
from pathlib import Path

SKILLS_DIR = Path(__file__).parent


def load_all_skills():
    """加载所有已启用的技能"""
    skills = {}
    for skill_file in SKILLS_DIR.glob("skill_*.py"):
        skill_name = skill_file.stem.replace("skill_", "")
        meta_file = SKILLS_DIR / f"skill_{skill_name}.json"
        # 检查是否已启用
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                if metadata.get("status") != "enabled":
                    continue
            except Exception:
                continue
        # 动态导入
        try:
            spec = importlib.util.spec_from_file_location(
                f"skills.skill_{skill_name}", skill_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                if hasattr(module, "TOOL_NAME") and hasattr(module, "run"):
                    skills[module.TOOL_NAME] = module.run
                    print(f"✅ 已加载技能: {module.TOOL_NAME}")
        except Exception as e:
            print(f"❌ 加载技能失败 {skill_name}: {e}")
    return skills


def list_skill_files():
    """列出所有技能文件"""
    skill_files = list(SKILLS_DIR.glob("skill_*.py"))
    return [f.stem.replace("skill_", "") for f in skill_files]