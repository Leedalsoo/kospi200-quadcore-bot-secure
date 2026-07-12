"""
[①사유]: 전체 시스템 통합 부팅 및 설정(Config) 주입.
[②방어 기제 #16, #20]: ConfigAgent 주입을 통한 런타임 제어권 확보 및 우아한 종료.
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

# [신규] 설정 및 오케스트레이션/로딩 통합
from config.config_agent import ConfigAgent
from plugins.plugin_loader import PluginLoader
from orchestration.strategy_orchestrator import StrategyOrchestrator

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("Main")

class TradingSystem:
    def __init__(self):
        # 1. [데이터 계층] 설정 로드 (무결성 검증 포함)
        self.config = ConfigAgent() 
        
        # 2. [인프라 계층] 이벤트 버스 및 저장소
        self.bus = EventBus(max_size=self.config.get("queue_size", 20000))
        self.store = EventStore(log_path="logs/system_state.jsonl")
        
        # 3. [운용 계층] 전략 지휘부 및 플러그인 로더
        # Config에서 전략별 초기 가중치를 주입받음
        self.shared_context = {
            "active_weights": self.config.get("active_weights"), 
            "global_delta": 0.0,
            "config": self.config # 모든 에이전트가 설정에 접근 가능하도록 주입
        }
        self.loader = PluginLoader(self.bus, self.shared_context)
        self.orchestrator = StrategyOrchestrator(self.shared_context)
        
        # 4. [기존 인프라] OMS 및 실행 엔진
        self.fsm = OMS_FSM(self.bus)
        self.risk = RiskAgent(HardLimitsConfig(max_margin_usage=1000000))
        self.market = MarketDataAgent(self.bus)
        self.execution = ExecutionAgent(self.bus, self.fsm)
        
        self.is_running = True

    async def initialize(self):
        """[①사유]: 시스템 부팅 및 전략 자동 로드 통합."""
        logger.info("System Initializing: Loading config, state, and plugins...")
        
        # 설정 검증 및 상태 복구
        history = await self.store.load_history()
        for event in history:
            logger.debug(f"Replaying Event: {event['event_type']}")
            
        # 전략 로딩 및 오케스트레이션 등록
        discovered_plugins = self.loader.discover_and_load()
        self.orchestrator.register_strategies(discovered_plugins)
        logger.info(f"System Ready. Strategies Loaded: {list(discovered_plugins.keys())}")

    async def run(self):
        """[①사유]: 시스템 이벤트 루프 실행."""
        await self.initialize()
        
        logger.info("Entering Event Loop. System Fully Armed.")
        while self.is_running:
            try:
                # 이벤트 버스에서 작업 소비
                event = await self.bus.consume()
                if event:
                    # 오케스트레이터가 실시간으로 시장 국면 판별 후 전략 조정
                    await self.orchestrator.monitor_regime(event)
            except Exception as e:
                logger.critical(f"System Loop Failure: {e}")

    def shutdown(self):
        logger.info("System Shutting Down gracefully.")
        self.is_running = False

if __name__ == "__main__":
    system = TradingSystem()
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, system.shutdown)
        
    try:
        loop.run_until_complete(system.run())
    finally:
        loop.close()
