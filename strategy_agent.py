"""
[①사유]: KOSPI200 옵션 다중 경계 전략의 세부 파라미터화.
[②방어 기제 #46, #69, #102]: 스프레드 및 급변동성 필터 적용.
"""

import logging
from data_contract import MarketTick, OrderRequest

class StrategyAgent:
    def __init__(self, event_bus, risk_agent):
        self.event_bus = event_bus
        self.risk_agent = risk_agent
        self.logger = logging.getLogger("StrategyAgent")
        
        # [정교화된 전략 수치]
        self.params = {
            "max_spread": 0.05,        # 0.05pt 이하 스프레드에서만 진입
            "max_volatility": 0.01,    # 1.0% 이상의 급변동 시 관망
            "base_quantity": 1         # 1계약 단위
        }

    def _is_entry_signal(self, tick: MarketTick) -> bool:
        """
        [전략 로직]: 비용 효율성 및 시장 안정성 검증.
        """
        # 1. 호가 스프레드 필터
        spread = tick.ask_price - tick.bid_price
        if spread > self.params["max_spread"]:
            return False
            
        # 2. 시장 급변동성 필터
        if tick.volatility > self.params["max_volatility"]:
            return False
            
        return True

    def _generate_order(self, tick: MarketTick) -> OrderRequest:
        """[전략 로직]: 주문 최적화."""
        return OrderRequest(
            order_id=f"ORD_{tick.timestamp}",
            quantity=self.params["base_quantity"],
            price=tick.last_price
        )
