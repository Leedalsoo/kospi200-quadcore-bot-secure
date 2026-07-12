"""
[①사유]: 시장 국면(Regime)에 따른 전략 동적 배분 및 앙상블 실행.
[②방어 기제 #201]: 전략 간 상충 방지 및 자본 배분 최적화.
"""

import logging

class StrategyOrchestrator:
    def __init__(self, shared_context):
        self.strategies = {}
        self.context = shared_context
        self.logger = logging.getLogger("Orchestrator")

    def register_strategies(self, loaded_plugins):
        """[①사유]: 로드된 모든 전략을 자동으로 등록."""
        self.strategies = loaded_plugins
        for name in loaded_plugins.keys():
            if name not in self.context['active_weights']:
                self.context['active_weights'][name] = 0.0
        self.logger.info(f"Orchestrator registered {len(loaded_plugins)} strategies.")

    async def run_orchestration(self, market_regime: str):
        """[①사유]: 시장 상황에 따른 가중치 동적 할당."""
        if market_regime == "VOLATILE":
            self.context['active_weights'] = {'track4_gamma': 0.7, 'track1_defense': 0.3}
        else:
            self.context['active_weights'] = {'track3_arbitrage': 0.8, 'track2_trap': 0.2}

