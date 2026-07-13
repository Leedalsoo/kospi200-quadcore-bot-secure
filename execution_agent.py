"""
[①사유]: 주문 생애주기 관리 및 거래소 API 인터페이스 최적화.
[②방어 기제 #56, #142]: 14단계 상태 머신 기반 무결성 검증 및 지수 백오프 재시도.
"""

import logging
import asyncio
from data_contract import OrderRequest, ExecutionReport
from network_agent import NetworkAgent
from fsm.oms_fsm import OMS_FSM, OrderStatus

class ExecutionAgent:
    def __init__(self, network: NetworkAgent, fsm: OMS_FSM):
        self.network = network
        self.fsm = fsm
        self.logger = logging.getLogger("ExecutionAgent")
        
        # [세부 운영 수치]
        self.params = {
            "retry_delay": 0.5,   # 초기 재시도 간격(초)
            "max_retries": 3,     # 최대 재시도 횟수
            "timeout_threshold": 5  # 주문 응답 타임아웃(초)
        }

    async def execute(self, request: OrderRequest):
        """[①사유]: 재시도 로직이 포함된 안전한 주문 집행."""
        attempt = 0
        # request.order_id 대신 실제 데이터 컨트랙트의 client_order_id 사용
        order_id = request.client_order_id
        
        while attempt < self.params["max_retries"]:
            try:
                # 상태 전이: CREATED -> PENDING
                if await self.fsm.transition(OrderStatus.CREATED, OrderStatus.PENDING, order_id):
                    await self.network.send_order(request.__dict__)
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
        # [방어 기제 #120]: 불가능한 상태 전이 차단
        order_id = report.client_order_id
        current_status = await self.fsm.get_status(order_id)
        
        # report.status는 거래소에서 받은 상태값
        if await self.fsm.transition(current_status, report.status, order_id):
            self.logger.info(f"Order {order_id} transitioned to {report.status}")
        else:
            self.logger.error(f"CRITICAL: Invalid transition from {current_status} to {report.status}")
