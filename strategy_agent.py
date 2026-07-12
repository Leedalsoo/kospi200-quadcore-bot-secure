"""
[①사유]: 전략 실행 엔진의 샌드박스화 및 데이터 라우팅.
[②방어 기제 #109]: 전략별 독립된 실행 공간 보장.
"""
import logging
from plugins.plugin_loader import PluginLoader

class StrategyAgent:
    def __init__(self, event_bus, shared_context):
        self.bus = event_bus
        self.logger = logging.getLogger("StrategyAgent")
        # [자동 탐색] 플러그인 로더를 통해 등록된 모든 전략을 관리
        self.loader = PluginLoader(self.bus, shared_context)
        self.strategies = self.loader.discover_and_load()
        self.logger.info(f"StrategyAgent initialized with {len(self.strategies)} strategies.")

    async def on_market_tick(self, tick):
        """[①사유]: 시장 데이터를 등록된 모든 전략 플러그인에 전파."""
        for name, strategy in self.strategies.items():
            try:
                # 전략별 고유 로직 호출
                await strategy.on_market_tick(tick)
            except Exception as e:
                self.logger.error(f"Strategy {name} runtime error: {e}")
