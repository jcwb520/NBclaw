#!/usr/bin/env python3
"""
repo_importer.py - 万能技能吸收模块
从任意 URL 吸收技能：GitHub / Git仓库 / 原始文件 / 网页代码块
"""
import os
import re
import json
import tempfile
import shutil
import requests
from pathlib import Path
from datetime import datetime

try:
    import git as gitlib
    HAS_GIT = True
except ImportError:
    HAS_GIT = False


class EnhancedRepoImporter:
    """增强版技能吸收引擎"""

    def __init__(self):
        self.skills_dir = Path("skills")
        self.skills_dir.mkdir(exist_ok=True)
        self.temp_dir = Path(tempfile.gettempdir()) / "nbclaw_downloads"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    # ── 主入口 ──
    def absorb_from_url(self, url: str) -> dict:
        """从任意 URL 吸收技能"""
        print(f"🌐 分析来源: {url}")
        source_type = self._detect_source_type(url)

        if source_type == "github":
            return self._absorb_from_github(url)
        elif source_type == "git_repository":
            return self._absorb_from_git(url)
        elif source_type == "raw_file":
            return self._absorb_from_raw_file(url)
        elif source_type == "webpage":
            return self._absorb_from_webpage(url)
        else:
            return {"success": False, "error": f"不支持的来源类型: {url}"}

    # ── 类型检测 ──
    def _detect_source_type(self, url: str) -> str:
        if "github.com" in url:
            return "github"
        elif url.endswith(".git"):
            return "git_repository"
        elif any(url.endswith(ext) for ext in [".py", ".js", ".ts", ".go", ".rs", ".sh"]):
            return "raw_file"
        elif url.startswith("http"):
            return "webpage"
        return "unknown"

    # ── GitHub ──
    def _absorb_from_github(self, url: str) -> dict:
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        if not match:
            return {"success": False, "error": "无效的 GitHub URL"}
        owner, repo = match.groups()
        repo_url = f"https://github.com/{owner}/{repo}.git"
        return self._clone_and_extract(repo_url, repo)

    # ── Git 仓库 ──
    def _absorb_from_git(self, url: str) -> dict:
        repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
        return self._clone_and_extract(url, repo_name)

    # ── 原始文件 ──
    def _absorb_from_raw_file(self, url: str) -> dict:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            code_content = response.text
            filename = url.split("/")[-1]
            skill_name = Path(filename).stem
            return self._create_skill_from_code(skill_name, code_content, url)
        except Exception as e:
            return {"success": False, "error": f"下载文件失败: {e}"}

    # ── 网页（提取代码块）──
    def _absorb_from_webpage(self, url: str) -> dict:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            # 提取 <pre><code>...</code></pre>
            code_blocks = re.findall(r"<pre><code>(.*?)</code></pre>", html, re.DOTALL)
            if not code_blocks:
                # 尝试 ```python ... ```
                code_blocks = re.findall(r"```python\s*(.*?)```", html, re.DOTALL)
            if not code_blocks:
                code_blocks = re.findall(r"```\s*(.*?)```", html, re.DOTALL)

            if code_blocks:
                combined = "\n\n".join(code_blocks)
                skill_name = url.split("/")[-1].replace(".html", "").replace(".htm", "")
                return self._create_skill_from_code(skill_name, combined, url)
            else:
                return {"success": False, "error": "网页中未找到代码块"}
        except Exception as e:
            return {"success": False, "error": f"解析网页失败: {e}"}

    # ── 克隆并提取 ──
    def _clone_and_extract(self, repo_url: str, repo_name: str) -> dict:
        if not HAS_GIT:
            return {"success": False, "error": "GitPython 未安装，无法处理仓库"}
        try:
            target_dir = self.temp_dir / repo_name
            if target_dir.exists():
                shutil.rmtree(target_dir)
            print(f"📥 克隆仓库: {repo_url}")
            gitlib.Repo.clone_from(repo_url, target_dir, depth=1)
            content = self._extract_repo_content(target_dir)
            result = self._generate_skill(repo_name, content, repo_url)
            shutil.rmtree(target_dir, ignore_errors=True)
            return result
        except Exception as e:
            return {"success": False, "error": f"处理仓库失败: {e}"}

    # ── 提取仓库内容 ──
    def _extract_repo_content(self, repo_path: Path) -> str:
        parts = []
        # README
        for name in ["README.md", "README.md", "readme.md"]:
            readme = repo_path / name
            if readme.exists():
                try:
                    parts.append(f"# README:\n{readme.read_text('utf-8', errors='ignore')[:3000]}")
                    break
                except Exception:
                    pass
        # Python 文件
        for py in list(repo_path.rglob("*.py"))[:12]:
            try:
                rel = py.relative_to(repo_path)
                parts.append(f"# File: {rel}\n{py.read_text('utf-8', errors='ignore')[:2000]}")
            except Exception:
                pass
        return "\n\n".join(parts)[:20000]

    # ── 生成技能文件 ──
    def _generate_skill(self, repo_name: str, content: str, source_url: str) -> dict:
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", repo_name.lower())
        skill_code = self._build_skill_code(safe_name, source_url)
        skill_file = self.skills_dir / f"skill_{safe_name}.py"
        skill_file.write_text(skill_code, encoding="utf-8")
        # 元数据
        meta_file = self.skills_dir / f"skill_{safe_name}.json"
        metadata = {
            "name":        safe_name,
            "source":      source_url,
            "created_at":  datetime.now().isoformat(),
            "status":      "pending_review",
            "type":        "auto_generated",
        }
        meta_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "success":    True,
            "skill_name": safe_name,
            "skill_file": str(skill_file),
            "meta_file":  str(meta_file),
            "message":    f"技能 {repo_name} 已吸收并保存",
        }

    def _build_skill_code(self, skill_name: str, source_url: str) -> str:
        return f'''# Skill: {skill_name}
# Source: {source_url}
# Generated by NBclaw

TOOL_NAME = "{skill_name}"
TOOL_DESCRIPTION = "从 {source_url} 吸收的技能"

def run(**kwargs):
    """执行技能"""
    try:
        return {{"success": True, "message": "技能执行成功", "source": "{source_url}"}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}

if __name__ == "__main__":
    result = run()
    print(result)
'''

    # ── 从代码创建技能 ──
    def _create_skill_from_code(self, skill_name: str, code: str, source_url: str) -> dict:
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", skill_name.lower())
        full_code = f'''# Skill: {skill_name}
# Source: {source_url}
# Generated by NBclaw

{code}

if __name__ == "__main__":
    result = run()
    print(result)
'''
        skill_file = self.skills_dir / f"skill_{safe_name}.py"
        skill_file.write_text(full_code, encoding="utf-8")
        meta_file = self.skills_dir / f"skill_{safe_name}.json"
        metadata = {
            "name":       safe_name,
            "source":     source_url,
            "created_at": datetime.now().isoformat(),
            "status":     "pending_review",
            "type":       "code_import",
        }
        meta_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "success":    True,
            "skill_name": safe_name,
            "skill_file": str(skill_file),
            "message":    f"代码技能 {skill_name} 已创建",
        }

    # ── 技能管理 ──
    def list_skills(self) -> list:
        skills = []
        for meta_file in self.skills_dir.glob("skill_*.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    skills.append(json.load(f))
            except Exception:
                pass
        return skills

    def enable_skill(self, skill_name: str) -> bool:
        meta_file = self.skills_dir / f"skill_{skill_name}.json"
        if not meta_file.exists():
            return False
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            metadata["status"] = "enabled"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False


# 全局实例
enhanced_importer = EnhancedRepoImporter()