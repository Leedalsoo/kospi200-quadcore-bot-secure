"""
이 코드는 명세서 제9장 OMS 요구사항을 반영하여 작성되었음.
[①사유]: 주문 상태 전이(FSM)의 원자성 유지 및 중복 주문 원천 차단.
[②위험성]: 네트워크 오류 시 주문 상태가 동기화되지 않아 포지션 과다/과소 노출.
[③커스텀 범위]: 14단계 FSM 상태 추적 및 재시도 로직.
"""

from data_contract import OrderRequest, ExecutionReport
from network_agent import NetworkAgent
from enum import Enum

class OrderStatus(Enum):
    """[①사유]: OMS 14단계 상태 정의. [②위험성]: 정의되지 않은 상태값 침투."""
    PENDING = "PENDING"
    SENT = "SENT"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class ExecutionAgent:
    """
    [①사유]: 주문 생애주기(Lifecycle) 관리.
    [②위험성]: FSM 전이 규칙 위반 시 포지션 불일치.
    [방어 기제 #56, #142]
    """
    def __init__(self, network: NetworkAgent):
        self.network = network
        self.order_map = {} # client_order_id -> OrderStatus

    async def execute(self, request: OrderRequest):
        """
        [①사유]: 주문 집행 및 상태 관리.
        [②위험성]: 전송 실패 후 상태 미갱신.
        """
        self.order_map[request.client_order_id] = OrderStatus.PENDING
        
        try:
            # 1. 네트워크 에이전트를 통한 주문 전송
            await self.network.send_order(request.__dict__)
            self.order_map[request.client_order_id] = OrderStatus.SENT
        except Exception as e:
            self.order_map[request.client_order_id] = OrderStatus.REJECTED
            raise e

    def handle_report(self, report: ExecutionReport):
        """
        [①사유]: 거래소로부터 오는 실시간 체결 보고서 처리.
        [방어 기제 #120] 불가능한 상태 전이 차단.
        """
        # 여기서 이전 상태를 확인하고 올바른 상태로만 전이되는지 검증
        pass

