"""
ConfigStore — 统一的配置读写中心。
每个插件的配置隔离存储，Hub 核心配置统一管理。
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("nbclaw.config_store")

CONFIG_DIR = Path.home() / ".nbclaw" / "config"


class ConfigStore:
    """
    统一配置存储：
    - Hub 核心配置：config_store.get("hub.*")
    - 插件配置：config_store.get_plugin(plugin_name, "key")
    - 持久化到 JSON 文件
    """

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Any] = {}
        self._load_core_config()

    def _load_core_config(self):
        """加载核心配置文件。"""
        core_config_file = CONFIG_DIR / "hub.json"
        if core_config_file.exists():
            try:
                with open(core_config_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info("核心配置已加载")
            except Exception as e:
                logger.error(f"加载核心配置失败: {e}")

    def _save_core_config(self):
        """持久化核心配置到文件。"""
        core_config_file = CONFIG_DIR / "hub.json"
        try:
            with open(core_config_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存核心配置失败: {e}")

    # ── 核心配置读写 ────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """读取配置，支持点号路径如 'hub.model'。"""
        keys = key.split(".")
        value = self._cache
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any):
        """写入配置，支持点号路径如 'hub.model'。"""
        keys = key.split(".")
        d = self._cache
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        self._save_core_config()

    # ── 插件配置读写 ───────────────────────────────────────

    def get_plugin(self, plugin_name: str, key: str, default: Any = None) -> Any:
        """读取插件专属配置。"""
        plugin_key = f"plugins.{plugin_name}.{key}"
        return self.get(plugin_key, default)

    def set_plugin(self, plugin_name: str, key: str, value: Any):
        """写入插件专属配置。"""
        plugin_key = f"plugins.{plugin_name}.{key}"
        self.set(plugin_key, value)

    def get_all_plugins_config(self) -> dict:
        """返回所有插件配置（不含核心配置）。"""
        return self._cache.get("plugins", {})

    # ── 工具 ────────────────────────────────────────────────

    def reset(self, key: Optional[str] = None):
        """重置配置（可选指定 key）。"""
        if key is None:
            self._cache = {}
        else:
            keys = key.split(".")
            d = self._cache
            for k in keys[:-1]:
                d = d.get(k, {})
            d.pop(keys[-1], None)
        self._save_core_config()