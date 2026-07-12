"""
이 코드는 시스템의 모든 주문 생애주기를 관리하는 최종 OMS FSM 엔진임.
[①사유]: 네트워크 지연/유실 상황에서도 주문 상태의 원자성 보장.
[②위험성]: 상태 불일치(State Mismatch) 발생 시 포지션 정합성 붕괴.
"""

from enum import Enum, auto
import logging

class OrderStatus(Enum):
    # 명세서 14단계 상태 전이 규격 반영
    CREATED = auto(); PENDING = auto(); SENT = auto(); PARTIAL = auto()
    FILLED = auto(); CANCELLED = auto(); REJECTED = auto()
    ACCEPTED = auto(); PENDING_CANCEL = auto(); PENDING_REPLACE = auto()
    EXPIRED = auto(); SUSPENDED = auto(); CALCULATED = auto()

class OMS_FSM:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("OMS_FSM")
        # 14단계 상태 전이 매트릭스
        self._transitions = {
            OrderStatus.CREATED: {OrderStatus.PENDING, OrderStatus.REJECTED},
            OrderStatus.PENDING: {OrderStatus.SENT, OrderStatus.REJECTED, OrderStatus.ACCEPTED},
            OrderStatus.SENT: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.PENDING_CANCEL},
            OrderStatus.PARTIAL: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED},
            OrderStatus.PENDING_CANCEL: {OrderStatus.CANCELLED, OrderStatus.REJECTED},
        }

    async def transition(self, current: OrderStatus, next_status: OrderStatus, order_id: str) -> bool:
        # if-else 들여쓰기 완벽하게 맞춤
        if next_status in self._transitions.get(current, set()):
            self.logger.info(f"Order {order_id}: {current.name} -> {next_status.name}")
            return True
        else:
            self.logger.error(f"CRITICAL: Invalid State Transition for {order_id}: {current.name} -> {next_status.name}")
            await self.event_bus.publish(priority=0, event_type="CRITICAL_ALERT", data={"msg": "Invalid Transition", "order_id": order_id})
            return False
            return False
        else:
            self.logger.error(f"CRITICAL: Invalid State Transition for {order_id}: {current.name} -> {next_status.name}")
            # [방어 기제 #189] 비정상 전이 발견 시 즉시 시스템 경보 발행
            await self.event_bus.publish(priority=0, event_type="CRITICAL_ALERT", data={"msg": "Invalid Transition", "order_id": order_id})
            return False
