"""
Hermes Agent 插件 — 接入 Hermes Agent 的 AI 能力。
"""

import asyncio
import logging
from core.plugin_manager import PluginInterface

logger = logging.getLogger("nbclaw.hermes_agent")


class HermesAgentPlugin(PluginInterface):
    """
    Hermes Agent 插件：
    - 订阅 user.message 事件
    - 调用 Hermes Agent 处理消息
    - 通过 event_bus 发布 agent.response 事件
    """

    name = "hermes_agent"
    version = "1.0.0"

    def __init__(self):
        self.event_bus = None
        self.config_store = None
        self.hub = None
        self._response_count = 0

    def init(self, ctx: dict):
        """接收插件上下文。"""
        self.event_bus = ctx["event_bus"]
        self.config_store = ctx["config_store"]
        self.hub = ctx["hub"]

        # 订阅 user.message 事件
        self.event_bus.subscribe("user.message", self._on_user_message)
        logger.info("✅ Hermes Agent 插件已初始化")

    def start(self):
        """启动插件。"""
        logger.info("🚀 Hermes Agent 插件已启动")

    def stop(self):
        """停止插件。"""
        self.event_bus.unsubscribe("user.message", self._on_user_message)
        logger.info("🛑 Hermes Agent 插件已停止")

    async def _on_user_message(self, data: dict) -> dict:
        """处理用户消息。"""
        text = data.get("text", "")
        logger.info(f"🤖 Hermes Agent 收到消息: {text[:50]}...")

        # 构造 prompt，发给 Hermes
        # TODO: 实际接入 Hermes Agent 的 API（根据配置决定用哪个模型）
        model = self.config_store.get("hermes.model", "deepseek")
        api_key = self.config_store.get("hermes.api_key", "")

        if not api_key:
            response_text = "⚠️ 请先在设置中配置 API Key"
        else:
            # 模拟 AI 响应（实际应调用 Hermes 的 API）
            self._response_count += 1
            response_text = f"[Hermes via {model}] 这是第 {self._response_count} 条回复。你说: {text[:30]}..."

        # 发布响应事件
        await self.event_bus.publish("agent.response", {
            "text": response_text,
            "model": model,
        })

        return {"handled": True, "response": response_text}

    def get_status(self) -> dict:
        """返回插件状态。"""
        return {
            "status": "running",
            "version": self.version,
            "response_count": self._response_count,
            "model": self.config_store.get("hermes.model", "deepseek"),
        }

    # ── 对外暴露的方法（可通过 IPC 调用）───────────────────

    async def chat(self, text: str) -> str:
        """直接聊天接口（绕过事件总线）。"""
        await self._on_user_message({"text": text})
        return "消息已发送，请等待响应"


# 注册插件类（PluginManager 会自动发现）
Plugin = HermesAgentPlugin