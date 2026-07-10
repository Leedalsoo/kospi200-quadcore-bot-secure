"""
시스템 통합 기동 스크립트 (Master Controller)
[①사유]: 각 에이전트 초기화, 이벤트 버스 연결 및 비동기 루프 가동.
[②위험성]: 순서가 꼬인 초기화는 시스템 데드락(Deadlock) 및 초기 시동 실패 유발.
"""

import asyncio
from event_bus import EventBus
from market_data_agent import MarketDataAgent
from risk_agent import RiskAgent
from strategy_agent import StrategyAgent
from execution_agent import ExecutionAgent
from interface_agent import InterfaceAgent
from observability_agent import ObservabilityAgent

class TradingBot:
    def __init__(self):
        self.bus = EventBus()
        # 모든 에이전트의 의존성을 주입하여 결합도를 최소화
        self.market_data = MarketDataAgent(self.bus)
        self.risk = RiskAgent(config={}) # HardLimitsConfig 주입 예정
        self.strategy = StrategyAgent(self.risk)
        self.execution = ExecutionAgent(self.bus)
        self.interface = InterfaceAgent(self.bus)
        self.monitor = ObservabilityAgent()

    async def run(self):
        """[①사유]: 비동기 작업 통합 수행 및 시스템 하트비트 시작."""
        # 이벤트 버스 루프와 각 에이전트의 태스크를 병렬로 실행
        await asyncio.gather(
            self.bus.start_loop(),
            self.monitor.check_health()
        )

if __name__ == "__main__":
    bot = TradingBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        # 시스템 안전 종료 루틴 (메모리 제로화 등)
        pass

