"""
이 코드는 시스템의 모든 주문 생애주기를 관리하는 최종 OMS FSM 엔진임.
[①사유]: 네트워크 지연/유실 상황에서도 주문 상태의 원자성 보장.
[②위험성]: 상태 불일치(State Mismatch) 발생 시 포지션 정합성 붕괴.
"""

from enum import Enum, auto
import logging

class OrderStatus(Enum):
    CREATED = auto(); PENDING = auto(); SENT = auto(); PARTIAL = auto()
    FILLED = auto(); CANCELLED = auto(); REJECTED = auto()

class OMS_FSM:
    """
    [①사유]: 주문 상태 전이의 강제성 및 정합성 검증 엔진.
    [방어 기제 #56, #142] 예외적인 상태 전이 시 경보(Alert) 발행.
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("OMS_FSM")
        self._transitions = {
            OrderStatus.CREATED: {OrderStatus.PENDING, OrderStatus.REJECTED},
            OrderStatus.PENDING: {OrderStatus.SENT, OrderStatus.REJECTED},
            OrderStatus.SENT: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED},
            OrderStatus.PARTIAL: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED},
        }

    async def transition(self, current: OrderStatus, next_status: OrderStatus, order_id: str) -> bool:
        """
        [①사유]: 상태 전이 수행 및 검증.
        [②위험성]: 규칙 위반 상태 전이 시 즉시 시스템 셧다운 경보 발행.
        """
        if next_status in self._transitions.get(current, set()):
            self.logger.info(f"Order {order_id}: {current.name} -> {next_status.name}")
            return True
        else:
            self.logger.error(f"CRITICAL: Invalid State Transition for {order_id}: {current.name} -> {next_status.name}")
            # [방어 기제 #189] 비정상 전이 발견 시 즉시 시스템 경보 발행
            await self.event_bus.publish(priority=0, event_type="CRITICAL_ALERT", data={"msg": "Invalid Transition", "order_id": order_id})
            return False
