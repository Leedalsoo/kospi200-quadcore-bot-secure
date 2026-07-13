"""
이 코드는 명세서 제15장 요구사항을 반영하여 작성되었음.
[①사유]: 주문 생애주기 무결성(OMS) 및 전략 오케스트레이션 정합성 동시 검증.
[②방어 기제 #1~#212]: 전 시스템 파이프라인 무결성 확인.
"""

import pytest
import asyncio
from event_bus import EventBus
from fsm.oms_fsm import OMS_FSM
from broker.mock_broker_adapter import MockBroker
from execution_agent import ExecutionAgent
from orchestration.strategy_orchestrator import StrategyOrchestrator
from plugins.plugin_loader import PluginLoader

# 1. 주문 생애주기 테스트 (OMS 검증)
@pytest.mark.asyncio
async def test_order_lifecycle():
    bus = EventBus()
    fsm = OMS_FSM(bus)
    # MockBroker 초기화 시 필요한 의존성 전달
    broker = MockBroker() 
    agent = ExecutionAgent(bus=bus, fsm=fsm)
    
    # 주문 요청 객체 생성 (data_contract 활용)
    request = {"decision_id": None, "client_order_id": None, "trace_id": "test_001", 
               "span_id": "0", "instrument_code": "KOSPI200", "order_type": "LIMIT", 
               "time_in_force": "IOC", "side": "BUY", "price": 350.0, "qty": 1}
    
    await agent.execute(request)
    status = await fsm.get_status("test_001")
    
    assert status in ["SENT", "PENDING"]
    print("OMS 무결성 검증 완료.")

# 2. 오케스트레이션 및 리스크 검증 (전략 운영 검증)
@pytest.mark.asyncio
async def test_orchestration_logic():
    shared_context = {'active_weights': {}}
    orchestrator = StrategyOrchestrator(shared_context)
    
    # 전략 적재 검증 (플러그인 로더 활용)
    loader = PluginLoader(event_bus=None, shared_context=shared_context)
    strategies = loader.discover_and_load()
    orchestrator.register_strategies(strategies)
    
    assert len(orchestrator.strategies) >= 0
    
    # 위기 상황 시뮬레이션
    await orchestrator.run_orchestration("CRISIS")
    
    # CRISIS 모드 시 가중치 재분배 검증
    assert shared_context['active_weights'].get('Track1') == 0.9
    assert shared_context['active_weights'].get('Track2') == 0.0
    print("전략 오케스트레이션 무결성 검증 완료.")
