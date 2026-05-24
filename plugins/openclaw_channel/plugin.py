"""
OpenClaw Channel 插件 — 接入 OpenClaw 的通道能力（微信/QQ/Telegram/Discord等）。
OpenClaw Gateway 通过标准 MCP 协议通信，这里作为 NBclaw 的通道适配层。
"""

import asyncio
import logging
from core.plugin_manager import PluginInterface

logger = logging.getLogger("nbclaw.openclaw_channel")


class OpenClawChannelPlugin(PluginInterface):
    """
    OpenClaw 通道插件：
    - 管理多个平台的连接（微信/QQ/Telegram/Discord 等）
    - 将各平台消息转发给 Hermes Agent 处理
    - 将响应发回对应平台
    - 未来接入 OpenClaw MCP Gateway
    """

    name = "openclaw_channel"
    version = "0.1.0"

    def __init__(self):
        self.event_bus = None
        self.config_store = None
        self._channels: dict[str, bool] = {}  # channel_name -> connected

    def init(self, ctx: dict):
        self.event_bus = ctx["event_bus"]
        self.config_store = ctx["config_store"]

        # 订阅来自各平台的消息
        self.event_bus.subscribe("channel.message", self._on_channel_message)

        # 订阅 agent.response，转发到对应平台
        self.event_bus.subscribe("agent.response", self._on_agent_response)

        logger.info("✅ OpenClaw Channel 插件已初始化")

    def start(self):
        """启动插件，连接所有已配置的平台。"""
        channels = self.config_store.get_plugin(self.name, "channels", [])
        logger.info(f"🚀 启动 OpenClaw Channel 插件，配置了 {len(channels)} 个平台")
        # TODO: 实际连接各平台（WebSocket/MQTT 等）
        # 目前是占位，后续按需实现

    def stop(self):
        """停止插件，断开所有平台连接。"""
        self._channels.clear()
        self.event_bus.unsubscribe("channel.message", self._on_channel_message)
        self.event_bus.unsubscribe("agent.response", self._on_agent_response)
        logger.info("🛑 OpenClaw Channel 插件已停止")

    async def _on_channel_message(self, data: dict) -> dict:
        """处理来自各平台的消息，转发给 Hermes。"""
        platform = data.get("platform", "unknown")
        content = data.get("content", "")
        user_id = data.get("user_id", "")

        logger.info(f"📨 收到 [{platform}] 用户 {user_id} 的消息: {content[:50]}...")

        # 转发给 Hermes Agent 处理
        await self.event_bus.publish("user.message", {
            "text": content,
            "platform": platform,
            "user_id": user_id,
        })

        return {"handled": True}

    async def _on_agent_response(self, data: dict) -> dict:
        """处理 AI 响应，发回对应平台。"""
        text = data.get("text", "")
        platform = data.get("platform", "unknown")

        logger.info(f"📤 响应 [{platform}]: {text[:50]}...")

        # TODO: 根据 platform 发送到对应平台
        # 需要记录每个 user_id 对应的 platform

        return {"handled": True}

    def get_status(self) -> dict:
        """返回插件状态。"""
        return {
            "status": "running",
            "version": self.version,
            "channels": list(self._channels.keys()),
        }

    # ── 平台管理 ─────────────────────────────────────────

    async def connect_channel(self, platform: str, config: dict):
        """连接指定平台。"""
        logger.info(f"连接平台: {platform}")
        self._channels[platform] = True
        # TODO: 实际调用 OpenClaw Gateway 的 MCP 接口

    async def disconnect_channel(self, platform: str):
        """断开指定平台。"""
        if platform in self._channels:
            del self._channels[platform]
            logger.info(f"已断开平台: {platform}")


Plugin = OpenClawChannelPlugin