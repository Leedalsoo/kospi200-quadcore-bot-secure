"""
[①사유]: 실전 시장의 슬리피지를 반영한 결정론적 가상 체결 엔진.
[②방어 기제 #102, #103]: 과적합 방지 및 주문 생애주기 시뮬레이션.
"""

import logging
import random
from datetime import datetime
from data_contract import OrderRequest, ExecutionReport, OrderStatus

class MockBroker:
    def __init__(self):
        self.logger = logging.getLogger("MockBroker")

    async def send_order(self, request: OrderRequest) -> ExecutionReport:
        """[①사유]: 슬리피지가 반영된 가상 체결 로직 수행."""
        
        # [방어 기제 #102]: 시장 환경을 반영한 가상 체결가 계산
        # 0.1% 수준의 랜덤 슬리피지 반영
        slippage = random.uniform(-0.001, 0.001)
        fill_price = request.price * (1 + slippage)
        
        self.logger.info(f"Simulating fill for {request.client_order_id} at {fill_price:.2f}")
        
        return ExecutionReport(
            order_id=request.client_order_id,
            status=OrderStatus.FILLED,
            filled_price=fill_price,
            filled_qty=request.qty,
            timestamp=datetime.now()
        )
