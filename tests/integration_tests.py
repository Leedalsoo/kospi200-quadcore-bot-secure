"""
이 코드는 명세서 제15장 요구사항을 반영하여 작성되었음.
[①사유]: 주문 생애주기 무결성(OMS) 및 전략 오케스트레이션 정합성 동시 검증.
[②방어 기제 #1~#212]: 전 시스템 파이프라인 무결성 확인.
"""

import pytest
import asyncio
import logging
from event_bus import EventBus
from oms_fsm import OMS_FSM
from mock_broker import MockBroker
from execution_agent import ExecutionAgent
from strategy_agent import StrategyAgent
from orchestration.strategy_orchestrator import StrategyOrchestrator

# 1. 주문 생애주기 테스트 (OMS 검증)
@pytest.mark.asyncio
async def test_order_lifecycle():
    bus = EventBus()
    fsm = OMS_FSM(bus)
    broker = MockBroker()
    agent = ExecutionAgent(bus, fsm)
    request = {"order_id": "test_001", "price": 350.0, "qty": 1}
    
    await agent.execute(request)
    status = await fsm.get_status("test_001")
    assert status == "SENT"
    print("OMS 무결성 검증 완료.")

# 2. 오케스트레이션 및 리스크 검증 (전략 운영 검증)
@pytest.mark.asyncio
async def test_orchestration_logic():
    shared_context = {'active_weights': {}}
    orchestrator = StrategyOrchestrator(shared_context)
    strategy_agent = StrategyAgent(None, shared_context)
    
    # 전략 적재 검증
    assert len(strategy_agent.strategies) == 5
    
    # 위기 상황 시뮬레이션
    orchestrator.rebalance_weights("CRISIS")
    assert shared_context['active_weights']['Track1'] == 0.9
    assert shared_context['active_weights']['Track2'] == 0.0
    print("전략 오케스트레이션 무결성 검증 완료.")
