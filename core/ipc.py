"""
IPC — Hub 与 Desktop Shell 之间的 HTTP/WebSocket 通信层。
Desktop Shell 通过 HTTP POST 调用 Hub 的公开方法，Hub 通过 WebSocket 推送事件。
"""

import asyncio
import logging
import json
from aiohttp import web, WSTextMessage, WSMsgType

logger = logging.getLogger("nbclaw.ipc")

DEFAULT_IPC_PORT = 18730  # 谐音"要霸气散"😄


class IPCServer:
    """
    Hub 端的 IPC 服务器：
    - HTTP POST /api/call — 调用 Hub 方法
    - WebSocket /ws — 推送 Hub 事件到 Shell
    - GET /api/status — 系统状态
    """

    def __init__(self, hub):
        self.hub = hub
        self.app = web.Application()
        self.app.router.add_post("/api/call", self._handle_call)
        self.app.app.router.add_get("/api/status", self._handle_status)
        self.app.app.router.add_get("/ws", self._handle_ws)
        self.runner = None
        self.site = None
        self.ws_clients: set[web.WebSocketResponse] = set()
        self._ws_lock = asyncio.Lock()

    async def start(self, port: int = DEFAULT_IPC_PORT):
        """启动 IPC 服务器。"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "localhost", port)
        await self.site.start()
        logger.info(f"🔌 IPC 服务器已启动 (http://localhost:{port})")

    async def stop(self):
        """停止 IPC 服务器。"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("🔌 IPC 服务器已关闭")

    async def _handle_call(self, request: web.Request) -> web.Response:
        """处理 API 调用。"""
        try:
            body = await request.json()
            method = body.get("method")
            params = body.get("params", {})

            if not hasattr(self.hub, method):
                return web.json_response({"error": f"方法不存在: {method}"}, status=404)

            func = getattr(self.hub, method)
            if asyncio.iscoroutinefunction(func):
                result = await func(**params)
            else:
                result = func(**params)

            return web.json_response({"result": result})

        except Exception as e:
            logger.error(f"IPC 调用失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_status(self, request: web.Request) -> web.Response:
        """返回系统状态。"""
        try:
            status = await self.hub.get_status()
            return web.json_response(status)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        """WebSocket 长连接 — Hub 推送事件到 Shell。"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async with self._ws_lock:
            self.ws_clients.add(ws)

        logger.info("🔌 WebSocket 客户端已连接")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    # 客户端发来的消息（暂时保留扩展用）
                    pass
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket 错误: {ws.exception()}")
        finally:
            async with self._ws_lock:
                self.ws_clients.remove(ws)
            logger.info("🔌 WebSocket 客户端已断开")

        return ws

    async def broadcast(self, event_type: str, data: dict):
        """广播事件到所有 WebSocket 客户端。"""
        if not self.ws_clients:
            return

        message = json.dumps({"type": event_type, "data": data})
        async with self._ws_lock:
            # 移除已断开的客户端
            dead = set()
            for ws in self.ws_clients:
                try:
                    await ws.send_str(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self.ws_clients.remove(ws)


# ── Shell（桌面端）调用的客户端工具 ──────────────────────────────────

import aiohttp


class IPCClient:
    """
    Desktop Shell 调用的 IPC 客户端。
    封装 HTTP POST 和 WebSocket 接收。
    """

    def __init__(self, port: int = DEFAULT_IPC_PORT):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def call(self, method: str, **params) -> dict:
        """调用 Hub 方法。"""
        async with self._session.post(
            f"{self.base_url}/api/call",
            json={"method": method, "params": params},
        ) as resp:
            return await resp.json()

    async def get_status(self) -> dict:
        """获取系统状态。"""
        async with self._session.get(f"{self.base_url}/api/status") as resp:
            return await resp.json()