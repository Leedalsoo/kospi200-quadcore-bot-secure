"""
이 코드는 명세서 제2장의 요구사항을 반영하여 작성되었음.
[①사유]: Rust-Python 간 Zero-copy 메모리 호환 및 타입 안정성 확보.
[②위험성]: 타입 불일치 시 시스템 정지 및 OMS FSM 오류 발생.
[③커스텀 범위]: 본 시스템의 7대 핵심 데이터 컨트랙트 규격.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import List
from uuid import UUID

@dataclass
class MarketTick:
    instrument_code: str
    timestamp: datetime
    last_price: float
    volume: int
    bid_prices: List[float]
    ask_prices: List[float]
    bid_qtys: List[int]
    ask_qtys: List[int]

@dataclass
class InstrumentProfile:
    instrument_code: str
    strike_price: float
    tick_size_rule: float
    expiry_date: date
    is_underlying: bool
    multiplier: int = 250000  # 기본값 필드를 마지막으로 이동

@dataclass
class OrderRequest:
    decision_id: UUID
    client_order_id: UUID
    trace_id: str
    span_id: str
    instrument_code: str
    time_in_force: str
    side: str
    price: Decimal
    qty: int
    order_type: str = "LIMIT"  # 기본값 필드를 마지막으로 이동

@dataclass
class ExecutionReport:
    client_order_id: UUID
    broker_order_id: str
    fill_id: str
    filled_qty: int
    filled_price: Decimal
    remaining_qty: int
    timestamp: datetime
    broker_raw_response: dict
    status: str = "PENDING"  # 기본값 필드를 마지막으로 이동

@dataclass
class Position:
    instrument_code: str
    role: str
    avg_price: Decimal
    qty: int
    realized_pnl: Decimal
    unrealized_pnl: Decimal

@dataclass
class DecisionLog:
    decision_id: UUID
    trace_id: str
    timestamp: datetime
    trigger_type: str
    regime_state: str
    composite_risk_score: float
    confidence_score: float
    execution_quality_score: float
    reason: str

@dataclass
class HardLimitsConfig:
    mdd_shutdown_pct: float
    max_kelly_fraction: float
    fat_finger_theo_dev_pct: float
    fat_finger_ltp_dev_pct: float
    max_order_qty_per_trade: int
    max_daily_loss_amount: Decimal

@dataclass
class OrderStatus:
    status_code: str
    description: str
