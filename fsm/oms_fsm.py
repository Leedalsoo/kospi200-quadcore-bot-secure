"""
이 코드는 시스템의 모든 주문 생애주기를 관리하는 최종 OMS FSM 엔진임.
"""
from enum import Enum, auto
import logging

class OrderStatus(Enum):
    CREATED = auto(); PENDING = auto(); SENT = auto(); PARTIAL = auto()
    FILLED = auto(); CANCELLED = auto(); REJECTED = auto()
    ACCEPTED = auto(); PENDING_CANCEL = auto(); PENDING_REPLACE = auto()
    EXPIRED = auto(); SUSPENDED = auto(); CALCULATED = auto()

class OMS_FSM:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("OMS_FSM")
        self._transitions = {
            OrderStatus.CREATED: {OrderStatus.PENDING, OrderStatus.REJECTED},
            OrderStatus.PENDING: {OrderStatus.SENT, OrderStatus.REJECTED, OrderStatus.ACCEPTED},
            OrderStatus.SENT: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.PENDING_CANCEL},
            OrderStatus.PARTIAL: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED},
            OrderStatus.PENDING_CANCEL: {OrderStatus.CANCELLED, OrderStatus.REJECTED},
        }

    async def transition(self, current, next_status, order_id):
        # 4개의 공백으로 들여쓰기를 통일했습니다.
        if next_status in self._transitions.get(current, set()):
            self.logger.info(f"Order {order_id}: {current.name} -> {next_status.name}")
            return True
        else:
            self.logger.error(f"CRITICAL: Invalid State Transition: {order_id}")
            await self.event_bus.publish(priority=0, event_type="CRITICAL_ALERT", data={"msg": "Invalid Transition"})
            return False
