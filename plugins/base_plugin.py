"""
[①사유]: 전략 플러그인 표준 인터페이스.
[②방어 기제 #108]: 전략별 독립적 실행(Isolation) 및 데이터 통신 규격화.
"""

import logging
from data_contract import OrderRequest

class BaseStrategyPlugin:
    def __init__(self, name: str, event_bus):
        self.name = name
        self.bus = event_bus
        self.logger = logging.getLogger(f"Plugin.{name}")

    async def execute_order(self, price: float, qty: int, side: str):
        """[①사유]: 이벤트 버스를 통한 안전한 주문 발행."""
        order = OrderRequest(
            order_id=f"{self.name}_{int(self.bus.get_time())}",
            price=price,
            qty=qty,
            side=side
        )
        await self.bus.publish(priority=0, event_type="ORDER_CREATE", data=order)
        self.logger.info(f"Strategy {self.name} issued {side} order.")

    async def on_market_tick(self, data: dict):
        """[①사유]: 추상 메서드 - 각 전략에서 구현."""
        raise NotImplementedError("전략 로직 구현 필요")

