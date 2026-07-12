"""
[①사유]: OMS 상태 머신(FSM)의 원자성 보장 및 무결성 검증.
[②방어 기제 #14, #10]: 비정상 상태 전이 차단 및 전이 기록 로그화.
"""

import logging
from enum import Enum, auto

class OrderStatus(Enum):
    CREATED = auto(); PENDING = auto(); SENT = auto(); PARTIAL = auto()
    FILLED = auto(); CANCELLED = auto(); REJECTED = auto()
    ACCEPTED = auto(); PENDING_CANCEL = auto(); PENDING_REPLACE = auto()
    EXPIRED = auto(); SUSPENDED = auto(); CALCULATED = auto()

class OMS_FSM:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("OMS_FSM")
        
        # [세부 전이 매트릭스] - 주문 거부/취소 단계의 엄격한 제어
        self._transitions = {
            OrderStatus.CREATED: {OrderStatus.PENDING, OrderStatus.REJECTED},
            OrderStatus.PENDING: {OrderStatus.SENT, OrderStatus.REJECTED, OrderStatus.ACCEPTED},
            OrderStatus.SENT: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.PENDING_CANCEL},
            OrderStatus.PARTIAL: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED},
            OrderStatus.PENDING_CANCEL: {OrderStatus.CANCELLED, OrderStatus.REJECTED},
        }

    async def transition(self, current: OrderStatus, next_status: OrderStatus, order_id: str) -> bool:
        """
        [①사유]: 상태 전이 유효성 검증 및 비정상 상태 시 자동 알림.
        """
        # 1. 상태 전이 가능 여부 확인
        if next_status in self._transitions.get(current, set()):
            self.logger.info(f"Transition Success [{order_id}]: {current.name} -> {next_status.name}")
            
            # [방어 기제 #10] 상태 전이 완료 이벤트 발행 (영속성 서비스가 구독)
            await self.event_bus.publish(priority=2, event_type="STATE_CHANGED", 
                                       data={"order_id": order_id, "from": current.name, "to": next_status.name})
            return True
        
        # 2. 비정상 전이 발생 시 즉시 조치
        else:
            self.logger.error(f"CRITICAL: State Mismatch [{order_id}]: {current.name} to {next_status.name}")
            
            # [방어 기제 #14] 상태 불일치 알림 발행 (위험 관리 모듈 전달)
            await self.event_bus.publish(priority=0, event_type="CRITICAL_ALERT", 
                                       data={"msg": "Invalid State Transition", "order_id": order_id})
            return False
