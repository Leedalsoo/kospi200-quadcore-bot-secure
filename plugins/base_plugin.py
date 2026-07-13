"""
[①사유]: 전략 간 상관관계 처리를 위한 공유 컨텍스트 제공.
[②방어 기제 #109]: 전략 간 상충(Conflict) 방지 및 리스크 통합 관리.
[③수정 사항]: 데이터 컨트랙트 규격 준수 및 TimeAgent 시각 동기화 적용.
"""

import logging
import uuid
from decimal import Decimal
from data_contract import OrderRequest

class BaseStrategyPlugin:
    def __init__(self, name: str, event_bus, shared_context):
        # [방어 기제 #109]: 공유 컨텍스트 주입 (TimeAgent 포함)
        self.name = name
        self.bus = event_bus
        self.context = shared_context 
        self.logger = logging.getLogger(f"Plugin.{name}")

    async def execute_order(self, price: float, qty: int, side: str):
        """
        [①사유]: 규격화된 OrderRequest를 생성하여 이벤트 버스에 발행.
        [②방어 기제]: 데이터 컨트랙트 불일치로 인한 런타임 에러 방지.
        """
        
        # 1. 데이터 컨트랙트 요구사항에 따른 필수 필드 생성
        order = OrderRequest(
            decision_id=uuid.uuid4(),
            client_order_id=uuid.uuid4(),
            trace_id=f"TR_{self.name}_{int(self.context['time'].get_monotonic_time())}",
            span_id=str(uuid.uuid4()),
            instrument_code="KOSPI200",  # 예시 종목코드
            order_type="LIMIT",
            time_in_force="IOC",
            side=side,
            price=Decimal(str(price)),    # Decimal 변환 필수
            qty=qty
        )
        
        # 2. 이벤트 버스로 주문 발행
        await self.bus.publish(priority=0, event_type="ORDER_CREATE", data=order)
        self.logger.info(f"Strategy {self.name} issued {side} order: {qty} units at {price}")

    async def on_market_tick(self, data: dict):
        """[①사유]: 전략 로직 구현부. context를 사용하여 다른 전략과 협동."""
        raise NotImplementedError("전략 로직 구현 필요")
