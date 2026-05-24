"""
NBclaw Hub - Core event-driven agent orchestration hub.
"""

import asyncio
import json
import logging
from typing import Any, Optional
from .plugin_manager import PluginManager
from .event_bus import EventBus
from .config_store import ConfigStore
from .ipc import IPCServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nbclaw.hub")


class NBclawHub:
    """
    NBclaw Hub — 插件容器 + 事件总线 + IPC 入口。
    稳定核心，所有插件通过 EventBus 通信。
    """

    def __init__(self):
        self.plugin_manager = PluginManager()
        self.event_bus = EventBus()
        self.config_store = ConfigStore()
        self.ipc = IPCServer(self)
        self._running = False

    async def start(self):
        """启动 Hub — 加载所有插件，启动 IPC。"""
        logger.info("🤖 NBclaw Hub 启动中...")

        # 加载所有插件
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_all(self._make_plugin_context())

        # 启动 IPC 服务器
        await self.ipc.start()

        self._running = True
        logger.info(f"✅ NBclaw Hub 已启动，已加载 {len(self.plugin_manager.plugins)} 个插件")

        # 保持运行
        while self._running:
            await asyncio.sleep(1)

    async def stop(self):
        """停止 Hub — 卸载所有插件。"""
        logger.info("🛑 NBclaw Hub 关闭中...")
        self._running = False
        await self.plugin_manager.unload_all()
        await self.ipc.stop()
        logger.info("✅ NBclaw Hub 已关闭")

    def _make_plugin_context(self):
        """给插件提供标准上下文。"""
        return {
            "event_bus": self.event_bus,
            "config_store": self.config_store,
            "hub": self,
        }

    # ── IPC 调用的公开接口 ────────────────────────────────

    async def send_message(self, text: str) -> dict:
        """用户发送消息 → Hermes Agent 处理。"""
        # 发事件让订阅者处理
        response = {"status": "ok", "text": f"[Hub] 收到: {text}"}

        # Hermes 插件会订阅 user.message 并处理
        await self.event_bus.publish("user.message", {"text": text})

        return response

    async def get_status(self) -> dict:
        """返回系统状态。"""
        return {
            "hub": "running" if self._running else "stopped",
            "plugins": {
                name: plugin.get_status()
                for name, plugin in self.plugin_manager.plugins.items()
            },
        }

    async def call_plugin_method(self, plugin_name: str, method: str, **kwargs) -> Any:
        """通过 IPC 调用指定插件的方法。"""
        plugin = self.plugin_manager.plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"插件不存在: {plugin_name}")

        if not hasattr(plugin, method):
            raise ValueError(f"插件 {plugin_name} 没有方法: {method}")

        func = getattr(plugin, method)
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        return func(**kwargs)


# ── 入口 ──────────────────────────────────────────────────────

async def main():
    hub = NBclawHub()
    try:
        await hub.start()
    except KeyboardInterrupt:
        await hub.stop()


if __name__ == "__main__":
    asyncio.run(main())