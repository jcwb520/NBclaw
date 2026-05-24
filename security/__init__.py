# security/sandbox.py - 技能安全沙箱
import subprocess
import tempfile
import os
import re
from pathlib import Path


class SkillSandbox:
    """技能安全沙箱 — 确保技能在安全环境中执行"""

    BLOCKED_COMMANDS = [
        "rm -rf", "format", "mkfs", "del /f /q",
        ":(){:|:&};:", "dd if=", " shred",
    ]

    BLOCKED_PATHS = [
        "/etc", "/usr/bin", "/System", "C:\\Windows",
        "/proc", "/sys", ".ssh",
    ]

    def __init__(self):
        self.allowed_cmds = ["python", "pip", "git", "curl", "wget", "ollama"]

    def validate_command(self, command: str) -> tuple[bool, str]:
        """验证命令是否安全"""
        cmd_lower = command.lower()
        # 检查危险命令
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return False, f"危险命令被阻止: {blocked}"
        # 检查路径遍历
        if ".." in command:
            return False, "路径遍历攻击被阻止"
        return True, "命令安全"

    def execute_safe(self, command: str, timeout: int = 30) -> dict:
        """在安全临时目录中执行命令"""
        is_safe, reason = self.validate_command(command)
        if not is_safe:
            return {"success": False, "error": reason}
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run(
                    command, shell=True,
                    capture_output=True, text=True,
                    timeout=timeout, cwd=tmpdir
                )
                return {
                    "success":   result.returncode == 0,
                    "stdout":    result.stdout,
                    "stderr":    result.stderr,
                    "returncode": result.returncode,
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "命令执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局沙箱实例
skill_sandbox = SkillSandbox()