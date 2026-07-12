"""
[①사유]: 전체 시스템 통합 및 라이프사이클 관리.
[②방어 기제 #16, #20]: 상태 복구 기반 재기동 및 우아한 종료(Graceful Shutdown).
[③추가 사항]: 전략 동적 로딩 및 오케스트레이션 엔진 통합.
"""

import asyncio
import logging
import signal
from event_bus import EventBus
from event_store import EventStore
from market_data_agent import MarketDataAgent
from oms_fsm import OMS_FSM
from risk_agent import RiskAgent
from execution_agent import ExecutionAgent
from data_contract import HardLimitsConfig

# [추가] 오케스트레이션 및 플러그인 로더 import
from plugins.plugin_loader import PluginLoader
from orchestration.strategy_orchestrator import StrategyOrchestrator

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("Main")

class TradingSystem:
    def __init__(self):
        # [기존 인프라 계층]
        self.bus = EventBus(max_size=20000)
        self.store = EventStore(log_path="logs/system_state.jsonl")
        self.fsm = OMS_FSM(self.bus)
        self.risk = RiskAgent(HardLimitsConfig(max_margin_usage=1000000))
        self.market = MarketDataAgent(self.bus)
        self.execution = ExecutionAgent(self.bus, self.fsm)
        
        # [신규 통합 계층] 공유 컨텍스트 및 지휘부 초기화
        self.shared_context = {"active_weights": {}, "global_delta": 0.0}
        self.loader = PluginLoader(self.bus, self.shared_context)
        self.orchestrator = StrategyOrchestrator(self.shared_context)
        
        self.is_running = True

    async def initialize(self):
        """[①사유]: 시스템 부팅 및 전략 자동 로드 통합."""
        logger.info("System Initializing: Loading historical state and plugins...")
        
        # [기존] 상태 복구 로직
        history = await self.store.load_history()
        for event in history:
            logger.info(f"Replaying Event: {event['event_type']}")
            
        # [신규] 전략 로딩 및 오케스트레이션 등록
        discovered_plugins = self.loader.discover_and_load()
        self.orchestrator.register_strategies(discovered_plugins)
        logger.info(f"System Ready. Strategies Loaded: {list(discovered_plugins.keys())}")

    async def run(self):
        """[①사유]: 시스템 이벤트 루프 실행."""
        await self.initialize()
        
        logger.info("System Ready. Entering Event Loop.")
        while self.is_running:
            try:
                # 이벤트 버스에서 작업 소비
                event = await self.bus.consume()
                if event:
                    # [고도화] 시장 상황(Market Regime)에 따른 오케스트레이션 실행 로직
                    # 예: 특정 조건에서 orchestrator.run_orchestration("VOLATILE") 호출
                    logger.debug(f"Processing: {event}")
            except Exception as e:
                logger.critical(f"System Loop Failure: {e}")

    def shutdown(self):
        self.is_running = False
        logger.info("System Shutting Down gracefully.")

if __name__ == "__main__":
    system = TradingSystem()
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, system.shutdown)
        
    try:
        loop.run_until_complete(system.run())
    finally:
        loop.close()
