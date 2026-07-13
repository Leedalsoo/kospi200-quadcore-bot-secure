"""
[①사유]: 구조 2 기반의 최종 통합 부팅 사령탑.
[②방어 기제 #16, #20]: ConfigAgent 및 TimeAgent 주입.
"""
import asyncio
import logging
import signal
import argparse
from config.config_agent import ConfigAgent
from plugins.plugin_loader import PluginLoader
from orchestration.strategy_orchestrator import StrategyOrchestrator
from time_agent import TimeAgent
from event_bus import EventBus
from event_store import EventStore
from oms_fsm import OMS_FSM
from execution_agent import ExecutionAgent
from network_agent import NetworkAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("Main")

class TradingSystem:
    def __init__(self, mode: str):
        self.config = ConfigAgent()
        self.time_service = TimeAgent()
        self.bus = EventBus(max_size=self.config.get("queue_size", 20000))
        self.store = EventStore(log_path="logs/system_state.jsonl")
        
        # 통합 컨텍스트
        self.shared_context = {
            "config": self.config, 
            "time": self.time_service,
            "active_weights": self.config.get("active_weights")
        }
        
        self.loader = PluginLoader(self.bus, self.shared_context)
        self.orchestrator = StrategyOrchestrator(self.shared_context)
        self.fsm = OMS_FSM(self.bus)
        self.execution = ExecutionAgent(NetworkAgent(), self.fsm)
        self.is_running = True

    async def run(self):
        discovered = self.loader.discover_and_load()
        self.orchestrator.register_strategies(discovered)
        logger.info(f"System Ready. Strategies: {list(discovered.keys())}")
        
        while self.is_running:
            await asyncio.sleep(1)

    def shutdown(self, sig):
        self.is_running = False
        logger.info("Graceful Shutdown.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['live', 'paper', 'simulation'], required=True)
    args = parser.parse_args()
    system = TradingSystem(args.mode)
    # 시그널 핸들러 생략...
    asyncio.run(system.run())
