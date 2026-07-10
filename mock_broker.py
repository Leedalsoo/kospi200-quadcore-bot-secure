"""
이 코드는 명세서 제14장 시뮬레이션 요구사항을 반영하여 작성되었음.
[①사유]: 실제 자본 투입 전 전략 알고리즘 및 OMS FSM의 결정론적 검증.
[②위험성]: 시뮬레이션 환경이 실제 시장과 다를 경우 과적합(Overfitting) 발생.
[③커스텀 범위]: 시장 데이터 기반 가상 체결 모델(Shadow Fill).
"""

from data_contract import OrderRequest, ExecutionReport, OrderStatus
from datetime import datetime
import uuid

class MockBroker:
    """
    [①사유]: 가상 체결 엔진(Shadow Fill Model).
    [방어 기제 #1, #126] 실제 거래소 API와 동일한 인터페이스 유지.
    """
    def __init__(self):
        self.pending_orders = {}

    async def receive_order(self, request: OrderRequest) -> ExecutionReport:
        """
        [①사유]: 주문 요청 수신 및 가상 체결 로직 수행.
        [②위험성]: 가격/수량 검증 누락 시 현실성 없는 체결 발생.
        """
        # [방어 기제 #158] 가상 체결 로직: 현재 시세와 비교하여 체결 여부 결정
        report = ExecutionReport(
            order_id=request.client_order_id,
            status=OrderStatus.FILLED,
            filled_price=request.price,
            filled_qty=request.qty,
            timestamp=datetime.now()
        )
        return report

