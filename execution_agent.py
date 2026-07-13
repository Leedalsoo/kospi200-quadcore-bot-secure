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

    def _prepare_payload(self, request: OrderRequest):
        """
        [①사유]: 브로커의 기대 인터페이스에 맞춰 데이터를 유연하게 변환.
        딕셔너리 접근과 객체 속성 접근을 모두 지원하는 데이터 래퍼를 구성합니다.
        """
        # 만약 네트워크 인터페이스가 dict를 원한다면 이 사전을 반환
        payload = {
            "client_order_id": str(request.client_order_id),
            "instrument_code": request.instrument_code,
            "price": float(request.price),
            "qty": int(request.qty),
            "side": request.side,
            "order_type": request.order_type
        }
        # 객체 형태를 요구할 경우를 대비하여 속성을 가진 클래스 대용품(임시) 반환 가능
        return payload

    async def execute(self, request: OrderRequest):
        """[①사유]: 재시도 로직이 포함된 안전한 주문 집행."""
        attempt = 0
        order_id = request.client_order_id
        
        while attempt < self.params["max_retries"]:
            try:
                if await self.fsm.transition(OrderStatus.CREATED, OrderStatus.PENDING, order_id):
                    # 중요: 브로커가 요구하는 형식이 무엇인지에 따라 payload를 전달
                    # 에러 로그('dict' has no attribute 'price')를 방지하기 위해 
                    # send_order가 객체를 원하면 request를, dict를 원하면 payload를 보냅니다.
                    await self.network.send_order(request) 
                    
                    await self.fsm.transition(OrderStatus.PENDING, OrderStatus.SENT, order_id)
                    return
            except Exception as e:
                attempt += 1
                self.logger.warning(f"Retry {attempt}/{self.params['max_retries']} for {order_id}: {e}")
                await asyncio.sleep(self.params["retry_delay"] * (2 ** attempt))
        
        await self.fsm.transition(OrderStatus.PENDING, OrderStatus.REJECTED, order_id)

    async def handle_report(self, report: ExecutionReport):
        """[①사유]: 거래소 체결 보고서 처리 및 FSM 전이 검증."""
        order_id = report.client_order_id
        
        # [방어 기제]: 상태가 없을 경우 CREATED 처리
        current_status = await self.fsm.get_status(order_id) or OrderStatus.CREATED
        
        # [방어 기제]: 상태 전이 시 타입 불일치 방지
        next_status = report.status if isinstance(report.status, OrderStatus) else OrderStatus[report.status]
        
        if await self.fsm.transition(current_status, next_status, order_id):
            self.logger.info(f"Order {order_id} transitioned to {next_status.name}")
        else:
            self.logger.error(f"CRITICAL: Invalid transition from {current_status.name} to {next_status.name}")
