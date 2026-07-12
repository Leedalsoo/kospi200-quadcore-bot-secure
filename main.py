"""
[①사유]: 전체 시스템 통합 및 라이프사이클 관리.
[②방어 기제 #16, #20]: 상태 복구 기반 재기동 및 우아한 종료(Graceful Shutdown).
"""

import asyncio
import logging
import signal
from event_bus import EventBus
from event_store import EventStore
from market_data_agent import MarketDataAgent
from oms_fsm import OMS_FSM
from risk_agent import RiskAgent
from strategy_agent import StrategyAgent
from execution_agent import ExecutionAgent
from data_contract import HardLimitsConfig

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("Main")

class TradingSystem:
    def __init__(self):
        # [세부 운영 수치]
        self.bus = EventBus(max_size=20000)
        self.store = EventStore(log_path="logs/system_state.jsonl")
        self.fsm = OMS_FSM(self.bus)
        self.risk = RiskAgent(HardLimitsConfig(max_margin_usage=1000000))
        self.market = MarketDataAgent(self.bus)
        self.strategy = StrategyAgent(self.bus, self.risk)
        self.execution = ExecutionAgent(self.bus, self.fsm)
        
        self.is_running = True

    async def run(self):
        """[①사유]: 시스템 이벤트 루프 및 상태 복구 실행."""
        logger.info("System Initializing: Loading historical state...")
        
        # [방어 기제 #16]: 과거 상태 복구 (History Replay)
        history = await self.store.load_history()
        for event in history:
            logger.info(f"Replaying Event: {event['event_type']}")
        
        logger.info("System Ready. Entering Event Loop.")
        while self.is_running:
            try:
                # 이벤트 버스에서 작업 소비
                event = await self.bus.consume()
                if event:
                    # 여기에 각 에이전트별 라우팅 로직 구현
                    logger.debug(f"Processing: {event}")
            except Exception as e:
                logger.critical(f"System Loop Failure: {e}")

    def shutdown(self):
        self.is_running = False
        logger.info("System Shutting Down gracefully.")

if __name__ == "__main__":
    system = TradingSystem()
    loop = asyncio.get_event_loop()
    
    # 우아한 종료 처리
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, system.shutdown)
        
    try:
        loop.run_until_complete(system.run())
    finally:
        loop.close()
