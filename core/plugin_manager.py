"""
Plugin Manager — 插件发现/加载/卸载/热更新。
"""

import logging
import importlib
import inspect
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("nbclaw.plugin_manager")

PLUGIN_BASE_PATH = Path(__file__).parent.parent / "plugins"


class PluginInterface:
    """插件接口标准 — 所有插件必须继承此类。"""

    name: str = "base"
    version: str = "0.0.0"

    def init(self, ctx: dict):
        """初始化插件，接收上下文。"""
        pass

    def start(self):
        """启动插件（Hub 完全启动后调用）。"""
        pass

    def stop(self):
        """停止插件（Hub 关闭前调用）。"""
        pass

    def handle_message(self, msg: dict) -> dict:
        """处理用户消息（如果插件订阅了 user.message）。"""
        return {"handled": False}

    def get_status(self) -> dict:
        """返回插件状态。"""
        return {"status": "ok", "version": self.version}


class PluginManager:
    """
    插件管理器：
    - discover_plugins：扫描 plugins/ 目录
    - load_all：实例化并初始化所有插件
    - unload_all：停止并卸载所有插件
    """

    def __init__(self):
        self.plugins: dict[str, PluginInterface] = {}

    async def discover_plugins(self):
        """扫描 plugins/ 目录，收集插件。"""
        if not PLUGIN_BASE_PATH.exists():
            logger.warning(f"插件目录不存在: {PLUGIN_BASE_PATH}")
            return

        for item in PLUGIN_BASE_PATH.iterdir():
            if not item.is_dir():
                continue
            # 跳过以 _ 开头的目录
            if item.name.startswith("_"):
                continue

            plugin_file = item / "plugin.py"
            if plugin_file.exists():
                logger.info(f"发现插件: {item.name}")
                await self._load_plugin_from_path(item)

    async def _load_plugin_from_path(self, path: Path):
        """从 path/plugins/name/plugin.py 加载插件。"""
        name = path.name

        try:
            # 动态导入 plugin.py
            import sys
            sys.path.insert(0, str(path))
            module = importlib.import_module("plugin")

            # 找继承 PluginInterface 的类
            plugin_class = None
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, PluginInterface) and cls is not PluginInterface:
                    plugin_class = cls
                    break

            if not plugin_class:
                logger.warning(f"插件 {name} 未找到继承 PluginInterface 的类")
                return

            # 实例化
            instance = plugin_class()
            self.plugins[name] = instance
            logger.info(f"✅ 插件 {name} v{instance.version} 已加载")

        except Exception as e:
            logger.error(f"❌ 加载插件 {name} 失败: {e}")

    async def load_all(self, ctx: dict):
        """初始化并启动所有已加载的插件。"""
        for name, plugin in self.plugins.items():
            try:
                plugin.init(ctx)
                plugin.start()
            except Exception as e:
                logger.error(f"❌ 插件 {name} 初始化失败: {e}")

    async def unload_all(self):
        """停止并卸载所有插件。"""
        for name, plugin in self.plugins.items():
            try:
                plugin.stop()
                logger.info(f"插件 {name} 已卸载")
            except Exception as e:
                logger.error(f"卸载插件 {name} 失败: {e}")
        self.plugins.clear()