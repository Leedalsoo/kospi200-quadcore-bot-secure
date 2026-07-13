"""[①사유]: 네트워크 지연과 Decimal 연산이 포함된 정밀 체결 시뮬레이터."""
import asyncio
import random
import uuid
from decimal import Decimal
from data_contract import OrderRequest, ExecutionReport, OrderStatus

class MockBroker:
    def __init__(self, time_service):
        self.time_service = time_service

    async def send_order(self, request: OrderRequest) -> ExecutionReport:
        await asyncio.sleep(random.uniform(0.010, 0.030))
        slippage = Decimal(str(random.uniform(-0.0005, 0.0005)))
        fill_price = request.price * (Decimal('1') + slippage)
        
        return ExecutionReport(
            client_order_id=request.client_order_id,
            status=OrderStatus.FILLED,
            filled_qty=request.qty,
            filled_price=fill_price,
            timestamp=self.time_service.get_synced_time(),
            broker_order_id=str(uuid.uuid4())
        )
