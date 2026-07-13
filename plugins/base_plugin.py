"""
[①사유]: 전략 간 상관관계 처리 및 중앙 관제 에러 핸들링을 위한 베이스 규격.
[②방어 기제 #109]: 전략 간 상충 방지 및 중앙 집중식 에러 리포팅.
[③수정 사항]: 데이터 컨트랙트 규격 준수, 시각 동기화, 및 템플릿 메서드 패턴 적용.
"""

import logging
import uuid
from decimal import Decimal
from data_contract import OrderRequest

class BaseStrategyPlugin:
    def __init__(self, name: str, event_bus, shared_context):
        # [방어 기제 #109]: 공유 컨텍스트(TimeAgent 포함) 주입
        self.name = name
        self.bus = event_bus
        self.context = shared_context 
        self.logger = logging.getLogger(f"Plugin.{name}")

    async def execute_order(self, price: float, qty: int, side: str):
        """[①사유]: 규격화된 OrderRequest를 생성하여 이벤트 버스에 발행."""
        
        # 1. 데이터 컨트랙트 요구사항에 따른 필수 필드 생성
        order = OrderRequest(
            decision_id=uuid.uuid4(),
            client_order_id=uuid.uuid4(),
            trace_id=f"TR_{self.name}_{int(self.context['time'].get_monotonic_time())}",
            span_id=str(uuid.uuid4()),
            instrument_code="KOSPI200",
            order_type="LIMIT",
            time_in_force="IOC",
            side=side,
            price=Decimal(str(price)),
            qty=qty
        )
        
        # 2. 이벤트 버스로 주문 발행
        await self.bus.publish(priority=0, event_type="ORDER_CREATE", data=order)
        self.logger.info(f"Strategy {self.name} issued {side} order: {qty} units at {price}")

    async def safe_execute(self, func, *args, **kwargs):
        """
        [①사유]: 전략 실행 중 발생하는 모든 예외를 중앙으로 규격화하여 전송.
        [방어 기제]: 에러 발생 시 시스템 셧다운을 방지하고 상태 로그를 버스로 발행.
        """
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Strategy Error in {self.name}: {e}")
            
            # [규격화된 에러 전송]: 대시보드 및 관제 시스템이 즉시 수신 가능
            await self.bus.publish(
                priority=0,
                event_type="CRITICAL_ALERT",
                data={
                    "agent": self.name,
                    "error": str(e),
                    "timestamp": self.context['time'].get_synced_time().isoformat()
                }
            )

    async def on_market_tick(self, data: dict):
        """
        [①사유]: 표준 진입점. 전략 로직은 _my_logic()에 구현하고 이 함수를 거쳐 실행하십시오.
        """
        # 하위 클래스에서 _my_logic을 구현하지 않으면 에러 발생
        await self.safe_execute(self._my_logic, data)

    async def _my_logic(self, data: dict):
        """[①사유]: 실제 전략 로직 구현부. 하위 클래스에서 반드시 오버라이드해야 함."""
        raise NotImplementedError("전략 로직(_my_logic) 구현이 필요합니다.")
