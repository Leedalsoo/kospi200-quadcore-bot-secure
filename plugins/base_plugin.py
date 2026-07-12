"""
[①사유]: 전략 간 상관관계 처리를 위한 공유 컨텍스트 제공.
[②방어 기제 #109]: 전략 간 상충(Conflict) 방지 및 리스크 통합 관리.
"""

import logging
from data_contract import OrderRequest

class BaseStrategyPlugin:
    def __init__(self, name: str, event_bus, shared_context):
        # [방어 기제 #109]: 전략 간 공유되는 리스크/포지션 컨텍스트 주입
        self.name = name
        self.bus = event_bus
        self.context = shared_context 
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
        """[①사유]: 전략 로직 구현부. context를 사용하여 다른 전략과 협동."""
        raise NotImplementedError("전략 로직 구현 필요")
