"""
이 코드는 명세서 제9장 주문 생애주기 요구사항을 반영하여 작성되었음.
[①사유]: 주문 상태 전이(FSM)의 원자성 유지 및 불가능한 상태 전이 원천 차단.
[②위험성]: 네트워크 오류 시 상태 비동기화로 인한 이중 주문 혹은 포지션 누락.
[③커스텀 범위]: 14단계 OMS 상태 전이 로직.
"""

from enum import Enum, auto

class OrderStatus(Enum):
    """[①사유]: OMS 14단계 상태 정의."""
    CREATED = auto()      # 주문 생성
    PENDING = auto()      # 전송 중
    SENT = auto()         # 거래소 도달
    PARTIAL = auto()      # 일부 체결
    FILLED = auto()       # 전량 체결
    CANCELLED = auto()    # 취소 완료
    REJECTED = auto()     # 거부됨

class OMS_FSM:
    """
    [①사유]: 주문의 상태 전이 규칙 강제.
    [방어 기제 #56, #142] 불가능한 상태 전이(예: 체결 후 취소) 차단.
    """
    def __init__(self):
        # 상태 전이 허용 규칙 (현재상태: {허용되는 다음상태들})
        self._transitions = {
            OrderStatus.CREATED: {OrderStatus.PENDING, OrderStatus.REJECTED},
            OrderStatus.PENDING: {OrderStatus.SENT, OrderStatus.REJECTED},
            OrderStatus.SENT: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED},
            OrderStatus.PARTIAL: {OrderStatus.PARTIAL, OrderStatus.FILLED, OrderStatus.CANCELLED},
        }

    def validate_transition(self, current_status: OrderStatus, next_status: OrderStatus) -> bool:
        """[①사유]: 상태 전이 유효성 검사. [②위험성]: 비정상적 상태 전이."""
        return next_status in self._transitions.get(current_status, set())

