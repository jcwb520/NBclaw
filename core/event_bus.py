"""
EventBus — 插件间的发布/订阅事件总线。
所有插件通信必须通过 EventBus，禁止直接引用。
"""

import logging
import asyncio
from typing import Callable, Awaitable, Any
from collections import defaultdict

logger = logging.getLogger("nbclaw.event_bus")


class EventBus:
    """
    事件总线：
    - 插件订阅事件：subscribe(event_type, callback)
    - 插件发布事件：publish(event_type, data)
    - 所有订阅者异步并行执行
    """

    def __init__(self):
        # event_type -> list of callbacks
        self._subscribers: dict[str, list[Callable[[dict], Awaitable[Any]]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[dict], Awaitable[Any]]):
        """订阅事件。"""
        self._subscribers[event_type].append(callback)
        logger.debug(f"订阅事件: {event_type} -> {callback.__name__}")

    def unsubscribe(self, event_type: str, callback: Callable[[dict], Awaitable[Any]]):
        """取消订阅。"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: str, data: dict):
        """发布事件，所有订阅者异步并行处理。"""
        callbacks = self._subscribers.get(event_type, [])
        if not callbacks:
            return

        # 并行执行所有订阅者
        tasks = [callback(data) for callback in callbacks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 记录异常（不中断流程）
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"事件 {event_type} 订阅者 #{i} 执行异常: {result}")

    # ── 常用事件类型常量 ────────────────────────────────────

    @staticmethod
    def USER_MESSAGE() -> str:
        return "user.message"

    @staticmethod
    def AGENT_RESPONSE() -> str:
        return "agent.response"

    @staticmethod
    def CHANNEL_CONNECTED() -> str:
        return "channel.connected"

    @staticmethod
    def CHANNEL_MESSAGE() -> str:
        return "channel.message"

    @staticmethod
    def SKILL_INVOKED() -> str:
        return "skill.invoked"