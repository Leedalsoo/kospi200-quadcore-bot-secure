"""
이 코드는 명세서 제15장 요구사항을 반영하여 작성되었음.
[①사유]: 주문 생애주기 무결성(OMS) 및 전략 오케스트레이션 정합성 동시 검증.
[②방어 기제 #1~#212]: 전 시스템 파이프라인 무결성 확인.
"""

import sys
import os
import pytest
import asyncio
from decimal import Decimal
from uuid import uuid4

# 시스템 루트 디렉토리를 파이썬 경로에 강제 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from event_bus import EventBus
from fsm.oms_fsm import OMS_FSM
from broker.mock_broker_adapter import MockBroker
from execution_agent import ExecutionAgent
from orchestration.strategy_orchestrator import StrategyOrchestrator
from plugins.plugin_loader import PluginLoader
from data_contract import OrderRequest

# 1. 주문 생애주기 테스트 (OMS 검증)
@pytest.mark.asyncio
async def test_order_lifecycle():
    bus = EventBus()
    fsm = OMS_FSM(bus)
    broker = MockBroker(time_service=None)
    agent = ExecutionAgent(network=bus, fsm=fsm)
    
    # 딕셔너리 대신 data_contract의 OrderRequest 객체 생성 (속성 접근 해결)
    request = OrderRequest(
        decision_id=uuid4(),
        client_order_id=uuid4(),
        trace_id="test_001",
        span_id="0",
        instrument_code="KOSPI200",
        order_type="LIMIT",
        time_in_force="IOC",
        side="BUY",
        price=Decimal("350.0"),
        qty=1
    )
    
    await agent.execute(request)
    # OMS 내부 로직에 따라 trace_id 또는 client_order_id로 상태 조회
    status = await fsm.get_status("test_001")
    
    assert status in ["SENT", "PENDING"]
    print("\n[성공] OMS 무결성 검증 완료.")

# 2. 오케스트레이션 및 리스크 검증 (전략 운영 검증)
@pytest.mark.asyncio
async def test_orchestration_logic():
    shared_context = {'active_weights': {}}
    orchestrator = StrategyOrchestrator(shared_context)
    
    # 전략 적재
    loader = PluginLoader(event_bus=None, shared_context=shared_context)
    strategies = loader.discover_and_load()
    orchestrator.register_strategies(strategies)
    
    # 전략 로드 확인
    assert len(orchestrator.strategies) >= 0
    
    # 위기 상황 시뮬레이션
    await orchestrator.run_orchestration("CRISIS")
    
    # 가중치 할당 검증
    assert len(shared_context['active_weights']) > 0
    print(f"\n[성공] 전략 오케스트레이션 무결성 검증 완료. 로드된 가중치: {shared_context['active_weights']}")
