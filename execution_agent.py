"""
[①사유]: 주문 생애주기 관리 및 거래소 API 인터페이스 최적화.
[②방어 기제 #56, #142]: 14단계 상태 머신 기반 무결성 검증 및 지수 백오프 재시도.
"""

import logging
import asyncio
from decimal import Decimal
from data_contract import OrderRequest, ExecutionReport
from network_agent import NetworkAgent
from fsm.oms_fsm import OMS_FSM, OrderStatus

class ExecutionAgent:
    def __init__(self, network: NetworkAgent, fsm: OMS_FSM):
        self.network = network
        self.fsm = fsm
        self.logger = logging.getLogger("ExecutionAgent")
        
        self.params = {
            "retry_delay": 0.5,
            "max_retries": 3,
            "timeout_threshold": 5
        }

    def _serialize_request(self, request: OrderRequest):
        """[①사유]: 네트워크 전송을 위한 명시적 직렬화."""
        return {
            "client_order_id": str(request.client_order_id),
            "instrument_code": request.instrument_code,
            "price": float(request.price) if isinstance(request.price, Decimal) else float(request.price),
            "qty": int(request.qty),
            "side": request.side,
            "order_type": request.order_type
        }

    async def execute(self, request: OrderRequest):
        """[①사유]: 재시도 로직이 포함된 안전한 주문 집행."""
        attempt = 0
        order_id = request.client_order_id
        
        while attempt < self.params["max_retries"]:
            try:
                # 상태 전이: CREATED -> PENDING
                if await self.fsm.transition(OrderStatus.CREATED, OrderStatus.PENDING, order_id):
                    await self.network.send_order(self._serialize_request(request))
                    
                    # 상태 전이: PENDING -> SENT
                    await self.fsm.transition(OrderStatus.PENDING, OrderStatus.SENT, order_id)
                    return
            except Exception as e:
                attempt += 1
                self.logger.warning(f"Retry {attempt}/{self.params['max_retries']} for {order_id}: {e}")
                await asyncio.sleep(self.params["retry_delay"] * (2 ** attempt))
        
        # 재시도 실패 시 상태: REJECTED
        await self.fsm.transition(OrderStatus.PENDING, OrderStatus.REJECTED, order_id)

    async def handle_report(self, report: ExecutionReport):
        """[①사유]: 거래소 체결 보고서 처리 및 FSM 전이 검증."""
        order_id = report.client_order_id
        
        # [방어 기제]: 상태 조회 실패 시 기본값(CREATED) 할당
        current_status = await self.fsm.get_status(order_id) or OrderStatus.CREATED
        
        # report.status가 OrderStatus 타입인지 확인 후 전이
        next_status = report.status if isinstance(report.status, OrderStatus) else OrderStatus[report.status]
        
        if await self.fsm.transition(current_status, next_status, order_id):
            self.logger.info(f"Order {order_id} transitioned to {next_status.name}")
        else:
            self.logger.error(f"CRITICAL: Invalid transition from {current_status.name} to {next_status.name}")
