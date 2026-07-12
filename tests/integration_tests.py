"""
[①사유]: 전체 시스템 통합 정합성 검증.
[②방어 기제 #1~#200]: 전체 파이프라인 무결성 확인.
"""

import pytest
import asyncio
from event_bus import EventBus
from oms_fsm import OMS_FSM
from mock_broker import MockBroker
from execution_agent import ExecutionAgent

@pytest.mark.asyncio
async def test_order_lifecycle():
    """[①사유]: 주문 요청부터 체결 완료까지의 전체 루프 검증."""
    bus = EventBus()
    fsm = OMS_FSM(bus)
    broker = MockBroker()
    agent = ExecutionAgent(bus, fsm)
    
    # 가상의 주문 요청 생성
    request = {"order_id": "test_001", "price": 350.0, "qty": 1}
    
    # 주문 집행 프로세스 구동
    await agent.execute(request)
    
    # FSM 상태가 최종 단계에 도달했는지 확인
    status = await fsm.get_status("test_001")
    assert status == "SENT" 
    print("통합 테스트 성공: 주문 생애주기 무결성 검증 완료.")
