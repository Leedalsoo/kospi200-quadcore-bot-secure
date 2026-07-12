"""
[①사유]: 전략 플러그인 동적 로드 및 Base 규격 준수 검증.
[②방어 기제 #10]: 표준 규격(BaseStrategyPlugin)을 준수하지 않는 전략 실행 차단.
"""

import os
import importlib
import inspect
import logging
from .base_plugin import BaseStrategyPlugin

class PluginLoader:
    def __init__(self, event_bus, shared_context):
        self.bus = event_bus
        self.shared_context = shared_context
        self.logger = logging.getLogger("PluginLoader")

    def discover_and_load(self):
        """[①사유]: plugins 폴더 내 모든 track*.py 파일을 자동 스캔 및 로드."""
        loaded_plugins = {}
        plugin_dir = "plugins"
        
        for filename in os.listdir(plugin_dir):
            if filename.startswith("track") and filename.endswith(".py"):
                module_name = f"plugins.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseStrategyPlugin) and obj is not BaseStrategyPlugin:
                            loaded_plugins[filename[:-3]] = obj(filename[:-3], self.bus, self.shared_context)
                            self.logger.info(f"Plugin Verified & Loaded: {filename[:-3]}")
                except Exception as e:
                    self.logger.error(f"Load Error {filename}: {e}")
        return loaded_plugins
